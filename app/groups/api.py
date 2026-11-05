"""JSON API of the groups: list, create, read, rename and join."""

import sqlite3
from typing import Annotated

from fastapi import APIRouter, Depends

from app.core.db import get_conn
from app.core.ids import Id
from app.core.session import User, current_user_api
from app.groups import service
from app.groups.schemas import (
    Group,
    GroupIn,
    GroupJoin,
    GroupOut,
    GroupRename,
    GroupRowOut,
)

router = APIRouter(prefix="/api/v1", tags=["groups"])

CurrentUser = Annotated[User, Depends(current_user_api)]
Conn = Annotated[sqlite3.Connection, Depends(get_conn)]


def group_out(group: Group) -> GroupOut:
    return GroupOut(
        id=group.id, name=group.name, currency=group.currency, invite_code=group.invite_code
    )


@router.get("/groups")
def list_groups(
    user: CurrentUser, conn: Conn, q: str = "", filter: str = "all"
) -> list[GroupRowOut]:
    found = service.list_groups(conn, user, q, filter)
    return [GroupRowOut(**vars(row)) for row in found.rows]


@router.post("/groups", status_code=201)
def create_group(body: GroupIn, user: CurrentUser, conn: Conn) -> GroupOut:
    return group_out(service.create_group(conn, user, body.name, body.currency))


@router.post("/groups/join")
def join_group(body: GroupJoin, user: CurrentUser, conn: Conn) -> GroupOut:
    return group_out(service.join(conn, user, body.code).group)


@router.get("/groups/{group_id}")
def get_group(group_id: Id, user: CurrentUser, conn: Conn) -> GroupOut:
    group, _ = service.require_member(conn, user, group_id)
    return group_out(group)


@router.patch("/groups/{group_id}")
def rename_group(group_id: Id, body: GroupRename, user: CurrentUser, conn: Conn) -> GroupOut:
    return group_out(service.update_group(conn, user, group_id, body.name))
