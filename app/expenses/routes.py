"""HTML routes of the expenses: dialogs, the share preview, add, edit and delete."""

import sqlite3
from typing import Annotated

from fastapi import APIRouter, Depends, Form, Query, Request
from fastapi.responses import Response

from app.core.db import get_conn
from app.core.errors import ValidationFailed
from app.core.htmx import fragment_only, mutation_response
from app.core.ids import Id
from app.core.session import User, current_user_html
from app.core.templating import templates
from app.expenses import service
from app.expenses.schemas import ExpenseForm

router = APIRouter()

LEDGER_CHANGED = {"ledger-changed": {}}


def _fragment(request: Request, name: str, view: object, status: int = 200) -> Response:
    context = {"view": view}
    return templates.TemplateResponse(request, name, context, status_code=status)


def _gone(err: service.ExpenseNotFound) -> Response:
    """The expense is gone. The list reloads, so it shows the real state."""
    return mutation_response(message=err.message, events=LEDGER_CHANGED, status=404)


@router.get("/groups/{group_id}/expenses/new")
def new_dialog(
    group_id: Id,
    request: Request,
    user: User = Depends(current_user_html),
    conn: sqlite3.Connection = Depends(get_conn),
) -> Response:
    if (other := fragment_only(request, f"/groups/{group_id}")) is not None:
        return other
    view = service.form_view(conn, user, group_id)
    return _fragment(request, "partials/expenses/form_dialog.html", view)


@router.get("/groups/{group_id}/expenses/preview")
def preview(
    group_id: Id,
    request: Request,
    amount: str = "",
    p: Annotated[list[str] | None, Query()] = None,
    user: User = Depends(current_user_html),
    conn: sqlite3.Connection = Depends(get_conn),
) -> Response:
    if (other := fragment_only(request, f"/groups/{group_id}")) is not None:
        return other
    group, members, shown = service.preview(conn, user, group_id, amount, p or [])
    context = {"group": group, "members": members, "preview": shown, "checked": p or []}
    return templates.TemplateResponse(request, "partials/expenses/preview.html", context)


@router.post("/groups/{group_id}/expenses")
def add(
    group_id: Id,
    request: Request,
    form: Annotated[ExpenseForm, Form()],
    user: User = Depends(current_user_html),
    conn: sqlite3.Connection = Depends(get_conn),
) -> Response:
    try:
        service.add_expense(conn, user, group_id, form)
    except ValidationFailed as err:
        view = service.form_view(conn, user, group_id, form, err.fields)
        return _fragment(request, "partials/expenses/form.html", view, 422)
    return mutation_response(message="Expense added", events=LEDGER_CHANGED)


@router.get("/groups/{group_id}/expenses/{expense_id}/edit")
def edit_dialog(
    group_id: Id,
    expense_id: Id,
    request: Request,
    user: User = Depends(current_user_html),
    conn: sqlite3.Connection = Depends(get_conn),
) -> Response:
    if (other := fragment_only(request, f"/groups/{group_id}")) is not None:
        return other
    try:
        view = service.form_view(conn, user, group_id, expense_id=expense_id)
    except service.ExpenseNotFound as err:
        return _gone(err)
    return _fragment(request, "partials/expenses/form_dialog.html", view)


@router.post("/groups/{group_id}/expenses/{expense_id}")
def save(
    group_id: Id,
    expense_id: Id,
    request: Request,
    form: Annotated[ExpenseForm, Form()],
    user: User = Depends(current_user_html),
    conn: sqlite3.Connection = Depends(get_conn),
) -> Response:
    try:
        service.update_expense(conn, user, group_id, expense_id, form)
    except ValidationFailed as err:
        try:
            view = service.form_view(conn, user, group_id, form, err.fields, expense_id)
        except service.ExpenseNotFound as gone:
            return _gone(gone)
        return _fragment(request, "partials/expenses/form.html", view, 422)
    except service.ExpenseNotFound as err:
        return _gone(err)
    return mutation_response(message="Expense updated", events=LEDGER_CHANGED)


@router.post("/groups/{group_id}/expenses/{expense_id}/delete")
def delete(
    group_id: Id,
    expense_id: Id,
    user: User = Depends(current_user_html),
    conn: sqlite3.Connection = Depends(get_conn),
) -> Response:
    try:
        service.delete_expense(conn, user, group_id, expense_id)
    except service.ExpenseNotFound as err:
        return _gone(err)
    return mutation_response(message="Expense deleted", events=LEDGER_CHANGED)
