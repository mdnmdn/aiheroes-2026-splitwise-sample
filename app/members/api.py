"""JSON API of the members: list, add and remove."""

import sqlite3
from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.responses import Response

from app.core.db import get_conn
from app.core.ids import Id
from app.core.session import User, current_user_api
from app.members import service
from app.members.schemas import Member, MemberAddIn, MemberOut

router = APIRouter(prefix="/api/v1", tags=["members"])

CurrentUser = Annotated[User, Depends(current_user_api)]
Conn = Annotated[sqlite3.Connection, Depends(get_conn)]


def member_out(member: Member) -> MemberOut:
    return MemberOut(id=member.id, user_id=member.user_id, name=member.name)


@router.get("/groups/{group_id}/members")
def list_members(group_id: Id, user: CurrentUser, conn: Conn) -> list[MemberOut]:
    return [member_out(m) for m in service.list_members(conn, user, group_id)]


@router.post("/groups/{group_id}/members", status_code=201)
def add_member(group_id: Id, body: MemberAddIn, user: CurrentUser, conn: Conn) -> MemberOut:
    return member_out(service.add_member_by_body(conn, user, group_id, body.user_id, body.name))


@router.delete("/groups/{group_id}/members/{member_id}", status_code=204)
def remove_member(group_id: Id, member_id: Id, user: CurrentUser, conn: Conn) -> Response:
    service.remove_member(conn, user, group_id, member_id)
    return Response(status_code=204)
