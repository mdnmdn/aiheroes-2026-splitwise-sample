"""HTML routes of the balances feature: the transaction list."""

import sqlite3
from typing import Annotated

from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import Response

from app.balances import service
from app.core.db import get_conn
from app.core.htmx import fragment_only
from app.core.ids import Id
from app.core.session import User, current_user_html
from app.core.templating import templates
from app.groups import service as groups_service

router = APIRouter()


@router.get("/groups/{group_id}/transactions")
def transactions(
    group_id: Id,
    request: Request,
    filter_: Annotated[str, Query(alias="filter")] = "all",
    user: User = Depends(current_user_html),
    conn: sqlite3.Connection = Depends(get_conn),
) -> Response:
    if (other := fragment_only(request, f"/groups/{group_id}")) is not None:
        return other
    group, me = groups_service.require_member(conn, user, group_id)
    tx = service.transaction_list(conn, group_id, me.id, filter_)
    context = {"group": group, "tx": tx}
    return templates.TemplateResponse(request, "partials/balances/transactions.html", context)
