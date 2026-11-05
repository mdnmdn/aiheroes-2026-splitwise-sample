"""JSON API of the balances: the balance of each member, and the transactions.
Money is an integer in minor units."""

import sqlite3
from typing import Annotated

from fastapi import APIRouter, Depends

from app.balances import service
from app.balances.schemas import BalanceOut, TransactionOut
from app.core.db import get_conn
from app.core.ids import Id
from app.core.session import User, current_user_api
from app.groups import service as groups_service

router = APIRouter(prefix="/api/v1", tags=["balances"])

CurrentUser = Annotated[User, Depends(current_user_api)]
Conn = Annotated[sqlite3.Connection, Depends(get_conn)]


@router.get("/groups/{group_id}/balances")
def list_balances(group_id: Id, user: CurrentUser, conn: Conn) -> list[BalanceOut]:
    group, _ = groups_service.require_member(conn, user, group_id)
    balances = service.group_balances(conn, group_id)
    return [
        BalanceOut(member_id=member_id, balance=balance, currency=group.currency)
        for member_id, balance in balances.items()
    ]


@router.get("/groups/{group_id}/transactions")
def list_transactions(group_id: Id, user: CurrentUser, conn: Conn) -> list[TransactionOut]:
    group, me = groups_service.require_member(conn, user, group_id)
    tx = service.transaction_list(conn, group_id, me.id)
    return [
        TransactionOut(**vars(row), currency=group.currency) for day in tx.days for row in day.rows
    ]
