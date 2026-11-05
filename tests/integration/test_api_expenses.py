from fastapi.testclient import TestClient

from app.core import clock


def _setup(make_user, make_group, join_group):
    alice, bob = make_user("Alice"), make_user("Bob")
    group = make_group(alice)
    return alice, bob, group, join_group(group, bob)


def _body(payer: int, participants: list[int], **extra) -> dict:
    data = {
        "description": "Dinner",
        "amount": 1001,
        "expense_date": clock.today_iso(),
        "payer_id": payer,
        "participant_ids": participants,
    }
    return {**data, **extra}


def test_create_expense_minor_units(client: TestClient, make_user, make_group, join_group, auth):
    alice, bob, group, b = _setup(make_user, make_group, join_group)
    url = f"/api/v1/groups/{group.id}/expenses"
    response = client.post(url, json=_body(1, [1, b]), headers=auth(alice))
    assert response.status_code == 201
    data = response.json()
    assert data["amount"] == 1001 and data["currency"] == "EUR"
    assert data["payer_id"] == 1 and data["group_id"] == group.id
    assert data["shares"] == [{"member_id": 1, "amount": 501}, {"member_id": b, "amount": 500}]
    assert isinstance(data["amount"], int)


def test_zero_decimal_currency_is_minor_units(
    client: TestClient, make_user, make_group, auth
) -> None:
    alice = make_user("Alice")
    group = make_group(alice, "Tokyo", "JPY")
    response = client.post(
        f"/api/v1/groups/{group.id}/expenses", json=_body(1, [1], amount=1500), headers=auth(alice)
    )
    assert response.status_code == 201
    assert response.json()["amount"] == 1500 and response.json()["currency"] == "JPY"


def test_list_get_update_delete(client: TestClient, make_user, make_group, join_group, auth):
    alice, bob, group, b = _setup(make_user, make_group, join_group)
    url = f"/api/v1/groups/{group.id}/expenses"
    created = client.post(url, json=_body(1, [1, b]), headers=auth(alice)).json()
    listed = client.get(url, headers=auth(bob)).json()
    assert listed == [created]
    one = f"{url}/{created['id']}"
    body = _body(b, [b], amount=2000, description="Taxi")
    updated = client.put(one, json=body, headers=auth(bob))
    assert updated.status_code == 200
    assert updated.json()["amount"] == 2000 and updated.json()["payer_id"] == b
    assert updated.json()["shares"] == [{"member_id": b, "amount": 2000}]
    gone = client.delete(one, headers=auth(alice))
    assert gone.status_code == 204 and gone.content == b""
    assert client.get(url, headers=auth(alice)).json() == []
    assert client.delete(one, headers=auth(alice)).status_code == 404
    assert client.put(one, json=_body(1, [1]), headers=auth(alice)).status_code == 404


def test_422_fields(client: TestClient, make_user, make_group, join_group, auth) -> None:
    alice, bob, group, b = _setup(make_user, make_group, join_group)
    url = f"/api/v1/groups/{group.id}/expenses"
    bad = _body(999, [], amount=0, description=" ", expense_date="2999-01-01")
    response = client.post(url, json=bad, headers=auth(alice))
    assert response.status_code == 422
    error = response.json()["error"]
    assert error["code"] == "validation_failed"
    assert set(error["fields"]) == {
        "description",
        "amount",
        "expense_date",
        "payer_id",
        "participant_ids",
    }
    foreign = client.post(url, json=_body(1, [1, 999]), headers=auth(alice))
    assert "participant_ids" in foreign.json()["error"]["fields"]


def test_amount_must_be_integer(client: TestClient, make_user, make_group, auth) -> None:
    alice = make_user("Alice")
    group = make_group(alice)
    url = f"/api/v1/groups/{group.id}/expenses"
    for value in ("12.50", 12.5, True, None):
        response = client.post(url, json=_body(1, [1], amount=value), headers=auth(alice))
        assert response.status_code == 422, value
        assert "amount" in response.json()["error"]["fields"]
    assert "amount" in client.post(url, json={}, headers=auth(alice)).json()["error"]["fields"]
    assert client.post(url, json=_body(1, [1], amount=-5), headers=auth(alice)).status_code == 422


def test_404_non_member_other_group_bad_id(
    client: TestClient, make_user, make_group, join_group, auth
) -> None:
    alice, bob, group, b = _setup(make_user, make_group, join_group)
    outsider = make_user("Zed")
    other = make_group(outsider, "Other")
    created = client.post(
        f"/api/v1/groups/{group.id}/expenses", json=_body(1, [1]), headers=auth(alice)
    ).json()
    url = f"/api/v1/groups/{group.id}/expenses"
    assert client.get(url, headers=auth(outsider)).status_code == 404
    assert client.post(url, json=_body(1, [1]), headers=auth(outsider)).status_code == 404
    assert client.delete(f"{url}/{created['id']}", headers=auth(outsider)).status_code == 404
    # the expense exists, but not in this group
    foreign = f"/api/v1/groups/{other.id}/expenses/{created['id']}"
    assert client.delete(foreign, headers=auth(outsider)).status_code == 404
    assert client.put(foreign, json=_body(1, [1]), headers=auth(outsider)).status_code == 404
    for path in ("/api/v1/groups/abc/expenses", "/api/v1/groups/9999/expenses", f"{url}/abc"):
        assert client.get(path, headers=auth(alice)).status_code in (404, 405)
    assert client.delete(f"{url}/abc", headers=auth(alice)).status_code == 404
    assert client.delete("/api/v1/groups/9999/expenses/1", headers=auth(alice)).status_code == 404


def test_expenses_need_auth(client: TestClient) -> None:
    url = "/api/v1/groups/1/expenses"
    assert client.get(url).status_code == 401
    assert client.post(url, json=_body(1, [1])).status_code == 401
    assert client.put(f"{url}/1", json=_body(1, [1])).status_code == 401
    assert client.delete(f"{url}/1").status_code == 401


def test_malformed_json_and_strict_ids(client: TestClient, make_user, make_group, auth) -> None:
    alice = make_user("Alice")
    group = make_group(alice)
    url = f"/api/v1/groups/{group.id}/expenses"
    headers = {**auth(alice), "Content-Type": "application/json"}
    broken = client.post(url, content="{not json", headers=headers)
    assert broken.status_code == 422
    assert list(broken.json()["error"]["fields"]) == ["body"]
    for value in ("1", 1.5, True):
        response = client.post(url, json=_body(value, [1]), headers=auth(alice))
        assert response.status_code == 422
        assert "payer_id" in response.json()["error"]["fields"]
    response = client.post(url, json=_body(1, ["1"]), headers=auth(alice))
    assert response.status_code == 422
    assert "participant_ids" in response.json()["error"]["fields"]
