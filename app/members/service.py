"""Rules of the members: add, remove, leave, and the members panel."""

import sqlite3
from dataclasses import dataclass

import structlog

from app.balances import service as balances_service
from app.balances.schemas import Breakdown, Summary
from app.core.clock import now_iso
from app.core.db import transaction
from app.core.errors import Conflict, NotFound, ValidationFailed
from app.core.ids import parse_id
from app.core.session import User
from app.groups import service as groups_service
from app.groups.schemas import Group
from app.members import repo
from app.members.schemas import Member, MemberRow
from app.users import repo as users_repo
from app.users import service as users_service
from app.users.schemas import NEW_USER

log = structlog.get_logger()

CHOOSE_ERROR = "Choose a user."
MEMBER_NOT_FOUND = "That member is not in this group."


@dataclass(frozen=True)
class Panel:
    group: Group
    rows: list[MemberRow]
    summary: Summary
    my_balance: int


def panel(conn: sqlite3.Connection, user: User, group_id: int) -> Panel:
    """The balances card: the members in join order with the balance of each one, and the stats."""
    group, me = groups_service.require_member(conn, user, group_id)
    summary = balances_service.summary(conn, group_id)
    balances = summary.balances
    rows = [
        MemberRow(member=m, balance=balances.get(m.id, 0), is_me=m.id == me.id)
        for m in repo.list_members(conn, group_id)
    ]
    return Panel(group=group, rows=rows, summary=summary, my_balance=balances.get(me.id, 0))


def get_member(
    conn: sqlite3.Connection, user: User, group_id: int, member_id: int
) -> tuple[Group, Member]:
    group, _ = groups_service.require_member(conn, user, group_id)
    member = repo.find(conn, group_id, member_id)
    if member is None:
        raise NotFound(MEMBER_NOT_FOUND)
    return group, member


@dataclass(frozen=True)
class Detail:
    group: Group
    member: Member
    balance: int
    removable: bool
    is_me: bool
    breakdown: Breakdown


def detail(conn: sqlite3.Connection, user: User, group_id: int, member_id: int) -> Detail:
    """What the member dialog shows: the balance and its breakdown from the balances feature."""
    group, member = get_member(conn, user, group_id, member_id)
    breakdown = balances_service.breakdown(conn, group_id, member.id, group.currency)
    return Detail(
        group=group,
        member=member,
        balance=balances_service.group_balances(conn, group_id).get(member.id, 0),
        removable=not repo.has_transaction(conn, member.id),
        is_me=member.user_id == user.id,
        breakdown=breakdown,
    )


def add_options(conn: sqlite3.Connection, user: User, group_id: int) -> tuple[Group, list[User]]:
    """The group and the users who are not members of it, by name."""
    group, _ = groups_service.require_member(conn, user, group_id)
    return group, repo.users_not_in_group(conn, group_id)


def add_member(
    conn: sqlite3.Connection, user: User, group_id: int, user_id: str, raw_name: str
) -> Member:
    """Add an existing user, or create a user when user_id is NEW_USER. Last in join order."""
    group, _ = groups_service.require_member(conn, user, group_id)
    try:
        with transaction(conn):
            target = _target_user(conn, group_id, user_id, raw_name)
            repo.insert(conn, group_id, target.id, now_iso())
    except sqlite3.IntegrityError as err:
        # A unique index rejected a concurrent request: the same member or the same user name.
        if user_id == NEW_USER:
            message = users_service.exists_error(raw_name.strip())
            raise ValidationFailed(message, fields={"name": message}) from err
        found = users_repo.find_by_id(conn, parse_id(user_id))
        message = f"{found.name if found else 'This user'} is a member of this group."
        raise ValidationFailed(message, fields={"user_id": message}) from err
    member = repo.find_by_user(conn, group_id, target.id)
    assert member is not None
    log.info("member.added", group_id=group.id, member_id=member.id, user_id=user.id)
    return member


def add_member_by_body(
    conn: sqlite3.Connection, user: User, group_id: int, user_id: int | None, name: str | None
) -> Member:
    """The API choice: user_id wins, else name creates a user, else ValidationFailed."""
    if user_id is not None:
        return add_member(conn, user, group_id, str(user_id), "")
    if name is not None:
        return add_member(conn, user, group_id, NEW_USER, name)
    message = "Send user_id or name."
    raise ValidationFailed(message, fields={"user_id": message, "name": message})


def _target_user(conn: sqlite3.Connection, group_id: int, user_id: str, raw_name: str) -> User:
    if user_id == NEW_USER:
        name = users_service.validate_name(conn, raw_name)
        return users_repo.insert(conn, name, now_iso())
    found = users_repo.find_by_id(conn, parse_id(user_id))
    if found is None:
        raise ValidationFailed(CHOOSE_ERROR, fields={"user_id": CHOOSE_ERROR})
    if repo.find_by_user(conn, group_id, found.id):
        message = f"{found.name} is a member of this group."
        raise ValidationFailed(message, fields={"user_id": message})
    return found


def remove_member(conn: sqlite3.Connection, user: User, group_id: int, member_id: int) -> Member:
    """Delete the member and keep the user. Conflict if the member has a transaction.

    A user cannot remove the own member here. Leave does that.
    """
    _, member = get_member(conn, user, group_id, member_id)
    if member.user_id == user.id:
        raise Conflict("You cannot remove yourself. Use Leave.")
    _delete(conn, member)
    log.info("member.removed", group_id=group_id, member_id=member_id, user_id=user.id)
    return member


def leave_group(conn: sqlite3.Connection, user: User, group_id: int) -> Group:
    group, me = groups_service.require_member(conn, user, group_id)
    _delete(conn, me)
    log.info("member.left", group_id=group_id, member_id=me.id, user_id=user.id)
    return group


def _delete(conn: sqlite3.Connection, member: Member) -> None:
    conflict = Conflict(f"{member.name} has transactions in this group.")
    try:
        with transaction(conn):
            if repo.has_transaction(conn, member.id):
                raise conflict
            repo.delete(conn, member.id)
    except sqlite3.IntegrityError as err:
        raise conflict from err  # a transaction came in at the same time


def list_members(conn: sqlite3.Connection, user: User, group_id: int) -> list[Member]:
    """The members of the group in join order."""
    groups_service.require_member(conn, user, group_id)
    return repo.list_members(conn, group_id)
