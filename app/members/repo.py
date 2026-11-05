"""SQL of the members feature: the table members. Reads users, expenses and payments."""

import sqlite3

from app.core.session import User
from app.members.schemas import Member

_SELECT = "SELECT m.id, m.user_id, u.name FROM members m JOIN users u ON u.id = m.user_id"


def _member(row: sqlite3.Row) -> Member:
    return Member(id=row["id"], user_id=row["user_id"], name=row["name"])


def list_members(conn: sqlite3.Connection, group_id: int) -> list[Member]:
    rows = conn.execute(f"{_SELECT} WHERE m.group_id = ? ORDER BY m.id", (group_id,))
    return [_member(r) for r in rows]


def find(conn: sqlite3.Connection, group_id: int, member_id: int) -> Member | None:
    row = conn.execute(f"{_SELECT} WHERE m.group_id = ? AND m.id = ?", (group_id, member_id))
    found = row.fetchone()
    return _member(found) if found else None


def find_by_user(conn: sqlite3.Connection, group_id: int, user_id: int) -> Member | None:
    row = conn.execute(f"{_SELECT} WHERE m.group_id = ? AND m.user_id = ?", (group_id, user_id))
    found = row.fetchone()
    return _member(found) if found else None


def insert(conn: sqlite3.Connection, group_id: int, user_id: int, joined_at: str) -> int:
    """Raises sqlite3.IntegrityError when the user is a member of the group."""
    cursor = conn.execute(
        "INSERT INTO members (group_id, user_id, joined_at) VALUES (?, ?, ?)",
        (group_id, user_id, joined_at),
    )
    return int(cursor.lastrowid or 0)


def delete(conn: sqlite3.Connection, member_id: int) -> None:
    """Raises sqlite3.IntegrityError when a transaction references the member."""
    conn.execute("DELETE FROM members WHERE id = ?", (member_id,))


def has_transaction(conn: sqlite3.Connection, member_id: int) -> bool:
    """True if the member is the payer or a participant of an expense, or in a payment."""
    row = conn.execute(
        """
        SELECT EXISTS (SELECT 1 FROM expenses WHERE payer_id = :id)
            OR EXISTS (SELECT 1 FROM expense_shares WHERE member_id = :id)
            OR EXISTS (SELECT 1 FROM payments WHERE sender_id = :id OR receiver_id = :id) AS used
        """,
        {"id": member_id},
    ).fetchone()
    return bool(row["used"])


def users_not_in_group(conn: sqlite3.Connection, group_id: int) -> list[User]:
    rows = conn.execute(
        "SELECT id, name FROM users"
        " WHERE id NOT IN (SELECT user_id FROM members WHERE group_id = ?) ORDER BY name",
        (group_id,),
    )
    return [User(id=r["id"], name=r["name"]) for r in rows]
