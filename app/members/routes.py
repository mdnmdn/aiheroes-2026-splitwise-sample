"""HTML routes of the members: the panel, the member dialog, add and remove."""

import sqlite3
from typing import Annotated

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import Response

from app.core.db import get_conn
from app.core.errors import Conflict, NotFound, ValidationFailed
from app.core.htmx import fragment_only, mutation_response
from app.core.ids import Id
from app.core.session import User, current_user_html
from app.core.templating import templates
from app.members import service
from app.members.schemas import AddMemberForm
from app.users.schemas import NEW_USER

router = APIRouter()

MEMBERS_CHANGED = {"members-changed": {}}


def _fragment(
    request: Request, name: str, context: dict[str, object], status: int = 200
) -> Response:
    return templates.TemplateResponse(request, name, context, status_code=status)


def _add_context(
    conn: sqlite3.Connection, user: User, group_id: int, form: AddMemberForm, errors: dict[str, str]
) -> dict[str, object]:
    group, users = service.add_options(conn, user, group_id)
    options = [(str(u.id), u.name) for u in users] + [(NEW_USER, "New user…")]
    selected = form.user_id or (str(users[0].id) if users else NEW_USER)
    return {
        "group": group,
        "options": options,
        "selected": selected,
        "name": form.name,
        "errors": errors,
    }


@router.get("/groups/{group_id}/members")
def members_panel(
    group_id: Id,
    request: Request,
    user: User = Depends(current_user_html),
    conn: sqlite3.Connection = Depends(get_conn),
) -> Response:
    if (other := fragment_only(request, f"/groups/{group_id}")) is not None:
        return other
    panel = service.panel(conn, user, group_id)
    return _fragment(request, "partials/members/panel.html", {"group": panel.group, **vars(panel)})


@router.get("/groups/{group_id}/members/new")
def add_dialog(
    group_id: Id,
    request: Request,
    user: User = Depends(current_user_html),
    conn: sqlite3.Connection = Depends(get_conn),
) -> Response:
    if (other := fragment_only(request, f"/groups/{group_id}")) is not None:
        return other
    context = _add_context(conn, user, group_id, AddMemberForm(), {})
    return _fragment(request, "partials/members/add_dialog.html", context)


@router.post("/groups/{group_id}/members")
def add(
    group_id: Id,
    request: Request,
    form: Annotated[AddMemberForm, Form()],
    user: User = Depends(current_user_html),
    conn: sqlite3.Connection = Depends(get_conn),
) -> Response:
    try:
        member = service.add_member(conn, user, group_id, form.user_id, form.name)
    except ValidationFailed as err:
        context = _add_context(conn, user, group_id, form, err.fields)
        return _fragment(request, "partials/members/add_form.html", context, 422)
    group, _ = service.add_options(conn, user, group_id)
    return mutation_response(message=f"{member.name} added to {group.name}", events=MEMBERS_CHANGED)


@router.get("/groups/{group_id}/members/{member_id}")
def member_dialog(
    group_id: Id,
    member_id: Id,
    request: Request,
    user: User = Depends(current_user_html),
    conn: sqlite3.Connection = Depends(get_conn),
) -> Response:
    if (other := fragment_only(request, f"/groups/{group_id}")) is not None:
        return other
    detail = service.detail(conn, user, group_id, member_id)
    return _fragment(request, "partials/members/detail_dialog.html", vars(detail))


@router.post("/groups/{group_id}/members/{member_id}/delete")
def remove(
    group_id: Id,
    member_id: Id,
    user: User = Depends(current_user_html),
    conn: sqlite3.Connection = Depends(get_conn),
) -> Response:
    try:
        member = service.remove_member(conn, user, group_id, member_id)
    except (Conflict, NotFound) as err:
        # The panel reloads, so it shows the real state. The status tells the client what failed.
        return mutation_response(message=err.message, events=MEMBERS_CHANGED, status=err.status)
    return mutation_response(message=f"{member.name} removed", events=MEMBERS_CHANGED)
