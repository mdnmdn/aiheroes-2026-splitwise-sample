"""SQL of the balances feature: the rows that feed compute_balances. Reads only."""

import sqlite3


def _marks(group_ids: list[int]) -> str:
    return ",".join("?" * len(group_ids))


def member_ids(conn: sqlite3.Connection, group_ids: list[int]) -> dict[int, list[int]]:
    """Group id to the member ids of the group, for each group in group_ids."""
    rows = conn.execute(
        f"SELECT group_id, id FROM members WHERE group_id IN ({_marks(group_ids)}) ORDER BY id",
        group_ids,
    )
    result: dict[int, list[int]] = {g: [] for g in group_ids}
    for r in rows:
        result[r["group_id"]].append(r["id"])
    return result


def expenses(conn: sqlite3.Connection, group_ids: list[int]) -> dict[int, list[tuple[int, int]]]:
    """Group id to the (payer_id, amount) of its expenses."""
    rows = conn.execute(
        f"SELECT group_id, payer_id, amount FROM expenses WHERE group_id IN ({_marks(group_ids)})",
        group_ids,
    )
    result: dict[int, list[tuple[int, int]]] = {g: [] for g in group_ids}
    for r in rows:
        result[r["group_id"]].append((r["payer_id"], r["amount"]))
    return result


def shares(conn: sqlite3.Connection, group_ids: list[int]) -> dict[int, list[tuple[int, int]]]:
    """Group id to the (member_id, share) of its expense shares."""
    rows = conn.execute(
        "SELECT e.group_id, s.member_id, s.share FROM expense_shares s"
        f" JOIN expenses e ON e.id = s.expense_id WHERE e.group_id IN ({_marks(group_ids)})",
        group_ids,
    )
    result: dict[int, list[tuple[int, int]]] = {g: [] for g in group_ids}
    for r in rows:
        result[r["group_id"]].append((r["member_id"], r["share"]))
    return result


def payments(
    conn: sqlite3.Connection, group_ids: list[int]
) -> dict[int, list[tuple[int, int, int]]]:
    """Group id to the (sender_id, receiver_id, amount) of its payments."""
    rows = conn.execute(
        "SELECT group_id, sender_id, receiver_id, amount FROM payments"
        f" WHERE group_id IN ({_marks(group_ids)})",
        group_ids,
    )
    result: dict[int, list[tuple[int, int, int]]] = {g: [] for g in group_ids}
    for r in rows:
        result[r["group_id"]].append((r["sender_id"], r["receiver_id"], r["amount"]))
    return result


def member_shares(conn: sqlite3.Connection, group_id: int, member_id: int) -> dict[int, int]:
    """Expense id to the share of the member, for each expense of the group that has one."""
    rows = conn.execute(
        "SELECT s.expense_id, s.share FROM expense_shares s"
        " JOIN expenses e ON e.id = s.expense_id WHERE e.group_id = ? AND s.member_id = ?",
        (group_id, member_id),
    )
    return {r["expense_id"]: r["share"] for r in rows}


def expense_rows(conn: sqlite3.Connection, group_id: int) -> list[sqlite3.Row]:
    return conn.execute(
        "SELECT id, description, amount, expense_date AS date, payer_id, created_at"
        " FROM expenses WHERE group_id = ?",
        (group_id,),
    ).fetchall()


def participants(conn: sqlite3.Connection, group_id: int) -> dict[int, list[int]]:
    """Expense id to the member ids of its participants."""
    rows = conn.execute(
        "SELECT s.expense_id, s.member_id FROM expense_shares s"
        " JOIN expenses e ON e.id = s.expense_id WHERE e.group_id = ? ORDER BY s.member_id",
        (group_id,),
    )
    result: dict[int, list[int]] = {}
    for r in rows:
        result.setdefault(r["expense_id"], []).append(r["member_id"])
    return result


def payment_rows(conn: sqlite3.Connection, group_id: int) -> list[sqlite3.Row]:
    return conn.execute(
        "SELECT id, amount, payment_date AS date, sender_id, receiver_id, note, created_at"
        " FROM payments WHERE group_id = ?",
        (group_id,),
    ).fetchall()
