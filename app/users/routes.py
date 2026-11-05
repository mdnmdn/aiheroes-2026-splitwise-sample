"""HTML routes of the sign-in: the login page and form, and sign out."""

import sqlite3
from typing import Annotated

import structlog
from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse, Response

from app.core.db import get_conn
from app.core.errors import ValidationFailed
from app.core.htmx import flash, is_htmx, set_events
from app.core.session import (
    HEADER_NAME,
    User,
    clear_session_cookie,
    optional_user,
    set_session_cookie,
    sign_token,
)
from app.core.templating import render
from app.users import service
from app.users.schemas import NEW_USER, LoginForm

router = APIRouter()
log = structlog.get_logger()


def _login_context(
    conn: sqlite3.Connection,
    user: User | None,
    form: LoginForm,
    errors: dict[str, str],
) -> dict[str, object]:
    users = service.list_users(conn)
    selected = form.user_id or (NEW_USER if not users else "")
    options = [("", "Select your name…")] if users else []
    options += [(str(u.id), u.name) for u in users] + [(NEW_USER, "New user…")]
    return {
        "user": user,
        "shell": "bare",
        "options": options,
        "selected": selected,
        "name": form.name,
        "next": service.safe_next(form.next),
        "errors": errors,
    }


@router.get("/login")
def login_page(
    request: Request,
    next: str = "",
    user: User | None = Depends(optional_user),
    conn: sqlite3.Connection = Depends(get_conn),
) -> Response:
    context = _login_context(conn, user, LoginForm(next=next), {})
    return render(request, "pages/login.html", context)


@router.post("/login")
def login(
    request: Request,
    form: Annotated[LoginForm, Form()],
    user: User | None = Depends(optional_user),
    conn: sqlite3.Connection = Depends(get_conn),
) -> Response:
    try:
        signed_in = service.sign_in(conn, form.user_id, form.name)
    except ValidationFailed as err:
        context = _login_context(conn, user, form, err.fields)
        template = "partials/users/login_form.html" if is_htmx(request) else "pages/login.html"
        return render(request, template, context, status_code=422)
    token = sign_token(signed_in.id)
    target = service.safe_next(form.next)
    if is_htmx(request):
        response = Response(headers={"HX-Redirect": target})
        set_events(response, {"session-start": {"token": token, "user_id": signed_in.id}})
    else:
        response = RedirectResponse(target, status_code=303)
    set_session_cookie(response, token)
    return flash(response, f"Signed in as {signed_in.name}.")


@router.post("/logout")
def logout() -> Response:
    response = RedirectResponse("/login", status_code=303)
    clear_session_cookie(response)
    return response


@router.post("/login/resume")
def resume(request: Request, conn: sqlite3.Connection = Depends(get_conn)) -> Response:
    """Put the token of this tab in the cookie. Reads the header only, never the cookie."""
    token = request.headers.get(HEADER_NAME)
    user = service.find_by_token(conn, token)
    if token is None or user is None:
        response = Response(status_code=401)
        clear_session_cookie(response)
        return response
    response = Response(status_code=204)
    set_session_cookie(response, token)
    log.info("session.resumed", user_id=user.id)
    return response
