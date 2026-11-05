"""SQL of the expenses feature: the tables expenses and expense_shares."""

import sqlite3

from app.expenses.schemas import Expense


def _expense(conn: sqlite3.Connection, row: sqlite3.Row) -> Expense:
    shares = conn.execute(
        "SELECT member_id, share FROM expense_shares WHERE expense_id = ? ORDER BY member_id",
        (row["id"],),
    )
    return Expense(
        id=row["id"],
        group_id=row["group_id"],
        description=row["description"],
        amount=row["amount"],
        expense_date=row["expense_date"],
        payer_id=row["payer_id"],
        shares={r["member_id"]: r["share"] for r in shares},
    )


def find(conn: sqlite3.Connection, group_id: int, expense_id: int) -> Expense | None:
    row = conn.execute(
        "SELECT id, group_id, description, amount, expense_date, payer_id FROM expenses"
        " WHERE group_id = ? AND id = ?",
        (group_id, expense_id),
    ).fetchone()
    return _expense(conn, row) if row else None


def insert(
    conn: sqlite3.Connection,
    group_id: int,
    description: str,
    amount: int,
    expense_date: str,
    payer_id: int,
    now: str,
) -> int:
    cursor = conn.execute(
        "INSERT INTO expenses (group_id, description, amount, expense_date, payer_id,"
        " created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (group_id, description, amount, expense_date, payer_id, now, now),
    )
    return int(cursor.lastrowid or 0)


def update(
    conn: sqlite3.Connection,
    expense_id: int,
    description: str,
    amount: int,
    expense_date: str,
    payer_id: int,
    now: str,
) -> None:
    """Keeps id and created_at."""
    conn.execute(
        "UPDATE expenses SET description = ?, amount = ?, expense_date = ?, payer_id = ?,"
        " updated_at = ? WHERE id = ?",
        (description, amount, expense_date, payer_id, now, expense_id),
    )


def replace_shares(conn: sqlite3.Connection, expense_id: int, shares: dict[int, int]) -> None:
    conn.execute("DELETE FROM expense_shares WHERE expense_id = ?", (expense_id,))
    conn.executemany(
        "INSERT INTO expense_shares (expense_id, member_id, share) VALUES (?, ?, ?)",
        [(expense_id, member_id, share) for member_id, share in shares.items()],
    )


def share_sum(conn: sqlite3.Connection, expense_id: int) -> int:
    row = conn.execute(
        "SELECT COALESCE(SUM(share), 0) AS total FROM expense_shares WHERE expense_id = ?",
        (expense_id,),
    ).fetchone()
    return int(row["total"])


def delete(conn: sqlite3.Connection, expense_id: int) -> None:
    """The shares go with it (ON DELETE CASCADE)."""
    conn.execute("DELETE FROM expenses WHERE id = ?", (expense_id,))


def list_for_group(conn: sqlite3.Connection, group_id: int) -> list[Expense]:
    """The expenses of a group, newest date first."""
    rows = conn.execute(
        "SELECT id, group_id, description, amount, expense_date, payer_id FROM expenses"
        " WHERE group_id = ? ORDER BY expense_date DESC, id DESC",
        (group_id,),
    ).fetchall()
    return [_expense(conn, r) for r in rows]
