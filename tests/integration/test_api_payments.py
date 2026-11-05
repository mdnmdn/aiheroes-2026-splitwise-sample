from fastapi.testclient import TestClient

from app.balances.service import group_balances
from app.core import clock


def _setup(make_user, make_group, join_group):
    alice, bob = make_user("Alice"), make_user("Bob")
    group = make_group(alice)
    return alice, bob, group, join_group(group, bob)


def _body(sender: int, receiver: int, **extra) -> dict:
    data = {
        "sender_id": sender,
        "receiver_id": receiver,
        "amount": 3000,
        "payment_date": clock.today_iso(),
        "note": "cash",
    }
    return {**data, **extra}


def test_create_payment_minor_units(
    client: TestClient, tmp_db, make_user, make_group, join_group, auth
) -> None:
    alice, bob, group, b = _setup(make_user, make_group, join_group)
    url = f"/api/v1/groups/{group.id}/payments"
    response = client.post(url, json=_body(b, 1), headers=auth(bob))
    assert response.status_code == 201
    data = response.json()
    assert data["amount"] == 3000 and data["currency"] == "EUR" and data["note"] == "cash"
    assert (data["sender_id"], data["receiver_id"]) == (b, 1)
    assert group_balances(tmp_db, group.id) == {b: 3000, 1: -3000}


def test_list_update_delete(client: TestClient, make_user, make_group, join_group, auth) -> None:
    alice, bob, group, b = _setup(make_user, make_group, join_group)
    url = f"/api/v1/groups/{group.id}/payments"
    created = client.post(url, json=_body(b, 1), headers=auth(bob)).json()
    assert client.get(url, headers=auth(alice)).json() == [created]
    one = f"{url}/{created['id']}"
    updated = client.put(one, json=_body(1, b, amount=500, note=""), headers=auth(alice))
    assert updated.status_code == 200
    assert updated.json()["amount"] == 500 and updated.json()["sender_id"] == 1
    gone = client.delete(one, headers=auth(alice))
    assert gone.status_code == 204 and gone.content == b""
    assert client.get(url, headers=auth(alice)).json() == []
    assert client.delete(one, headers=auth(alice)).status_code == 404
    assert client.put(one, json=_body(1, b), headers=auth(alice)).status_code == 404


def test_422_fields(client: TestClient, make_user, make_group, join_group, auth) -> None:
    alice, bob, group, b = _setup(make_user, make_group, join_group)
    url = f"/api/v1/groups/{group.id}/payments"
    same = client.post(url, json=_body(1, 1), headers=auth(alice))
    assert same.status_code == 422 and "receiver_id" in same.json()["error"]["fields"]
    bad = client.post(
        url,
        json=_body(999, 888, amount=0, payment_date="2999-01-01", note="x" * 500),
        headers=auth(alice),
    )
    assert set(bad.json()["error"]["fields"]) == {
        "sender_id",
        "receiver_id",
        "amount",
        "payment_date",
        "note",
    }
    for value in ("30.00", 30.5, None):
        response = client.post(url, json=_body(1, b, amount=value), headers=auth(alice))
        assert response.status_code == 422
        assert "amount" in response.json()["error"]["fields"]


def test_404_non_member_other_group_bad_id(
    client: TestClient, make_user, make_group, join_group, auth
) -> None:
    alice, bob, group, b = _setup(make_user, make_group, join_group)
    outsider = make_user("Zed")
    other = make_group(outsider, "Other")
    url = f"/api/v1/groups/{group.id}/payments"
    created = client.post(url, json=_body(b, 1), headers=auth(bob)).json()
    assert client.get(url, headers=auth(outsider)).status_code == 404
    assert client.post(url, json=_body(b, 1), headers=auth(outsider)).status_code == 404
    foreign = f"/api/v1/groups/{other.id}/payments/{created['id']}"
    assert client.delete(foreign, headers=auth(outsider)).status_code == 404
    assert client.put(foreign, json=_body(1, 1), headers=auth(outsider)).status_code == 404
    assert client.get("/api/v1/groups/abc/payments", headers=auth(alice)).status_code == 404
    assert client.get("/api/v1/groups/9999/payments", headers=auth(alice)).status_code == 404
    assert client.delete(f"{url}/abc", headers=auth(alice)).status_code == 404
    assert client.delete(f"{url}/9999", headers=auth(alice)).status_code == 404


def test_payments_need_auth(client: TestClient) -> None:
    url = "/api/v1/groups/1/payments"
    assert client.get(url).status_code == 401
    assert client.post(url, json=_body(1, 2)).status_code == 401
    assert client.put(f"{url}/1", json=_body(1, 2)).status_code == 401
    assert client.delete(f"{url}/1").status_code == 401
