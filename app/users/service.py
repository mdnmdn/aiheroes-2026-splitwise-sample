"""Rules of the sign-in: user names, the next path and the sign-in itself."""

import re
import sqlite3

import structlog

from app.core.clock import now_iso
from app.core.db import transaction
from app.core.errors import ValidationFailed
from app.core.ids import parse_id
from app.core.limits import USER_NAME_MAX as NAME_MAX
from app.core.session import User, read_token
from app.groups.repo import count_groups
from app.users import repo
from app.users.schemas import NEW_USER

log = structlog.get_logger()

CHOOSE_ERROR = "Choose your name, or pick “New user…”."
_SAFE_NEXT = re.compile(r"/(?!/)[A-Za-z0-9_\-./?=&%]*")


def safe_next(value: str | None) -> str:
    """The value if it is a path on this app, else '/'."""
    return value if value and _SAFE_NEXT.fullmatch(value) else "/"


def name_error(name: str) -> str | None:
    """The error of a trimmed name for length, or None. Does not check for a duplicate."""
    if not name:
        return "Enter a name."
    if len(name) > NAME_MAX:
        return f"Use at most {NAME_MAX} characters."
    return None


def exists_error(name: str) -> str:
    return f"{name} is a user. Pick that user from the list or use a different name."


def validate_name(conn: sqlite3.Connection, raw: str, except_id: int | None = None) -> str:
    """The trimmed name, or ValidationFailed with the field error. Members use it too."""
    name = raw.strip()
    message = name_error(name)
    if message is None:
        found = repo.find_by_name(conn, name)
        if found and found.id != except_id:
            message = exists_error(name)
    if message:
        raise ValidationFailed(message, fields={"name": message})
    return name


def list_users(conn: sqlite3.Connection) -> list[User]:
    return repo.list_users(conn)


def find_by_token(conn: sqlite3.Connection, token: str | None) -> User | None:
    """The user of a valid token, or None when the token is bad or the user is gone."""
    user_id = read_token(token)
    return repo.find_by_id(conn, user_id) if user_id is not None else None


def sign_in(conn: sqlite3.Connection, user_id: str, name: str) -> User:
    """Pick a user by id, or create one when user_id is NEW_USER."""
    if user_id == NEW_USER:
        return _create(conn, name)
    user = repo.find_by_id(conn, parse_id(user_id))
    if user is None:
        raise ValidationFailed(CHOOSE_ERROR, fields={"user_id": CHOOSE_ERROR})
    return user


def _create(conn: sqlite3.Connection, raw: str) -> User:
    name = validate_name(conn, raw)
    try:
        with transaction(conn):
            user = repo.insert(conn, name, now_iso())
    except sqlite3.IntegrityError as err:
        message = exists_error(name)
        raise ValidationFailed(message, fields={"name": message}) from err
    log.info("user.created", user_id=user.id)
    return user


def menu_context(conn: sqlite3.Connection, user: User | None) -> dict[str, object]:
    """Template values that the topbar needs on every page."""
    return {"user": user, "group_count": count_groups(conn, user.id) if user else 0}
