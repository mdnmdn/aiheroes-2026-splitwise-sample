import sqlite3

from app.balances.service import transaction_list
from app.members import repo as members_repo


def _setup(tmp_db: sqlite3.Connection, make_user, make_group, join_group):
    alice, bob, carla = make_user("Alice"), make_user("Bob"), make_user("Carla")
    group = make_group(alice)
    a = members_repo.find_by_user(tmp_db, group.id, alice.id).id  # type: ignore[union-attr]
    return group, a, join_group(group, bob), join_group(group, carla)


def _date(conn: sqlite3.Connection, table: str, row_id: int, column: str, value: str) -> None:
    conn.execute(f"UPDATE {table} SET {column} = ? WHERE id = ?", (value, row_id))  # noqa: S608


def test_days_newest_first_and_entry_time_inside_a_day(
    tmp_db, make_user, make_group, join_group, add_expense, add_payment
) -> None:
    group, a, b, c = _setup(tmp_db, make_user, make_group, join_group)
    old = add_expense(group, a, [a, b, c], 900)
    first = add_expense(group, a, [a, b, c], 900)
    second = add_expense(group, a, [a, b, c], 900)
    pay = add_payment(group, b, a, 300)
    _date(tmp_db, "expenses", old, "expense_date", "2026-10-01")
    for row_id in (first, second):  # same date and same entry time: the higher id first
        _date(tmp_db, "expenses", row_id, "created_at", "2026-11-05T10:00:00Z")
    _date(tmp_db, "payments", pay, "created_at", "2026-11-05T11:00:00Z")
    tx = transaction_list(tmp_db, group.id, a)
    assert [d.date for d in tx.days] == ["2026-11-05", "2026-10-01"]
    assert [(r.kind, r.id) for r in tx.days[0].rows] == [
        ("payment", pay),
        ("expense", second),
        ("expense", first),
    ]
    assert (tx.shown, tx.total) == (4, 4)


def test_row_texts(tmp_db, make_user, make_group, join_group, add_expense, add_payment) -> None:
    group, a, b, c = _setup(tmp_db, make_user, make_group, join_group)
    add_expense(group, b, [a, b, c], 900)
    add_expense(group, b, [c, a], 900)
    add_payment(group, b, a, 300)
    tmp_db.execute("UPDATE payments SET note = 'Cash'")
    rows = [r for d in transaction_list(tmp_db, group.id, a).days for r in d.rows]
    assert [r.meta for r in rows if r.title == "Bob → Alice"] == ["Cash"]
    metas = sorted(r.meta for r in rows if r.kind == "expense")
    assert metas == ["Bob paid · for Alice, Carla", "Bob paid · for everyone (3)"]


def test_mine_filter(tmp_db, make_user, make_group, join_group, add_expense, add_payment) -> None:
    group, a, b, c = _setup(tmp_db, make_user, make_group, join_group)
    add_expense(group, b, [b, c], 900)  # not Alice
    paid = add_expense(group, a, [b, c], 900)  # payer, not a participant
    shared = add_expense(group, b, [a, b], 900)  # participant
    add_payment(group, b, c, 100)  # not Alice
    got = add_payment(group, c, a, 100)  # receiver
    tx = transaction_list(tmp_db, group.id, a, "mine")
    ids = {(r.kind, r.id) for d in tx.days for r in d.rows}
    assert ids == {("expense", paid), ("expense", shared), ("payment", got)}
    assert (tx.shown, tx.total, tx.filter) == (3, 5, "mine")
    assert transaction_list(tmp_db, group.id, a, "bogus").filter == "all"


def test_empty_list(tmp_db, make_user, make_group, join_group) -> None:
    group, a, *_ = _setup(tmp_db, make_user, make_group, join_group)
    tx = transaction_list(tmp_db, group.id, a)
    assert (tx.days, tx.shown, tx.total) == ([], 0, 0)
