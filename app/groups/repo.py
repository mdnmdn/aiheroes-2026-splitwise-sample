"""SQL of the groups feature: the table groups. Reads members, expenses and payments."""

import sqlite3

from app.groups.schemas import Group


def _group(row: sqlite3.Row) -> Group:
    return Group(
        id=row["id"], name=row["name"], currency=row["currency"], invite_code=row["invite_code"]
    )


def insert(conn: sqlite3.Connection, name: str, currency: str, code: str, created_at: str) -> int:
    """Raises sqlite3.IntegrityError when the invite code exists."""
    cursor = conn.execute(
        "INSERT INTO groups (name, currency, invite_code, created_at) VALUES (?, ?, ?, ?)",
        (name, currency, code, created_at),
    )
    return int(cursor.lastrowid or 0)


def find(conn: sqlite3.Connection, group_id: int) -> Group | None:
    row = conn.execute(
        "SELECT id, name, currency, invite_code FROM groups WHERE id = ?", (group_id,)
    ).fetchone()
    return _group(row) if row else None


def find_by_code(conn: sqlite3.Connection, code: str) -> Group | None:
    row = conn.execute(
        "SELECT id, name, currency, invite_code FROM groups WHERE invite_code = ?", (code,)
    ).fetchone()
    return _group(row) if row else None


def code_exists(conn: sqlite3.Connection, code: str) -> bool:
    return find_by_code(conn, code) is not None


def rename(conn: sqlite3.Connection, group_id: int, name: str) -> None:
    conn.execute("UPDATE groups SET name = ? WHERE id = ?", (name, group_id))


def list_for_user(conn: sqlite3.Connection, user_id: int) -> list[sqlite3.Row]:
    """The groups of a user, by name without case. The row has the member id of the user."""
    return conn.execute(
        """
        SELECT g.id, g.name, g.currency, me.id AS member_id,
               (SELECT COUNT(*) FROM members WHERE group_id = g.id) AS member_count,
               (SELECT COUNT(*) FROM expenses WHERE group_id = g.id)
             + (SELECT COUNT(*) FROM payments WHERE group_id = g.id) AS transaction_count
        FROM groups g JOIN members me ON me.group_id = g.id AND me.user_id = ?
        ORDER BY g.name COLLATE NOCASE, g.id
        """,
        (user_id,),
    ).fetchall()


def count_groups(conn: sqlite3.Connection, user_id: int) -> int:
    row = conn.execute("SELECT COUNT(*) AS n FROM members WHERE user_id = ?", (user_id,)).fetchone()
    return int(row["n"])
