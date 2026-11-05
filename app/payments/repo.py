"""SQL of the payments feature: the table payments."""

import sqlite3

from app.payments.schemas import Payment


def _payment(row: sqlite3.Row) -> Payment:
    return Payment(
        id=row["id"],
        group_id=row["group_id"],
        sender_id=row["sender_id"],
        receiver_id=row["receiver_id"],
        amount=row["amount"],
        payment_date=row["payment_date"],
        note=row["note"],
    )


def find(conn: sqlite3.Connection, group_id: int, payment_id: int) -> Payment | None:
    row = conn.execute(
        "SELECT id, group_id, sender_id, receiver_id, amount, payment_date, note FROM payments"
        " WHERE group_id = ? AND id = ?",
        (group_id, payment_id),
    ).fetchone()
    return _payment(row) if row else None


def insert(conn: sqlite3.Connection, group_id: int, values: tuple, now: str) -> int:
    """values: sender_id, receiver_id, amount, payment_date, note."""
    cursor = conn.execute(
        "INSERT INTO payments (group_id, sender_id, receiver_id, amount, payment_date, note,"
        " created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (group_id, *values, now, now),
    )
    return int(cursor.lastrowid or 0)


def update(conn: sqlite3.Connection, payment_id: int, values: tuple, now: str) -> None:
    """Keeps id and created_at."""
    conn.execute(
        "UPDATE payments SET sender_id = ?, receiver_id = ?, amount = ?, payment_date = ?,"
        " note = ?, updated_at = ? WHERE id = ?",
        (*values, now, payment_id),
    )


def delete(conn: sqlite3.Connection, payment_id: int) -> None:
    conn.execute("DELETE FROM payments WHERE id = ?", (payment_id,))


def list_for_group(conn: sqlite3.Connection, group_id: int) -> list[Payment]:
    """The payments of a group, newest date first."""
    rows = conn.execute(
        "SELECT id, group_id, sender_id, receiver_id, amount, payment_date, note FROM payments"
        " WHERE group_id = ? ORDER BY payment_date DESC, id DESC",
        (group_id,),
    ).fetchall()
    return [_payment(r) for r in rows]
