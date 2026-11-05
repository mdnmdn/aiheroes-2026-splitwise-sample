"""Balances card and member detail, through the routes."""

import json
import sqlite3

import pytest
from fastapi.testclient import TestClient

from app.balances.service import group_balances
from app.core import clock

HX = {"HX-Request": "true"}
MINUS = "−"


def _events(response) -> dict:
    return json.loads(response.headers["HX-Trigger"])


@pytest.fixture
def trio(tmp_db: sqlite3.Connection, make_user, make_group, join_group, add_expense):
    alice, bob, carla = make_user("Alice"), make_user("Bob"), make_user("Carla")
    group = make_group(alice)
    a = tmp_db.execute("SELECT id FROM members WHERE user_id = ?", (alice.id,)).fetchone()["id"]
    b, c = join_group(group, bob), join_group(group, carla)
    return alice, bob, carla, group, a, b, c


def _card(client, group, user, auth) -> str:
    return client.get(f"/groups/{group.id}/members", headers={**auth(user), **HX}).text


def test_card_states(client: TestClient, trio, add_expense, add_payment, auth) -> None:
    alice, bob, _, group, a, b, c = trio
    empty = _card(client, group, alice, auth)
    assert "Add a payment to see who owes whom." in empty
    assert "Total of the expenses" in empty and "0.00 EUR" in empty
    assert "All settled up" not in empty
    add_expense(group, a, [a, b, c], 9000)
    owed = _card(client, group, alice, auth)
    assert "90.00 EUR" in owed and "+60.00 EUR" in owed and f"{MINUS}30.00 EUR" in owed
    assert "Your balance · is owed" in owed and "is owed" in owed and "owes" in owed
    assert "Settle up" not in owed and "All settled up" not in owed
    assert 'id="members-region"' in owed and "ledger-changed from:body" in owed
    assert "Your balance · owes" in _card(client, group, bob, auth)
    add_payment(group, b, a, 3000)
    add_payment(group, c, a, 3000)
    settled = _card(client, group, alice, auth)
    assert "All settled up" in settled and "Settle up" not in settled
    assert "Your balance · settled" in settled and "0.00 EUR" in settled


def test_group_page_holds_the_card(client: TestClient, trio, add_expense, auth) -> None:
    alice, _, _, group, a, b, c = trio
    add_expense(group, a, [a, b, c], 9000)
    page = client.get(f"/groups/{group.id}", headers=auth(alice)).text
    assert "Total of the expenses" in page and "Settle up" not in page


def test_member_detail_breakdown(client: TestClient, trio, add_expense, add_payment, auth) -> None:
    alice, bob, _, group, a, b, c = trio
    add_expense(group, a, [a, b, c], 9000)
    add_payment(group, b, a, 3000)
    url = f"/groups/{group.id}/members/{a}"
    text = client.get(url, headers={**auth(alice), **HX}).text
    assert "Alice is owed" in text and "+30.00 EUR" in text
    assert "Paid minus share for each expense, plus payments sent, minus payments received." in text
    assert "Paid 90.00 EUR · share 30.00 EUR" in text and "+60.00 EUR" in text
    assert "Received from Bob" in text and f"{MINUS}30.00 EUR" in text
    assert "total-line" in text and "Balance" in text
    assert "Leave group" in text and "Members with transactions" in text
    bob_text = client.get(f"/groups/{group.id}/members/{b}", headers={**auth(alice), **HX}).text
    assert "Paid Alice" in bob_text and "Payment · sent" in bob_text


def test_member_detail_without_lines(client: TestClient, trio, auth) -> None:
    alice, _, _, group, a, b, c = trio
    text = client.get(f"/groups/{group.id}/members/{c}", headers={**auth(alice), **HX}).text
    assert "Carla is not part of any transaction in this group yet." in text
    assert "Settled" in text and "Remove from group" in text


@pytest.mark.parametrize("member", ["0", "abc", "999", "99999999999999999999"])
def test_member_detail_bad_ids(client: TestClient, trio, auth, member: str) -> None:
    alice, _, _, group, *_ = trio
    response = client.get(f"/groups/{group.id}/members/{member}", headers={**auth(alice), **HX})
    assert response.status_code == 404


def test_acceptance_balances(client: TestClient, tmp_db: sqlite3.Connection, trio, auth) -> None:
    alice, bob, carla, group, a, b, c = trio
    base = f"/groups/{group.id}"
    expense = {
        "description": "Dinner",
        "amount": "90.00",
        "expense_date": clock.today_iso(),
        "payer_id": str(a),
        "p": [str(a), str(b), str(c)],
    }
    assert client.post(f"{base}/expenses", data=expense, headers={**auth(alice), **HX}).is_success
    card = _card(client, group, alice, auth)
    assert "+60.00 EUR" in card and card.count(f"{MINUS}30.00 EUR") == 2
    payment = {
        "sender_id": str(b),
        "receiver_id": str(a),
        "amount": "30.00",
        "payment_date": clock.today_iso(),
        "note": "",
    }
    assert client.post(f"{base}/payments", data=payment, headers={**auth(bob), **HX}).is_success
    assert group_balances(tmp_db, group.id) == {a: 3000, b: 0, c: -3000}
    assert "All settled up" not in _card(client, group, alice, auth)
    expense_id = tmp_db.execute("SELECT id FROM expenses").fetchone()["id"]
    assert client.post(
        f"{base}/expenses/{expense_id}/delete", headers={**auth(alice), **HX}
    ).is_success
    assert group_balances(tmp_db, group.id) == {a: -3000, b: 3000, c: 0}
    # Alice pays Bob, then every balance is zero.
    payment = {**payment, "sender_id": str(a), "receiver_id": str(b)}
    assert client.post(f"{base}/payments", data=payment, headers={**auth(carla), **HX}).is_success
    assert group_balances(tmp_db, group.id) == {a: 0, b: 0, c: 0}
    assert "All settled up" in _card(client, group, alice, auth)


def test_member_names_are_escaped_in_dialogs(
    client: TestClient, tmp_db, make_user, make_group, join_group, add_expense, auth
) -> None:
    alice, evil = make_user("Alice"), make_user("<script>x</script>")
    group = make_group(alice)
    a = tmp_db.execute("SELECT id FROM members WHERE user_id = ?", (alice.id,)).fetchone()["id"]
    e = join_group(group, evil)
    add_expense(group, a, [a, e], 1000)
    for path in (f"/groups/{group.id}/members/{e}",):
        text = client.get(path, headers={**auth(alice), **HX}).text
        assert "<script>x</script>" not in text
        assert "&lt;script&gt;x&lt;/script&gt;" in text
    detail = client.get(f"/groups/{group.id}/members/{e}", headers={**auth(alice), **HX}).text
    assert 'aria-describedby="detNote"' in detail and 'id="detNote"' in detail
