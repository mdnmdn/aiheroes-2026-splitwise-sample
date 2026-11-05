"""HTML routes of the payments: dialogs, record, edit and delete."""

import sqlite3
from typing import Annotated

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import Response

from app.core.db import get_conn
from app.core.errors import ValidationFailed
from app.core.htmx import fragment_only, htmx_response, mutation_response, toast
from app.core.ids import Id
from app.core.session import User, current_user_html
from app.core.templating import templates
from app.groups import service as groups_service
from app.payments import service
from app.payments.schemas import PaymentForm

router = APIRouter()

LEDGER_CHANGED = {"ledger-changed": {}}
NEED_MEMBER = "Add one more member first."


def _fragment(request: Request, name: str, view: object, status: int = 200) -> Response:
    context = {"view": view}
    return templates.TemplateResponse(request, name, context, status_code=status)


def _gone(err: service.PaymentNotFound) -> Response:
    """The payment is gone. The list reloads, so it shows the real state."""
    return mutation_response(message=err.message, events=LEDGER_CHANGED, status=404)


@router.get("/groups/{group_id}/payments/new")
def new_dialog(
    group_id: Id,
    request: Request,
    user: User = Depends(current_user_html),
    conn: sqlite3.Connection = Depends(get_conn),
) -> Response:
    if (other := fragment_only(request, f"/groups/{group_id}")) is not None:
        return other
    group, _ = groups_service.require_member(conn, user, group_id)
    if not service.has_other_member(conn, group_id):
        invite = templates.TemplateResponse(
            request, "partials/groups/invite_dialog.html", {"group": group}
        )
        return htmx_response(invite, toast(NEED_MEMBER))
    view = service.form_view(conn, user, group_id)
    return _fragment(request, "partials/payments/form_dialog.html", view)


@router.post("/groups/{group_id}/payments")
def record(
    group_id: Id,
    request: Request,
    form: Annotated[PaymentForm, Form()],
    user: User = Depends(current_user_html),
    conn: sqlite3.Connection = Depends(get_conn),
) -> Response:
    try:
        service.record_payment(conn, user, group_id, form)
    except ValidationFailed as err:
        view = service.form_view(conn, user, group_id, form, err.fields)
        return _fragment(request, "partials/payments/form.html", view, 422)
    return mutation_response(message="Payment recorded", events=LEDGER_CHANGED)


@router.get("/groups/{group_id}/payments/{payment_id}/edit")
def edit_dialog(
    group_id: Id,
    payment_id: Id,
    request: Request,
    user: User = Depends(current_user_html),
    conn: sqlite3.Connection = Depends(get_conn),
) -> Response:
    if (other := fragment_only(request, f"/groups/{group_id}")) is not None:
        return other
    try:
        view = service.form_view(conn, user, group_id, payment_id=payment_id)
    except service.PaymentNotFound as err:
        return _gone(err)
    return _fragment(request, "partials/payments/form_dialog.html", view)


@router.post("/groups/{group_id}/payments/{payment_id}")
def save(
    group_id: Id,
    payment_id: Id,
    request: Request,
    form: Annotated[PaymentForm, Form()],
    user: User = Depends(current_user_html),
    conn: sqlite3.Connection = Depends(get_conn),
) -> Response:
    try:
        service.update_payment(conn, user, group_id, payment_id, form)
    except ValidationFailed as err:
        try:
            view = service.form_view(conn, user, group_id, form, err.fields, payment_id)
        except service.PaymentNotFound as gone:
            return _gone(gone)
        return _fragment(request, "partials/payments/form.html", view, 422)
    except service.PaymentNotFound as err:
        return _gone(err)
    return mutation_response(message="Payment updated", events=LEDGER_CHANGED)


@router.post("/groups/{group_id}/payments/{payment_id}/delete")
def delete(
    group_id: Id,
    payment_id: Id,
    user: User = Depends(current_user_html),
    conn: sqlite3.Connection = Depends(get_conn),
) -> Response:
    try:
        service.delete_payment(conn, user, group_id, payment_id)
    except service.PaymentNotFound as err:
        return _gone(err)
    return mutation_response(message="Payment deleted", events=LEDGER_CHANGED)
