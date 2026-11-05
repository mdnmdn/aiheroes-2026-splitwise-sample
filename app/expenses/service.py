"""Rules of the expenses: validation, equal split, preview, add, edit and delete.

The date and amount helpers here also serve the payments feature.
"""

import re
import sqlite3
from datetime import date

import structlog

from app.core import clock
from app.core.clock import now_iso
from app.core.db import transaction
from app.core.errors import AppError, NotFound, ValidationFailed
from app.core.ids import parse_id
from app.core.limits import DESCRIPTION_MAX
from app.core.money import format_money, parse_amount, split_equal, to_input
from app.core.session import User
from app.expenses import repo
from app.expenses.schemas import Expense, ExpenseData, ExpenseForm, ExpenseView, Preview
from app.groups import service as groups_service
from app.groups.schemas import Group
from app.members import repo as members_repo
from app.members.schemas import Member

log = structlog.get_logger()


class ExpenseNotFound(NotFound):
    """The item is gone. The route answers 404 and the list reloads."""


NOT_FOUND = "That expense does not exist."
_ISO_DATE = re.compile(r"^[0-9]{4}-[0-9]{2}-[0-9]{2}$")


def validate_amount(text: str, currency: str, errors: dict[str, str]) -> int:
    """Minor units, or 0 with the error in errors["amount"]."""
    try:
        return parse_amount(text, currency)
    except ValueError as err:
        errors["amount"] = str(err)
        return 0


def validate_date(text: str, key: str, label: str, errors: dict[str, str]) -> str:
    """The ISO date, or "" with the error in errors[key]. label: "expense date"."""
    value = text.strip()
    try:
        if not _ISO_DATE.match(value):
            raise ValueError
        date.fromisoformat(value)
    except ValueError:
        errors[key] = f"Pick an {label}." if label.startswith("expense") else f"Pick a {label}."
        return ""
    if value > clock.today_iso():
        errors[key] = f"The {label} cannot be in the future."
        return ""
    return value


def _id_set(values: list[str]) -> set[int]:
    return {i for v in values if (i := parse_id(v))}


def build_preview(
    members: list[Member], amount_text: str, selected: list[str], currency: str
) -> Preview:
    """Shares of the selected members. An invalid amount gives no shares."""
    chosen = _id_set(selected)
    ids = [m.id for m in members if m.id in chosen]  # join order, not selection order
    n = len(ids)
    all_selected = n == len(members) and n > 0
    if n == 0:
        return Preview({}, "Choose who shares this expense.", False)
    noun = "participant" if n == 1 else "participants"
    try:
        amount = parse_amount(amount_text, currency)
    except ValueError:
        return Preview({}, f"{n} {noun}", all_selected)
    shares = dict(zip(ids, split_equal(amount, n), strict=True))
    rest = amount % n
    if rest == 0:
        hint = f"{n} {noun} · {format_money(amount // n, currency)} each"
    else:
        hint = f"{n} {noun} · the first {rest} in join order get one minor unit more"
    return Preview(shares, hint, all_selected)


def validate(group: Group, members: list[Member], form: ExpenseForm) -> ExpenseData:
    """ValidationFailed with all field errors, or the values to store."""
    errors: dict[str, str] = {}
    description = form.description.strip()
    if not description:
        errors["description"] = "Add a short description."
    elif len(description) > DESCRIPTION_MAX:
        errors["description"] = f"Use at most {DESCRIPTION_MAX} characters."
    amount = validate_amount(form.amount, group.currency, errors)
    expense_date = validate_date(form.expense_date, "expense_date", "expense date", errors)
    member_ids = {m.id for m in members}
    payer_id = parse_id(form.payer_id)
    if payer_id not in member_ids:
        errors["payer_id"] = "Choose who paid."
    chosen = _id_set(form.p)
    if not form.p:
        errors["participants"] = "Pick at least one participant."
    elif len(chosen) != len({v for v in form.p}) or not chosen <= member_ids:
        errors["participants"] = "Choose members of this group only."
    if errors:
        raise ValidationFailed("Fix the fields.", fields=errors)
    ids = [m.id for m in members if m.id in chosen]
    return ExpenseData(description, amount, expense_date, payer_id, ids)


def _view(
    group: Group,
    members: list[Member],
    values: ExpenseForm,
    errors: dict[str, str],
    expense_id: int | None = None,
    confirm_body: str = "",
) -> ExpenseView:
    preview = build_preview(members, values.amount, values.p, group.currency)
    return ExpenseView(
        group, members, values, errors, preview, expense_id, clock.today_iso(), confirm_body
    )


def form_view(
    conn: sqlite3.Connection,
    user: User,
    group_id: int,
    form: ExpenseForm | None = None,
    errors: dict[str, str] | None = None,
    expense_id: int | None = None,
) -> ExpenseView:
    """Context of the dialog. Without a form: the add defaults or the stored values."""
    group, me = groups_service.require_member(conn, user, group_id)
    members = members_repo.list_members(conn, group_id)
    confirm_body = ""
    if form is None and expense_id is not None:
        expense = get(conn, group_id, expense_id)
        form = ExpenseForm(
            description=expense.description,
            amount=to_input(expense.amount, group.currency),
            expense_date=expense.expense_date,
            payer_id=str(expense.payer_id),
            p=[str(i) for i in expense.shares],
        )
        money = format_money(expense.amount, group.currency)
        confirm_body = (
            f"The app deletes {expense.description} ({money}) and recalculates the balances."
        )
    elif form is None:
        form = ExpenseForm(
            expense_date=clock.today_iso(),
            payer_id=str(me.id),
            p=[str(m.id) for m in members],
        )
    elif expense_id is not None:
        current = repo.find(conn, group_id, expense_id)
        if current is None:
            raise ExpenseNotFound(NOT_FOUND)
    return _view(group, members, form, errors or {}, expense_id, confirm_body)


def preview(
    conn: sqlite3.Connection, user: User, group_id: int, amount: str, selected: list[str]
) -> tuple[Group, list[Member], Preview]:
    group, _ = groups_service.require_member(conn, user, group_id)
    members = members_repo.list_members(conn, group_id)
    return group, members, build_preview(members, amount, selected, group.currency)


def get(conn: sqlite3.Connection, group_id: int, expense_id: int) -> Expense:
    expense = repo.find(conn, group_id, expense_id)
    if expense is None:
        raise ExpenseNotFound(NOT_FOUND)
    return expense


def _save(
    conn: sqlite3.Connection, group: Group, form: ExpenseForm, expense_id: int | None
) -> tuple[int, ExpenseData]:
    """One transaction: validate, then the expense and its shares.

    The shares must add up to the amount. The members are read inside the transaction.
    """
    group_id = group.id
    with transaction(conn):
        if expense_id is not None and repo.find(conn, group_id, expense_id) is None:
            raise ExpenseNotFound(NOT_FOUND)
        data = validate(group, members_repo.list_members(conn, group_id), form)
        shares = dict(
            zip(
                data.participant_ids,
                split_equal(data.amount, len(data.participant_ids)),
                strict=True,
            )
        )
        now = now_iso()
        if expense_id is None:
            expense_id = repo.insert(
                conn, group_id, data.description, data.amount, data.expense_date, data.payer_id, now
            )
        else:
            repo.update(
                conn,
                expense_id,
                data.description,
                data.amount,
                data.expense_date,
                data.payer_id,
                now,
            )
        repo.replace_shares(conn, expense_id, shares)
        if repo.share_sum(conn, expense_id) != data.amount:
            raise AppError("The shares do not add up to the amount.")
    return expense_id, data


def add_expense(conn: sqlite3.Connection, user: User, group_id: int, form: ExpenseForm) -> int:
    group, _ = groups_service.require_member(conn, user, group_id)
    expense_id, data = _save(conn, group, form, None)
    log.info(
        "expense.added",
        group_id=group_id,
        expense_id=expense_id,
        user_id=user.id,
        amount=data.amount,
        currency=group.currency,
    )
    return expense_id


def update_expense(
    conn: sqlite3.Connection, user: User, group_id: int, expense_id: int, form: ExpenseForm
) -> int:
    group, _ = groups_service.require_member(conn, user, group_id)
    get(conn, group_id, expense_id)
    _save(conn, group, form, expense_id)
    log.info("expense.updated", group_id=group_id, expense_id=expense_id, user_id=user.id)
    return expense_id


def delete_expense(conn: sqlite3.Connection, user: User, group_id: int, expense_id: int) -> None:
    groups_service.require_member(conn, user, group_id)
    with transaction(conn):
        get(conn, group_id, expense_id)
        repo.delete(conn, expense_id)
    log.info("expense.deleted", group_id=group_id, expense_id=expense_id, user_id=user.id)


def list_expenses(
    conn: sqlite3.Connection, user: User, group_id: int
) -> tuple[Group, list[Expense]]:
    group, _ = groups_service.require_member(conn, user, group_id)
    return group, repo.list_for_group(conn, group_id)
