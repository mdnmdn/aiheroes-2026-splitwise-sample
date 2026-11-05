import json
import sqlite3

from fastapi.testclient import TestClient

from app.members import repo as members_repo

HX = {"HX-Request": "true"}


def _events(response) -> dict:
    return json.loads(response.headers["HX-Trigger"])


def test_home_signed_out_redirects_to_login(client: TestClient) -> None:
    response = client.get("/", follow_redirects=False)
    assert response.status_code == 303
    assert response.headers["location"].startswith("/login")


def test_home_empty_state(client: TestClient, make_user, auth) -> None:
    text = client.get("/", headers=auth(make_user("Alice"))).text
    assert "You are not in any group yet" in text
    assert 'id="group-list-region"' not in text
    assert "Join with a code" in text
    assert "Create group" in text


def test_home_lists_groups_with_balance(
    client: TestClient, make_user, make_group, join_group, add_expense, auth, tmp_db
) -> None:
    alice, bob = make_user("Alice"), make_user("Bob")
    group = make_group(alice, "Lisbon trip")
    a = members_repo.find_by_user(tmp_db, group.id, alice.id).id
    b = join_group(group, bob)
    add_expense(group, a, [a, b], 1200)
    text = client.get("/", headers=auth(alice)).text
    assert 'id="group-list-region"' in text
    assert f'href="/groups/{group.id}"' in text
    assert "2 members · 1 transaction · EUR" in text
    assert "+6.00 EUR" in text
    assert "is owed" in text
    assert "1 of 1 groups" in text
    bob_text = client.get("/", headers=auth(bob)).text
    assert "−6.00 EUR" in bob_text
    assert "owes" in bob_text


def test_list_fragment_search_and_filter(client: TestClient, make_user, make_group, auth) -> None:
    alice = make_user("Alice")
    make_group(alice, "Lisbon trip")
    make_group(alice, "Flat")
    response = client.get("/groups/list?q=LIS&filter=all", headers={**auth(alice), **HX})
    assert response.status_code == 200
    assert response.text.lstrip().startswith('<div class="od-stack"')
    assert 'id="group-list-region"' in response.text
    assert "Lisbon trip" in response.text
    assert "Flat" not in response.text
    assert "1 of 2 groups" in response.text
    owed = client.get("/groups/list?filter=owed", headers={**auth(alice), **HX}).text
    assert "No groups match" in owed
    assert "Try another name or show all groups." in owed
    assert "Clear filters" in owed
    assert "0 of 2 groups" in owed


def test_list_fragment_signed_out_and_not_htmx(client: TestClient, make_user, auth) -> None:
    signed_out = client.get("/groups/list", headers=HX, follow_redirects=False)
    assert signed_out.headers["HX-Redirect"].startswith("/login")
    plain = client.get("/groups/list", headers=auth(make_user("Alice")), follow_redirects=False)
    assert (plain.status_code, plain.headers["location"]) == (303, "/")


def test_new_dialog(client: TestClient, make_user, auth) -> None:
    alice = make_user("Alice")
    response = client.get("/groups/new", headers={**auth(alice), **HX})
    assert response.status_code == 200
    text = response.text
    assert '<dialog id="group-dialog"' in text
    assert "New group" in text
    assert '<option value="EUR" selected>EUR — €</option>' in text
    assert text.count("<option") == 15
    assert "Set once when the group is created." in text
    signed_out = client.get("/groups/new", headers=HX, follow_redirects=False)
    assert signed_out.headers["HX-Redirect"].startswith("/login")
    plain = client.get("/groups/new", headers=auth(alice), follow_redirects=False)
    assert plain.status_code == 303


def test_create_group_redirects_and_flashes(
    client: TestClient, make_user, auth, tmp_db: sqlite3.Connection
) -> None:
    alice = make_user("Alice")
    response = client.post(
        "/groups", data={"name": " Ski week ", "currency": "CHF"}, headers={**auth(alice), **HX}
    )
    row = tmp_db.execute("SELECT id, name, currency, invite_code FROM groups").fetchone()
    assert (row["name"], row["currency"]) == ("Ski week", "CHF")
    assert row["invite_code"].startswith("SKI-")
    assert json.loads(response.headers["HX-Location"])["path"] == f"/groups/{row['id']}"
    assert "sw_flash" in response.headers["set-cookie"]
    page = client.get(f"/groups/{row['id']}", headers=auth(alice))
    assert "Ski week created. Invite people with its code." in page.text


def test_create_group_without_htmx_is_a_303(client: TestClient, make_user, auth) -> None:
    response = client.post(
        "/groups", data={"name": "Trip", "currency": "EUR"}, headers=auth(make_user("A")),
        follow_redirects=False,
    )  # fmt: skip
    assert response.status_code == 303
    assert response.headers["location"].startswith("/groups/")


def test_create_group_422_keeps_input(client: TestClient, make_user, auth) -> None:
    alice = make_user("Alice")
    response = client.post(
        "/groups", data={"name": "", "currency": "USD"}, headers={**auth(alice), **HX}
    )
    assert response.status_code == 422
    assert "Give the group a name." in response.text
    assert '<option value="USD" selected>' in response.text
    assert "<dialog" not in response.text
    long = client.post("/groups", data={"name": "x" * 51, "currency": "EUR"}, headers=auth(alice))
    assert "Use at most 50 characters." in long.text


def test_create_group_signed_out(client: TestClient) -> None:
    response = client.post("/groups", data={"name": "Trip"}, follow_redirects=False)
    assert response.status_code == 303


def test_join_opens_the_group(
    client: TestClient, make_user, make_group, auth, tmp_db: sqlite3.Connection
) -> None:
    alice, bob = make_user("Alice"), make_user("Bob")
    group = make_group(alice)
    response = client.post(
        "/groups/join", data={"code": group.invite_code.lower()}, headers={**auth(bob), **HX}
    )
    assert json.loads(response.headers["HX-Location"])["path"] == f"/groups/{group.id}"
    page = client.get(f"/groups/{group.id}", headers=auth(bob))
    assert page.status_code == 200
    assert f"You joined {group.name}" in page.text
    assert len(members_repo.list_members(tmp_db, group.id)) == 2


def test_join_again_says_you_are_in(client: TestClient, make_user, make_group, auth) -> None:
    alice = make_user("Alice")
    group = make_group(alice)
    client.post("/groups/join", data={"code": group.invite_code}, headers={**auth(alice), **HX})
    page = client.get(f"/groups/{group.id}", headers=auth(alice))
    assert f"You are in {group.name}" in page.text


def test_join_422(client: TestClient, make_user, auth) -> None:
    headers = {**auth(make_user("Alice")), **HX}
    empty = client.post("/groups/join", data={"code": " "}, headers=headers)
    assert empty.status_code == 422
    assert "Enter an invite code." in empty.text
    assert 'id="join-region"' in empty.text
    unknown = client.post("/groups/join", data={"code": "nop-aaaa"}, headers=headers)
    assert unknown.status_code == 422
    assert "No group uses this code." in unknown.text
    assert 'value="nop-aaaa"' in unknown.text


def test_join_signed_out(client: TestClient) -> None:
    response = client.post("/groups/join", data={"code": "A"}, follow_redirects=False)
    assert response.status_code == 303


def test_group_page(client: TestClient, make_user, make_group, auth) -> None:
    alice = make_user("Alice")
    group = make_group(alice, "Lisbon trip", "GBP")
    text = client.get(f"/groups/{group.id}", headers=auth(alice)).text
    assert "<title>Lisbon trip — Splitwise</title>" in text
    assert 'class="layout"' in text
    assert 'id="members-region"' in text
    assert 'id="expenses-region"' in text
    assert "Lisbon trip" in text
    assert '<span class="chip od-fixed">GBP</span>' in text
    assert f'hx-get="/groups/{group.id}/settings"' in text
    assert "You</span>" in text
    assert "Add expense" in text


def test_group_page_not_a_member_redirects_home_with_a_message(
    client: TestClient, make_user, make_group, auth
) -> None:
    alice, bob = make_user("Alice"), make_user("Bob")
    group = make_group(alice)
    response = client.get(f"/groups/{group.id}", headers=auth(bob), follow_redirects=False)
    assert (response.status_code, response.headers["location"]) == (303, "/")
    home = client.get("/", headers=auth(bob))
    assert "That group is not available to you." in home.text
    missing = client.get("/groups/999", headers=auth(bob), follow_redirects=False)
    assert missing.status_code == 303


def test_group_page_signed_out(client: TestClient, make_user, make_group) -> None:
    group = make_group(make_user("Alice"))
    response = client.get(f"/groups/{group.id}", follow_redirects=False)
    assert response.status_code == 303
    assert response.headers["location"].startswith("/login?next=")


def test_settings_dialog(client: TestClient, make_user, make_group, auth) -> None:
    alice = make_user("Alice")
    group = make_group(alice, "Trip", "SEK")
    response = client.get(f"/groups/{group.id}/settings", headers={**auth(alice), **HX})
    assert response.status_code == 200
    assert "Group settings" in response.text
    assert 'value="Trip"' in response.text
    assert 'value="SEK — SEK" disabled' in response.text
    assert "The base currency cannot change after the group is created." in response.text


def test_settings_dialog_not_a_member_is_404(
    client: TestClient, make_user, make_group, auth
) -> None:
    group = make_group(make_user("Alice"))
    response = client.get(f"/groups/{group.id}/settings", headers={**auth(make_user("Bob")), **HX})
    assert response.status_code == 404
    signed_out = client.get(f"/groups/{group.id}/settings", headers=HX, follow_redirects=False)
    assert signed_out.status_code in (200, 303)
    assert signed_out.headers.get("HX-Redirect", "").startswith("/login")


def test_save_settings_returns_topbar_and_events(
    client: TestClient, make_user, make_group, auth, tmp_db: sqlite3.Connection
) -> None:
    alice = make_user("Alice")
    group = make_group(alice, "Trip", "CHF")
    response = client.post(
        f"/groups/{group.id}/settings",
        data={"name": " Ski ", "currency": "USD"},
        headers={**auth(alice), **HX},
    )
    assert response.status_code == 200
    assert response.headers["HX-Reswap"] == "none"
    assert _events(response) == {
        "toast": {"message": "Group updated"},
        "close-dialog": {},
    }
    assert 'id="topbar" hx-swap-oob="true"' in response.text
    assert "Ski" in response.text
    row = tmp_db.execute("SELECT name, currency, invite_code FROM groups").fetchone()
    assert (row["name"], row["currency"], row["invite_code"]) == ("Ski", "CHF", group.invite_code)


def test_save_settings_422(client: TestClient, make_user, make_group, auth) -> None:
    alice = make_user("Alice")
    group = make_group(alice, "Trip")
    response = client.post(
        f"/groups/{group.id}/settings", data={"name": "  "}, headers={**auth(alice), **HX}
    )
    assert response.status_code == 422
    assert "Give the group a name." in response.text
    assert "HX-Trigger" not in response.headers


def test_save_settings_not_a_member(client: TestClient, make_user, make_group, auth) -> None:
    group = make_group(make_user("Alice"))
    response = client.post(
        f"/groups/{group.id}/settings",
        data={"name": "Hack"},
        headers={**auth(make_user("B")), **HX},
    )
    assert response.status_code == 404


def test_invite_dialog_for_any_member(
    client: TestClient, make_user, make_group, join_group, auth
) -> None:
    alice, bob = make_user("Alice"), make_user("Bob")
    group = make_group(alice, "Trip")
    join_group(group, bob)
    response = client.get(f"/groups/{group.id}/invite", headers={**auth(bob), **HX})
    assert response.status_code == 200
    assert "Share this code to invite people to Trip." in response.text
    assert f'aria-label="Invite code">{group.invite_code}</div>' in response.text
    assert f'data-copied="Code {group.invite_code} copied"' in response.text
    stranger = client.get(f"/groups/{group.id}/invite", headers={**auth(make_user("C")), **HX})
    assert stranger.status_code == 404


def test_leave_redirects_home(
    client: TestClient, make_user, make_group, join_group, auth, tmp_db: sqlite3.Connection
) -> None:
    alice, bob = make_user("Alice"), make_user("Bob")
    group = make_group(alice)
    join_group(group, bob)
    response = client.post(f"/groups/{group.id}/leave", headers={**auth(bob), **HX})
    assert response.status_code == 200
    assert json.loads(response.headers["HX-Location"])["path"] == "/"
    assert members_repo.find_by_user(tmp_db, group.id, bob.id) is None
    assert f"You left {group.name}" in client.get("/", headers=auth(bob)).text


def test_leave_twice_is_404_and_goes_home(client: TestClient, make_user, make_group, auth) -> None:
    alice, bob = make_user("Alice"), make_user("Bob")
    group = make_group(alice)
    response = client.post(f"/groups/{group.id}/leave", headers={**auth(bob), **HX})
    assert response.status_code == 404
    assert json.loads(response.headers["HX-Location"])["path"] == "/"


def test_leave_blocked_by_a_transaction(
    client: TestClient, make_user, make_group, add_expense, auth, tmp_db: sqlite3.Connection
) -> None:
    alice = make_user("Alice")
    group = make_group(alice)
    a = members_repo.find_by_user(tmp_db, group.id, alice.id).id
    add_expense(group, a, [a], 500)
    response = client.post(f"/groups/{group.id}/leave", headers={**auth(alice), **HX})
    assert response.status_code == 409
    assert "members-changed" in _events(response)
    assert members_repo.find_by_user(tmp_db, group.id, alice.id) is not None


def test_leave_signed_out(client: TestClient, make_user, make_group) -> None:
    group = make_group(make_user("Alice"))
    assert client.post(f"/groups/{group.id}/leave", follow_redirects=False).status_code == 303


def test_two_users_two_tabs(client: TestClient, make_user, make_group, join_group, auth) -> None:
    alice, bob = make_user("Alice"), make_user("Bob")
    group = make_group(alice)
    join_group(group, bob)
    alice_page = client.get(f"/groups/{group.id}", headers=auth(alice)).text
    bob_page = client.get(f"/groups/{group.id}", headers=auth(bob)).text
    assert f'data-user-id="{alice.id}"' in alice_page
    assert f'data-user-id="{bob.id}"' in bob_page
