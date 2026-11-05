from fastapi.testclient import TestClient


def _setup(make_user, make_group, join_group):
    alice, bob = make_user("Alice"), make_user("Bob")
    group = make_group(alice)
    return alice, bob, group, join_group(group, bob)


def test_list_members_in_join_order(client: TestClient, make_user, make_group, join_group, auth):
    alice, bob, group, b = _setup(make_user, make_group, join_group)
    response = client.get(f"/api/v1/groups/{group.id}/members", headers=auth(alice))
    assert response.status_code == 200
    assert [(m["name"], m["user_id"]) for m in response.json()] == [
        ("Alice", alice.id),
        ("Bob", bob.id),
    ]
    assert response.json()[1]["id"] == b


def test_add_member_existing_and_new(client: TestClient, make_user, make_group, auth) -> None:
    alice, carol = make_user("Alice"), make_user("Carol")
    group = make_group(alice)
    url = f"/api/v1/groups/{group.id}/members"
    existing = client.post(url, json={"user_id": carol.id}, headers=auth(alice))
    assert existing.status_code == 201 and existing.json()["name"] == "Carol"
    new = client.post(url, json={"name": "Eve"}, headers=auth(alice))
    assert new.status_code == 201 and new.json()["name"] == "Eve"
    assert len(client.get(url, headers=auth(alice)).json()) == 3


def test_add_member_422(client: TestClient, make_user, make_group, auth) -> None:
    alice = make_user("Alice")
    make_user("Carol")
    group = make_group(alice)
    url = f"/api/v1/groups/{group.id}/members"
    assert "user_id" in client.post(url, json={}, headers=auth(alice)).json()["error"]["fields"]
    assert client.post(url, json={"user_id": alice.id}, headers=auth(alice)).status_code == 422
    assert client.post(url, json={"user_id": 999}, headers=auth(alice)).status_code == 422
    assert client.post(url, json={"name": "Carol"}, headers=auth(alice)).status_code == 422
    assert (
        "name" in client.post(url, json={"name": ""}, headers=auth(alice)).json()["error"]["fields"]
    )


def test_remove_member_204_then_404(client: TestClient, make_user, make_group, join_group, auth):
    alice, bob, group, b = _setup(make_user, make_group, join_group)
    url = f"/api/v1/groups/{group.id}/members/{b}"
    response = client.delete(url, headers=auth(alice))
    assert response.status_code == 204 and response.content == b""
    assert client.delete(url, headers=auth(alice)).status_code == 404


def test_remove_member_409(
    client: TestClient, make_user, make_group, join_group, add_expense, auth
) -> None:
    alice, bob, group, b = _setup(make_user, make_group, join_group)
    add_expense(group, 1, [1, b], 1000)
    response = client.delete(f"/api/v1/groups/{group.id}/members/{b}", headers=auth(alice))
    assert response.status_code == 409 and response.json()["error"]["code"] == "conflict"
    own = client.delete(f"/api/v1/groups/{group.id}/members/1", headers=auth(alice))
    assert own.status_code == 409


def test_members_404(client: TestClient, make_user, make_group, join_group, auth) -> None:
    alice, bob, group, b = _setup(make_user, make_group, join_group)
    outsider = make_user("Zed")
    other = make_group(make_user("Yan"), "Other")
    base = f"/api/v1/groups/{group.id}/members"
    assert client.get(base, headers=auth(outsider)).status_code == 404
    assert client.post(base, json={"name": "X"}, headers=auth(outsider)).status_code == 404
    assert client.get("/api/v1/groups/abc/members", headers=auth(alice)).status_code == 404
    assert client.get("/api/v1/groups/9999/members", headers=auth(alice)).status_code == 404
    # a member id of another group is not found
    foreign = f"/api/v1/groups/{other.id}/members/{b}"
    assert client.delete(foreign, headers=auth(alice)).status_code == 404
    mine = f"{base}/{b}"
    assert client.delete(mine, headers=auth(outsider)).status_code == 404
    assert client.patch(mine, json={"name": "x"}, headers=auth(alice)).status_code == 405
    assert client.delete(f"{base}/abc", headers=auth(alice)).status_code == 404
    assert client.delete(f"{base}/9999", headers=auth(alice)).status_code == 404


def test_members_need_auth(client: TestClient) -> None:
    assert client.get("/api/v1/groups/1/members").status_code == 401
    assert client.post("/api/v1/groups/1/members", json={"name": "x"}).status_code == 401
    assert client.delete("/api/v1/groups/1/members/1").status_code == 401


def test_add_member_user_id_wins_and_is_strict(
    client: TestClient, make_user, make_group, auth
) -> None:
    alice, carol = make_user("Alice"), make_user("Carol")
    group = make_group(alice)
    url = f"/api/v1/groups/{group.id}/members"
    both = client.post(url, json={"user_id": carol.id, "name": "Eve"}, headers=auth(alice))
    assert both.status_code == 201 and both.json()["name"] == "Carol"
    neither = client.post(url, json={}, headers=auth(alice))
    assert neither.status_code == 422
    assert set(neither.json()["error"]["fields"]) == {"user_id", "name"}
    for value in ("1", 1.5, True):
        bad = client.post(url, json={"user_id": value}, headers=auth(alice))
        assert bad.status_code == 422
        assert "user_id" in bad.json()["error"]["fields"]
