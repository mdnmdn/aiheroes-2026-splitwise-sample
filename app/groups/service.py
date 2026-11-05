"""Rules of the groups: names, invite codes, create, rename, join and the home list."""

import random
import re
import sqlite3
from collections.abc import Callable
from dataclasses import dataclass

import structlog

from app.balances.service import balances_of_groups
from app.core.clock import now_iso
from app.core.db import transaction
from app.core.errors import Conflict, NotFound, ValidationFailed
from app.core.limits import GROUP_NAME_MAX as NAME_MAX
from app.core.money import CURRENCIES
from app.core.session import User
from app.groups import repo
from app.groups.schemas import FILTERS, Group, GroupList, GroupRow
from app.members import repo as members_repo
from app.members.schemas import Member

log = structlog.get_logger()

CODE_ALPHABET = "ABCDEFGHJKMNPQRSTUVWXYZ23456789"
CODE_TRIES = 10
NOT_AVAILABLE = "That group is not available to you."
_PREFIX_CHARS = re.compile(r"[^A-Za-z0-9]")


def validate_name(raw: str) -> str:
    """The trimmed group name, or ValidationFailed with the field error."""
    name = raw.strip()
    message = None
    if not name:
        message = "Give the group a name."
    elif len(name) > NAME_MAX:
        message = f"Use at most {NAME_MAX} characters."
    if message:
        raise ValidationFailed(message, fields={"name": message})
    return name


def validate_currency(value: str) -> str:
    code = value.strip().upper()
    if code not in CURRENCIES:
        message = "Choose a currency."
        raise ValidationFailed(message, fields={"currency": message})
    return code


def invite_prefix(name: str) -> str:
    """XXX of the invite code: the first 3 letters and digits in capitals, padded with X."""
    chars = _PREFIX_CHARS.sub("", name)[:3].upper()
    return chars.ljust(3, "X") if chars else "GRP"


def draw_code(name: str, taken: Callable[[str], bool]) -> str:
    """A code XXX-YYYY that `taken` does not know. Draws YYYY again until it is free."""
    prefix = invite_prefix(name)
    while True:
        code = f"{prefix}-{''.join(random.choices(CODE_ALPHABET, k=4))}"
        if not taken(code):
            return code


def require_member(conn: sqlite3.Connection, user: User, group_id: int) -> tuple[Group, Member]:
    """The group and the member of the user. NotFound if either does not exist."""
    group = repo.find(conn, group_id)
    member = members_repo.find_by_user(conn, group_id, user.id) if group else None
    if group is None or member is None:
        raise NotFound(NOT_AVAILABLE)
    return group, member


def create_group(conn: sqlite3.Connection, user: User, raw_name: str, raw_currency: str) -> Group:
    name = validate_name(raw_name)
    currency = validate_currency(raw_currency)
    for _ in range(CODE_TRIES):
        code = draw_code(name, lambda c: repo.code_exists(conn, c))
        try:
            with transaction(conn):
                now = now_iso()
                group_id = repo.insert(conn, name, currency, code, now)
                members_repo.insert(conn, group_id, user.id, now)
        except sqlite3.IntegrityError:
            continue  # the code was taken between the check and the insert
        log.info("group.created", group_id=group_id, user_id=user.id)
        return Group(id=group_id, name=name, currency=currency, invite_code=code)
    raise Conflict("The app could not make an invite code. Try again.")


def update_group(conn: sqlite3.Connection, user: User, group_id: int, raw_name: str) -> Group:
    """Rename. The base currency and the invite code never change."""
    group, _ = require_member(conn, user, group_id)
    name = validate_name(raw_name)
    with transaction(conn):
        repo.rename(conn, group_id, name)
    log.info("group.renamed", group_id=group_id, user_id=user.id)
    return Group(id=group.id, name=name, currency=group.currency, invite_code=group.invite_code)


@dataclass(frozen=True)
class JoinResult:
    group: Group
    joined: bool


def join(conn: sqlite3.Connection, user: User, raw_code: str) -> JoinResult:
    code = raw_code.strip().upper()
    if not code:
        message = "Enter an invite code."
        raise ValidationFailed(message, fields={"code": message})
    group = repo.find_by_code(conn, code)
    if group is None:
        message = "No group uses this code. Check it with the person who invited you."
        raise ValidationFailed(message, fields={"code": message})
    try:
        with transaction(conn):
            if members_repo.find_by_user(conn, group.id, user.id):
                return JoinResult(group, joined=False)
            members_repo.insert(conn, group.id, user.id, now_iso())
    except sqlite3.IntegrityError:
        return JoinResult(group, joined=False)  # joined in another request first
    log.info("member.joined", group_id=group.id, user_id=user.id)
    return JoinResult(group, joined=True)


def list_groups(
    conn: sqlite3.Connection, user: User, q: str = "", filter_: str = "all"
) -> GroupList:
    """The groups of the user with the balance of the user, searched and filtered."""
    found = repo.list_for_user(conn, user.id)
    balances = balances_of_groups(conn, [r["id"] for r in found])
    rows = [
        GroupRow(
            id=r["id"],
            name=r["name"],
            currency=r["currency"],
            member_count=r["member_count"],
            transaction_count=r["transaction_count"],
            balance=balances[r["id"]].get(r["member_id"], 0),
        )
        for r in found
    ]
    needle = q.strip().lower()
    mode = filter_ if filter_ in FILTERS else "all"

    def shown(row: GroupRow) -> bool:
        if needle not in row.name.lower():
            return False
        return mode == "all" or (row.balance < 0 if mode == "owe" else row.balance > 0)

    return GroupList(rows=[r for r in rows if shown(r)], total=len(rows))
