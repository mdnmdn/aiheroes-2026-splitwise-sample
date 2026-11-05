from fastapi.testclient import TestClient

from app.core import clock


def _setup(make_user, make_group, join_group):
    alice, bob, carla = make_user("Alice"), make_user("Bob"), make_user("Carla")
    group = make_group(alice)
    return alice, bob, carla, group, join_group(group, bob), join_group(group, carla)


def _expense(client: TestClient, group, headers: dict, payer: int, members: list[int]) -> None:
    """Alice pays 90.00 EUR for the given members (the acceptance example of the overview)."""
    body = {
        "description": "Dinner",
        "amount": 9000,
        "expense_date": clock.today_iso(),
        "payer_id": payer,
        "participant_ids": members,
    }
    response = client.post(f"/api/v1/groups/{group.id}/expenses", json=body, headers=headers)
    assert response.status_code == 201


def test_balances_minor_units(client: TestClient, make_user, make_group, join_group, auth):
    alice, bob, carla, group, b, c = _setup(make_user, make_group, join_group)
    _expense(client, group, auth(alice), 1, [1, b, c])
    url = f"/api/v1/groups/{group.id}/balances"
    response = client.get(url, headers=auth(alice))
    assert response.status_code == 200
    assert response.json() == [
        {"member_id": 1, "balance": 6000, "currency": "EUR"},
        {"member_id": b, "balance": -3000, "currency": "EUR"},
        {"member_id": c, "balance": -3000, "currency": "EUR"},
    ]
    assert all(isinstance(row["balance"], int) for row in response.json())


def test_balances_sum_to_zero(client: TestClient, make_user, make_group, join_group, auth):
    alice, bob, carla, group, b, c = _setup(make_user, make_group, join_group)
    _expense(client, group, auth(alice), 1, [1, b, c])
    url = f"/api/v1/groups/{group.id}/balances"
    rows = client.get(url, headers=auth(bob)).json()
    assert sum(row["balance"] for row in rows) == 0


def test_transactions_expense_and_payment(
    client: TestClient, make_user, make_group, join_group, auth
) -> None:
    alice, bob, carla, group, b, c = _setup(make_user, make_group, join_group)
    _expense(client, group, auth(alice), 1, [1, b, c])
    payment = {
        "sender_id": b,
        "receiver_id": 1,
        "amount": 3000,
        "payment_date": clock.today_iso(),
        "note": "cash",
    }
    client.post(f"/api/v1/groups/{group.id}/payments", json=payment, headers=auth(bob))
    url = f"/api/v1/groups/{group.id}/transactions"
    response = client.get(url, headers=auth(carla))
    assert response.status_code == 200
    rows = response.json()
    assert sorted(row["kind"] for row in rows) == ["expense", "payment"]
    assert sorted(row["amount"] for row in rows) == [3000, 9000]
    assert all(row["currency"] == "EUR" for row in rows)
    expense = next(row for row in rows if row["kind"] == "expense")
    assert expense["title"] == "Dinner" and expense["meta"] == "Alice paid · for everyone (3)"


def test_balances_need_auth(client: TestClient) -> None:
    for path in ("balances", "transactions"):
        assert client.get(f"/api/v1/groups/1/{path}").status_code == 401


def test_404_non_member_and_bad_id(
    client: TestClient, make_user, make_group, join_group, auth
) -> None:
    alice, bob, carla, group, b, c = _setup(make_user, make_group, join_group)
    _expense(client, group, auth(alice), 1, [1, b, c])
    outsider = make_user("Zed")
    for path in ("balances", "transactions"):
        url = f"/api/v1/groups/{group.id}/{path}"
        assert client.get(url, headers=auth(outsider)).status_code == 404
        assert client.get(f"/api/v1/groups/9999/{path}", headers=auth(alice)).status_code == 404
        assert client.get(f"/api/v1/groups/abc/{path}", headers=auth(alice)).status_code == 404
