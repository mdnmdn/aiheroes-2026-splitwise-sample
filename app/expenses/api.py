"""JSON API of the expenses. Money is an integer in minor units."""

import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.responses import Response

from app.core.db import get_conn
from app.core.errors import ValidationFailed
from app.core.ids import Id
from app.core.money import to_input
from app.core.session import User, current_user_api
from app.expenses import service
from app.expenses.schemas import Expense, ExpenseForm, ExpenseIn, ExpenseOut, ShareOut
from app.groups import service as groups_service

router = APIRouter(prefix="/api/v1", tags=["expenses"])

CurrentUser = Annotated[User, Depends(current_user_api)]
Conn = Annotated[sqlite3.Connection, Depends(get_conn)]


def expense_out(expense: Expense, currency: str) -> ExpenseOut:
    return ExpenseOut(
        id=expense.id,
        group_id=expense.group_id,
        description=expense.description,
        amount=expense.amount,
        currency=currency,
        expense_date=expense.expense_date,
        payer_id=expense.payer_id,
        shares=[ShareOut(member_id=m, amount=s) for m, s in expense.shares.items()],
    )


def _currency(conn: sqlite3.Connection, user: User, group_id: int) -> str:
    return groups_service.require_member(conn, user, group_id)[0].currency


def _form(currency: str, body: ExpenseIn) -> ExpenseForm:
    """The text form that the service validates. The same rules as the HTML form apply."""
    return ExpenseForm(
        description=body.description,
        amount=to_input(body.amount, currency),
        expense_date=body.expense_date,
        payer_id=str(body.payer_id),
        p=[str(i) for i in body.participant_ids],
    )


@contextmanager
def _api_fields() -> Iterator[None]:
    """The service names the field "participants". The body field is participant_ids."""
    try:
        yield
    except ValidationFailed as err:
        fields = {"participant_ids" if k == "participants" else k: v for k, v in err.fields.items()}
        raise ValidationFailed(err.message, fields=fields) from err


@router.get("/groups/{group_id}/expenses")
def list_expenses(group_id: Id, user: CurrentUser, conn: Conn) -> list[ExpenseOut]:
    group, expenses = service.list_expenses(conn, user, group_id)
    return [expense_out(e, group.currency) for e in expenses]


@router.post("/groups/{group_id}/expenses", status_code=201)
def create_expense(group_id: Id, body: ExpenseIn, user: CurrentUser, conn: Conn) -> ExpenseOut:
    currency = _currency(conn, user, group_id)
    with _api_fields():
        expense_id = service.add_expense(conn, user, group_id, _form(currency, body))
    return expense_out(service.get(conn, group_id, expense_id), currency)


@router.put("/groups/{group_id}/expenses/{expense_id}")
def update_expense(
    group_id: Id, expense_id: Id, body: ExpenseIn, user: CurrentUser, conn: Conn
) -> ExpenseOut:
    currency = _currency(conn, user, group_id)
    with _api_fields():
        service.update_expense(conn, user, group_id, expense_id, _form(currency, body))
    return expense_out(service.get(conn, group_id, expense_id), currency)


@router.delete("/groups/{group_id}/expenses/{expense_id}", status_code=204)
def delete_expense(group_id: Id, expense_id: Id, user: CurrentUser, conn: Conn) -> Response:
    service.delete_expense(conn, user, group_id, expense_id)
    return Response(status_code=204)
