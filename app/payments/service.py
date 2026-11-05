"""Rules of the payments: validation, record, edit and delete.

record_payment serves the form, the JSON API and "Mark as paid" of the balances feature.
"""

import sqlite3

import structlog

from app.core import clock
from app.core.clock import now_iso
from app.core.db import transaction
from app.core.errors import NotFound, ValidationFailed
from app.core.ids import parse_id
from app.core.limits import NOTE_MAX
from app.core.money import format_money, to_input
from app.core.session import User
from app.expenses.service import validate_amount, validate_date
from app.groups import service as groups_service
from app.groups.schemas import Group
from app.members import repo as members_repo
from app.members.schemas import Member
from app.payments import repo
from app.payments.schemas import Payment, PaymentData, PaymentForm, PaymentView

log = structlog.get_logger()


class PaymentNotFound(NotFound):
    """The item is gone. The route answers 404 and the list reloads."""


NOT_FOUND = "That payment does not exist."


def _member_id(text: str, member_ids: set[int]) -> int:
    value = parse_id(text)
    return value if value in member_ids else 0


def validate(group: Group, members: list[Member], form: PaymentForm) -> PaymentData:
    """ValidationFailed with all field errors, or the values to store."""
    errors: dict[str, str] = {}
    member_ids = {m.id for m in members}
    sender_id = _member_id(form.sender_id, member_ids)
    receiver_id = _member_id(form.receiver_id, member_ids)
    if not sender_id:
        errors["sender_id"] = "Choose the sender."
    if not receiver_id:
        errors["receiver_id"] = "Choose the receiver."
    elif sender_id == receiver_id:
        errors["receiver_id"] = "Sender and receiver must be different members."
    amount = validate_amount(form.amount, group.currency, errors)
    payment_date = validate_date(form.payment_date, "payment_date", "payment date", errors)
    note = form.note.strip()
    if len(note) > NOTE_MAX:
        errors["note"] = f"Use at most {NOTE_MAX} characters."
    if errors:
        raise ValidationFailed("Fix the fields.", fields=errors)
    return PaymentData(sender_id, receiver_id, amount, payment_date, note)


def has_other_member(conn: sqlite3.Connection, group_id: int) -> bool:
    """True when the group has two members or more, so a payment can have two different parties."""
    return len(members_repo.list_members(conn, group_id)) >= 2


def get(conn: sqlite3.Connection, group_id: int, payment_id: int) -> Payment:
    payment = repo.find(conn, group_id, payment_id)
    if payment is None:
        raise PaymentNotFound(NOT_FOUND)
    return payment


def form_view(
    conn: sqlite3.Connection,
    user: User,
    group_id: int,
    form: PaymentForm | None = None,
    errors: dict[str, str] | None = None,
    payment_id: int | None = None,
) -> PaymentView:
    """Context of the dialog. Without a form: the add defaults or the stored values."""
    group, me = groups_service.require_member(conn, user, group_id)
    members = members_repo.list_members(conn, group_id)
    confirm_body = ""
    payment = get(conn, group_id, payment_id) if payment_id is not None else None
    if form is None and payment is not None:
        form = PaymentForm(
            sender_id=str(payment.sender_id),
            receiver_id=str(payment.receiver_id),
            amount=to_input(payment.amount, group.currency),
            payment_date=payment.payment_date,
            note=payment.note,
        )
    elif form is None:
        receiver = next((m for m in members if m.id != me.id), None)
        form = PaymentForm(
            sender_id=str(me.id),
            receiver_id=str(receiver.id if receiver else ""),
            payment_date=clock.today_iso(),
        )
    if payment is not None:
        names = {m.id: m.name for m in members}
        money = format_money(payment.amount, group.currency)
        confirm_body = (
            f"{names[payment.sender_id]} → {names[payment.receiver_id]}, {money}."
            " The app recalculates the balances."
        )
    return PaymentView(
        group, members, form, errors or {}, payment_id, clock.today_iso(), confirm_body
    )


def record_payment(conn: sqlite3.Connection, user: User, group_id: int, form: PaymentForm) -> int:
    group, _ = groups_service.require_member(conn, user, group_id)
    with transaction(conn):
        data = validate(group, members_repo.list_members(conn, group_id), form)
        values = (data.sender_id, data.receiver_id, data.amount, data.payment_date, data.note)
        payment_id = repo.insert(conn, group_id, values, now_iso())
    log.info(
        "payment.recorded",
        group_id=group_id,
        payment_id=payment_id,
        user_id=user.id,
        amount=data.amount,
        currency=group.currency,
    )
    return payment_id


def update_payment(
    conn: sqlite3.Connection, user: User, group_id: int, payment_id: int, form: PaymentForm
) -> int:
    group, _ = groups_service.require_member(conn, user, group_id)
    get(conn, group_id, payment_id)
    with transaction(conn):
        get(conn, group_id, payment_id)
        data = validate(group, members_repo.list_members(conn, group_id), form)
        values = (data.sender_id, data.receiver_id, data.amount, data.payment_date, data.note)
        repo.update(conn, payment_id, values, now_iso())
    log.info("payment.updated", group_id=group_id, payment_id=payment_id, user_id=user.id)
    return payment_id


def delete_payment(conn: sqlite3.Connection, user: User, group_id: int, payment_id: int) -> None:
    groups_service.require_member(conn, user, group_id)
    with transaction(conn):
        get(conn, group_id, payment_id)
        repo.delete(conn, payment_id)
    log.info("payment.deleted", group_id=group_id, payment_id=payment_id, user_id=user.id)


def list_payments(
    conn: sqlite3.Connection, user: User, group_id: int
) -> tuple[Group, list[Payment]]:
    group, _ = groups_service.require_member(conn, user, group_id)
    return group, repo.list_for_group(conn, group_id)
