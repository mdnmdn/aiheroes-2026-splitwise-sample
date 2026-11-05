"""Simulated sign-in: signed token, cookie and header. Development only, not security.

Resolution order: header X-Splitwise-User, then cookie sw_user, then none.
See _docs/tech/guide-authentication.md.
"""

import sqlite3
from dataclasses import dataclass

import structlog
from fastapi import Depends, Request, Response
from itsdangerous import BadSignature, URLSafeSerializer

from app.core.config import get_settings
from app.core.db import get_conn
from app.core.errors import NotSignedIn

COOKIE_NAME = "sw_user"
HEADER_NAME = "X-Splitwise-User"
SALT = "sw-user"


@dataclass(frozen=True)
class User:
    id: int
    name: str


def _serializer() -> URLSafeSerializer:
    return URLSafeSerializer(get_settings().secret_key or "", salt=SALT)


def sign_token(user_id: int) -> str:
    return _serializer().dumps(user_id)


def read_token(token: str | None) -> int | None:
    """The user id in a token, or None when the token is missing or its signature is bad."""
    if not token:
        return None
    try:
        value = _serializer().loads(token)
    except BadSignature:
        return None
    return value if isinstance(value, int) else None


def set_session_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        COOKIE_NAME,
        token,
        httponly=True,
        samesite="lax",
        secure=get_settings().env == "prod",
    )


def clear_session_cookie(response: Response) -> None:
    response.delete_cookie(COOKIE_NAME)


def _resolve(request: Request, conn: sqlite3.Connection) -> User | None:
    # Lazy import: users.repo imports User from this module, so a top-level import is a cycle.
    from app.users.repo import find_by_id

    for token in (request.headers.get(HEADER_NAME), request.cookies.get(COOKIE_NAME)):
        user_id = read_token(token)
        user = find_by_id(conn, user_id) if user_id is not None else None
        if user:
            structlog.contextvars.bind_contextvars(user_id=user.id)
            return user
    return None


async def optional_user(
    request: Request, conn: sqlite3.Connection = Depends(get_conn)
) -> User | None:
    return _resolve(request, conn)


async def current_user_html(request: Request, conn: sqlite3.Connection = Depends(get_conn)) -> User:
    """Raises NotSignedIn: the handler redirects to /login?next=..."""
    user = _resolve(request, conn)
    if user is None:
        raise NotSignedIn("Sign in first")
    return user


async def current_user_api(request: Request, conn: sqlite3.Connection = Depends(get_conn)) -> User:
    """Raises NotSignedIn: the handler returns 401 JSON for /api/ paths."""
    return await current_user_html(request, conn)
