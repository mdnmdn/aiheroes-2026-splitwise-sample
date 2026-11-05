"""The three acceptance examples of _docs/product/overview.md, through the routes."""

import sqlite3

from fastapi.testclient import TestClient

from app.balances.service import group_balances
from app.core import clock

HX = {"HX-Request": "true"}


def test_acceptance_examples(
    client: TestClient, tmp_db: sqlite3.Connection, make_user, make_group, join_group, auth
) -> None:
    alice, bob, carla = make_user("Alice"), make_user("Bob"), make_user("Carla")
    group = make_group(alice)
    b, c = join_group(group, bob), join_group(group, carla)
    a = tmp_db.execute("SELECT id FROM members WHERE user_id = ?", (alice.id,)).fetchone()["id"]
    base = f"/groups/{group.id}"

    def check(expected: dict[int, int]) -> None:
        balances = group_balances(tmp_db, group.id)
        assert balances == expected
        assert sum(balances.values()) == 0

    # 1. Alice pays 90.00 for the three members.
    body = {
        "description": "Dinner",
        "amount": "90.00",
        "expense_date": clock.today_iso(),
        "payer_id": str(a),
        "p": [str(a), str(b), str(c)],
    }
    created = client.post(f"{base}/expenses", data=body, headers={**auth(alice), **HX})
    assert created.status_code == 200
    check({a: 6000, b: -3000, c: -3000})

    # 2. Bob pays 30.00 to Alice.
    payment = {
        "sender_id": str(b),
        "receiver_id": str(a),
        "amount": "30.00",
        "payment_date": clock.today_iso(),
        "note": "",
    }
    paid = client.post(f"{base}/payments", data=payment, headers={**auth(bob), **HX})
    assert paid.status_code == 200
    check({a: 3000, b: 0, c: -3000})

    # 3. Alice deletes the first expense. The payment stays.
    expense_id = tmp_db.execute("SELECT id FROM expenses").fetchone()["id"]
    deleted = client.post(f"{base}/expenses/{expense_id}/delete", headers={**auth(alice), **HX})
    assert deleted.status_code == 200
    check({a: -3000, b: 3000, c: 0})


def test_sum_is_zero_after_every_mutation(
    client: TestClient, tmp_db: sqlite3.Connection, make_user, make_group, join_group, auth
) -> None:
    alice, bob, carla = make_user("Alice"), make_user("Bob"), make_user("Carla")
    group = make_group(alice)
    b, c = join_group(group, bob), join_group(group, carla)
    a = tmp_db.execute("SELECT id FROM members WHERE user_id = ?", (alice.id,)).fetchone()["id"]
    url = f"/groups/{group.id}/expenses"
    headers = {**auth(bob), **HX}

    def form(amount: str, parts: list[int], payer: int) -> dict:
        return {
            "description": "Item",
            "amount": amount,
            "expense_date": clock.today_iso(),
            "payer_id": str(payer),
            "p": [str(p) for p in parts],
        }

    steps = [
        ("10.00", [a, b, c], a),
        ("0.01", [a, b, c], c),
        ("7.77", [b, c], a),
        ("1234.56", [a, c], b),
    ]
    for amount, parts, payer in steps:
        assert client.post(url, data=form(amount, parts, payer), headers=headers).status_code == 200
        assert sum(group_balances(tmp_db, group.id).values()) == 0
    ids = [r["id"] for r in tmp_db.execute("SELECT id FROM expenses ORDER BY id")]
    edited = client.post(f"{url}/{ids[0]}", data=form("33.33", [a, c], b), headers=headers)
    assert edited.status_code == 200
    assert sum(group_balances(tmp_db, group.id).values()) == 0
    for expense_id in ids:
        assert client.post(f"{url}/{expense_id}/delete", headers=headers).status_code == 200
        assert sum(group_balances(tmp_db, group.id).values()) == 0
    assert group_balances(tmp_db, group.id) == {a: 0, b: 0, c: 0}
