from fastapi.testclient import TestClient


def test_create_and_get_group(client: TestClient, sign_in) -> None:
    alice = sign_in("Alice")
    body = {"name": "Trip", "currency": "EUR"}
    response = client.post("/api/v1/groups", json=body, headers=alice)
    assert response.status_code == 201
    group = response.json()
    assert group["name"] == "Trip" and group["currency"] == "EUR"
    assert group["invite_code"].startswith("TRI-")
    got = client.get(f"/api/v1/groups/{group['id']}", headers=alice)
    assert got.status_code == 200 and got.json() == group


def test_create_group_422_fields(client: TestClient, sign_in) -> None:
    alice = sign_in("Alice")
    response = client.post("/api/v1/groups", json={"name": " ", "currency": "XXX"}, headers=alice)
    assert response.status_code == 422
    assert "name" in response.json()["error"]["fields"]
    bad = client.post("/api/v1/groups", json={"name": "A", "currency": "XXX"}, headers=alice)
    assert "currency" in bad.json()["error"]["fields"]
    wrong_type = client.post("/api/v1/groups", json={"name": 5}, headers=alice)
    assert wrong_type.status_code == 422 and "name" in wrong_type.json()["error"]["fields"]


def test_list_groups_has_minor_unit_balance(
    client: TestClient, make_user, make_group, join_group, add_expense, auth
) -> None:
    alice, bob = make_user("Alice"), make_user("Bob")
    group = make_group(alice)
    b = join_group(group, bob)
    a = 1  # the member of Alice is the first one in a fresh database
    add_expense(group, a, [a, b], 1001)
    rows = client.get("/api/v1/groups", headers=auth(alice)).json()
    assert rows == [
        {
            "id": group.id,
            "name": "Lisbon trip",
            "currency": "EUR",
            "member_count": 2,
            "transaction_count": 1,
            "balance": 500,
        }
    ]
    assert client.get("/api/v1/groups?filter=owe", headers=auth(alice)).json() == []
    assert len(client.get("/api/v1/groups?filter=owed&q=lis", headers=auth(alice)).json()) == 1


def test_rename_group(client: TestClient, make_user, make_group, auth) -> None:
    alice = make_user("Alice")
    group = make_group(alice)
    url = f"/api/v1/groups/{group.id}"
    response = client.patch(url, json={"name": "Rome"}, headers=auth(alice))
    assert response.status_code == 200 and response.json()["name"] == "Rome"
    assert response.json()["invite_code"] == group.invite_code
    bad = client.patch(f"/api/v1/groups/{group.id}", json={"name": ""}, headers=auth(alice))
    assert bad.status_code == 422 and "name" in bad.json()["error"]["fields"]


def test_join_group(client: TestClient, make_user, make_group, auth) -> None:
    alice, bob = make_user("Alice"), make_user("Bob")
    group = make_group(alice)
    for _ in range(2):  # joining again is not an error
        response = client.post(
            "/api/v1/groups/join", json={"code": group.invite_code.lower()}, headers=auth(bob)
        )
        assert response.status_code == 200 and response.json()["id"] == group.id
    assert client.get(f"/api/v1/groups/{group.id}", headers=auth(bob)).status_code == 200
    bad = client.post("/api/v1/groups/join", json={"code": "NOPE-0000"}, headers=auth(bob))
    assert bad.status_code == 422 and "code" in bad.json()["error"]["fields"]


def test_group_404_non_member_unknown_and_bad_id(
    client: TestClient, make_user, make_group, auth
) -> None:
    alice, bob = make_user("Alice"), make_user("Bob")
    group = make_group(alice)
    for ident in (str(group.id), "9999", "abc", "0", "99999999999999999999"):
        headers = auth(bob) if ident == str(group.id) else auth(alice)
        for method in ("get", "patch"):
            kwargs = {"json": {"name": "x"}} if method == "patch" else {}
            response = getattr(client, method)(f"/api/v1/groups/{ident}", headers=headers, **kwargs)
            assert response.status_code == 404, (ident, method)
            assert response.json()["error"]["code"] == "not_found"


def test_groups_need_auth(client: TestClient) -> None:
    assert client.get("/api/v1/groups").status_code == 401
    assert client.post("/api/v1/groups", json={"name": "A"}).status_code == 401
    assert client.get("/api/v1/groups/1").status_code == 401
    assert client.patch("/api/v1/groups/1", json={"name": "A"}).status_code == 401
    assert client.post("/api/v1/groups/join", json={"code": "A"}).status_code == 401
