"""HTML routes of the groups: the home, the list fragment, dialogs, join, leave, the group page."""

import sqlite3
from typing import Annotated

from fastapi import APIRouter, Depends, Form, Query, Request
from fastapi.responses import Response

from app.balances import service as balances_service
from app.core.db import get_conn
from app.core.errors import Conflict, NotFound, ValidationFailed
from app.core.htmx import fragment_only, mutation_response, redirect_to
from app.core.ids import Id
from app.core.money import CURRENCIES, symbol
from app.core.session import User, current_user_html
from app.core.templating import render, templates
from app.groups import service
from app.groups.schemas import GroupForm, JoinForm
from app.members import service as members_service
from app.users import service as users_service

router = APIRouter()

CURRENCY_OPTIONS = [(code, f"{code} — {symbol(code)}") for code in CURRENCIES]
DEFAULT_CURRENCY = "EUR"


def _fragment(
    request: Request, name: str, context: dict[str, object], status: int = 200
) -> Response:
    return templates.TemplateResponse(request, name, context, status_code=status)


def _create_context(form: GroupForm, errors: dict[str, str]) -> dict[str, object]:
    return {
        "name": form.name,
        "currency": form.currency,
        "currency_options": CURRENCY_OPTIONS,
        "errors": errors,
    }


@router.get("/")
def home(
    request: Request,
    user: User = Depends(current_user_html),
    conn: sqlite3.Connection = Depends(get_conn),
) -> Response:
    context = users_service.menu_context(conn, user)
    context["groups"] = service.list_groups(conn, user)
    return render(request, "pages/groups_home.html", context)


@router.get("/groups/list")
def group_list(
    request: Request,
    q: str = "",
    filter_: Annotated[str, Query(alias="filter")] = "all",
    user: User = Depends(current_user_html),
    conn: sqlite3.Connection = Depends(get_conn),
) -> Response:
    if (other := fragment_only(request, "/")) is not None:
        return other
    groups = service.list_groups(conn, user, q, filter_)
    return _fragment(request, "partials/groups/list.html", {"groups": groups, "oob": True})


@router.get("/groups/new")
def new_dialog(request: Request, user: User = Depends(current_user_html)) -> Response:
    if (other := fragment_only(request, "/")) is not None:
        return other
    context = _create_context(GroupForm(currency=DEFAULT_CURRENCY), {})
    return _fragment(request, "partials/groups/create_dialog.html", context)


@router.post("/groups")
def create(
    request: Request,
    form: Annotated[GroupForm, Form()],
    user: User = Depends(current_user_html),
    conn: sqlite3.Connection = Depends(get_conn),
) -> Response:
    try:
        group = service.create_group(conn, user, form.name, form.currency)
    except ValidationFailed as err:
        context = _create_context(form, err.fields)
        return _fragment(request, "partials/groups/create_form.html", context, 422)
    message = f"{group.name} created. Invite people with its code."
    return redirect_to(request, f"/groups/{group.id}", message)


@router.post("/groups/join")
def join(
    request: Request,
    form: Annotated[JoinForm, Form()],
    user: User = Depends(current_user_html),
    conn: sqlite3.Connection = Depends(get_conn),
) -> Response:
    try:
        result = service.join(conn, user, form.code)
    except ValidationFailed as err:
        context = {"code": form.code, "errors": err.fields}
        return _fragment(request, "partials/groups/join_card.html", context, 422)
    name = result.group.name
    message = f"You joined {name}" if result.joined else f"You are in {name}"
    return redirect_to(request, f"/groups/{result.group.id}", message)


@router.get("/groups/{group_id}")
def group_page(
    group_id: Id,
    request: Request,
    user: User = Depends(current_user_html),
    conn: sqlite3.Connection = Depends(get_conn),
) -> Response:
    try:
        panel = members_service.panel(conn, user, group_id)
    except NotFound as err:
        return redirect_to(request, "/", err.message)
    context = users_service.menu_context(conn, user)
    me = next(row.member for row in panel.rows if row.is_me)
    tx = balances_service.transaction_list(conn, group_id, me.id)
    context.update(vars(panel), tx=tx)
    return render(request, "pages/group.html", context)


@router.get("/groups/{group_id}/settings")
def settings_dialog(
    group_id: Id,
    request: Request,
    user: User = Depends(current_user_html),
    conn: sqlite3.Connection = Depends(get_conn),
) -> Response:
    if (other := fragment_only(request, f"/groups/{group_id}")) is not None:
        return other
    group, _ = service.require_member(conn, user, group_id)
    context = {"group": group, "name": group.name, "errors": {}}
    return _fragment(request, "partials/groups/settings_dialog.html", context)


@router.post("/groups/{group_id}/settings")
def save_settings(
    group_id: Id,
    request: Request,
    form: Annotated[GroupForm, Form()],
    user: User = Depends(current_user_html),
    conn: sqlite3.Connection = Depends(get_conn),
) -> Response:
    try:
        group = service.update_group(conn, user, group_id, form.name)
    except ValidationFailed as err:
        current, _ = service.require_member(conn, user, group_id)
        context = {"group": current, "name": form.name, "errors": err.fields}
        return _fragment(request, "partials/groups/settings_form.html", context, 422)
    context = users_service.menu_context(conn, user)
    context["group"] = group
    topbar = _fragment(request, "partials/groups/topbar.html", context)
    return mutation_response(topbar, message="Group updated")


@router.get("/groups/{group_id}/invite")
def invite_dialog(
    group_id: Id,
    request: Request,
    user: User = Depends(current_user_html),
    conn: sqlite3.Connection = Depends(get_conn),
) -> Response:
    if (other := fragment_only(request, f"/groups/{group_id}")) is not None:
        return other
    group, _ = service.require_member(conn, user, group_id)
    return _fragment(request, "partials/groups/invite_dialog.html", {"group": group})


@router.post("/groups/{group_id}/leave")
def leave(
    group_id: Id,
    request: Request,
    user: User = Depends(current_user_html),
    conn: sqlite3.Connection = Depends(get_conn),
) -> Response:
    try:
        group = members_service.leave_group(conn, user, group_id)
    except NotFound as err:
        return redirect_to(request, "/", err.message, status=404)
    except Conflict as err:
        return mutation_response(message=err.message, events={"members-changed": {}}, status=409)
    return redirect_to(request, "/", f"You left {group.name}")
