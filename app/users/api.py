"""JSON API of the users: list, create with a token, and the current user."""

import sqlite3
from typing import Annotated

from fastapi import APIRouter, Depends

from app.core.db import get_conn
from app.core.session import User, current_user_api, sign_token
from app.users import service
from app.users.schemas import NEW_USER, UserIn, UserOut, UserWithToken

router = APIRouter(prefix="/api/v1", tags=["users"])


@router.get("/users")
def list_users(
    user: Annotated[User, Depends(current_user_api)],
    conn: Annotated[sqlite3.Connection, Depends(get_conn)],
) -> list[UserOut]:
    return [UserOut(id=u.id, name=u.name) for u in service.list_users(conn)]


@router.post("/users", status_code=201)
def create_user(
    body: UserIn, conn: Annotated[sqlite3.Connection, Depends(get_conn)]
) -> UserWithToken:
    """Open on purpose: a client has no token before it makes its first user."""
    user = service.sign_in(conn, NEW_USER, body.name)
    return UserWithToken(id=user.id, name=user.name, token=sign_token(user.id))


@router.get("/me")
def me(user: Annotated[User, Depends(current_user_api)]) -> UserOut:
    return UserOut(id=user.id, name=user.name)
