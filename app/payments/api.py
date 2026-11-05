"""JSON API of the payments. Money is an integer in minor units."""

import sqlite3
from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.responses import Response

from app.core.db import get_conn
from app.core.ids import Id
from app.core.money import to_input
from app.core.session import User, current_user_api
from app.groups import service as groups_service
from app.payments import service
from app.payments.schemas import Payment, PaymentForm, PaymentIn, PaymentOut

router = APIRouter(prefix="/api/v1", tags=["payments"])

CurrentUser = Annotated[User, Depends(current_user_api)]
Conn = Annotated[sqlite3.Connection, Depends(get_conn)]


def payment_out(payment: Payment, currency: str) -> PaymentOut:
    return PaymentOut(
        id=payment.id,
        group_id=payment.group_id,
        sender_id=payment.sender_id,
        receiver_id=payment.receiver_id,
        amount=payment.amount,
        currency=currency,
        payment_date=payment.payment_date,
        note=payment.note,
    )


def _currency(conn: sqlite3.Connection, user: User, group_id: int) -> str:
    return groups_service.require_member(conn, user, group_id)[0].currency


def _form(currency: str, body: PaymentIn) -> PaymentForm:
    """The text form that the service validates. The same rules as the HTML form apply."""
    return PaymentForm(
        sender_id=str(body.sender_id),
        receiver_id=str(body.receiver_id),
        amount=to_input(body.amount, currency),
        payment_date=body.payment_date,
        note=body.note,
    )


@router.get("/groups/{group_id}/payments")
def list_payments(group_id: Id, user: CurrentUser, conn: Conn) -> list[PaymentOut]:
    group, payments = service.list_payments(conn, user, group_id)
    return [payment_out(p, group.currency) for p in payments]


@router.post("/groups/{group_id}/payments", status_code=201)
def create_payment(group_id: Id, body: PaymentIn, user: CurrentUser, conn: Conn) -> PaymentOut:
    currency = _currency(conn, user, group_id)
    payment_id = service.record_payment(conn, user, group_id, _form(currency, body))
    return payment_out(service.get(conn, group_id, payment_id), currency)


@router.put("/groups/{group_id}/payments/{payment_id}")
def update_payment(
    group_id: Id, payment_id: Id, body: PaymentIn, user: CurrentUser, conn: Conn
) -> PaymentOut:
    currency = _currency(conn, user, group_id)
    service.update_payment(conn, user, group_id, payment_id, _form(currency, body))
    return payment_out(service.get(conn, group_id, payment_id), currency)


@router.delete("/groups/{group_id}/payments/{payment_id}", status_code=204)
def delete_payment(group_id: Id, payment_id: Id, user: CurrentUser, conn: Conn) -> Response:
    service.delete_payment(conn, user, group_id, payment_id)
    return Response(status_code=204)
