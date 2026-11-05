import json
import sqlite3

from fastapi.testclient import TestClient

from app.members import repo as members_repo

HX = {"HX-Request": "true"}


def _events(response) -> dict:
    return json.loads(response.headers["HX-Trigger"])


def test_panel_fragment(client: TestClient, make_user, make_group, join_group, auth) -> None:
    alice, bob = make_user("Alice"), make_user("Bob")
    group = make_group(alice)
    join_group(group, bob)
    response = client.get(f"/groups/{group.id}/members", headers={**auth(bob), **HX})
    assert response.status_code == 200
    text = response.text
    assert text.lstrip().startswith('<div class="card" id="members-region"')
    assert "members-changed from:body, ledger-changed from:body" in text
    assert text.index("Alice") < text.index("Bob")
    assert text.count("You</span>") == 1
    assert "settled" in text
    assert "<html" not in text


def test_panel_not_htmx_redirects_to_the_page(
    client: TestClient, make_user, make_group, auth
) -> None:
    alice = make_user("Alice")
    group = make_group(alice)
    url = f"/groups/{group.id}/members"
    response = client.get(url, headers=auth(alice), follow_redirects=False)
    assert (response.status_code, response.headers["location"]) == (303, f"/groups/{group.id}")


def test_panel_not_a_member_and_signed_out(client: TestClient, make_user, make_group, auth) -> None:
    group = make_group(make_user("Alice"))
    stranger = client.get(f"/groups/{group.id}/members", headers={**auth(make_user("Bob")), **HX})
    assert stranger.status_code == 404
    signed_out = client.get(f"/groups/{group.id}/members", headers=HX)
    assert signed_out.headers["HX-Redirect"].startswith("/login")


def test_add_dialog_lists_users_outside_the_group(
    client: TestClient, make_user, make_group, auth
) -> None:
    alice = make_user("Alice")
    make_user("Bob")
    group = make_group(alice)
    text = client.get(f"/groups/{group.id}/members/new", headers={**auth(alice), **HX}).text
    assert "Add member" in text
    assert ">Bob</option>" in text
    assert ">Alice</option>" not in text
    assert '<option value="__new">New user…</option>' in text
    assert "To let someone join on their own, share the invite code instead." in text
    assert 'data-k="name" hidden' in text


def test_add_dialog_preselects_new_user_when_no_one_is_left(
    client: TestClient, make_user, make_group, auth
) -> None:
    alice = make_user("Alice")
    group = make_group(alice)
    text = client.get(f"/groups/{group.id}/members/new", headers={**auth(alice), **HX}).text
    assert '<option value="__new" selected>' in text
    assert 'data-k="name" hidden' not in text


def test_add_existing_user(
    client: TestClient, make_user, make_group, auth, tmp_db: sqlite3.Connection
) -> None:
    alice, bob = make_user("Alice"), make_user("Bob")
    group = make_group(alice, "Trip")
    response = client.post(
        f"/groups/{group.id}/members", data={"user_id": str(bob.id)}, headers={**auth(alice), **HX}
    )
    assert response.status_code == 200
    assert response.headers["HX-Reswap"] == "none"
    assert _events(response) == {
        "toast": {"message": "Bob added to Trip"},
        "close-dialog": {},
        "members-changed": {},
    }
    assert [m.name for m in members_repo.list_members(tmp_db, group.id)] == ["Alice", "Bob"]


def test_add_new_user(client: TestClient, make_user, make_group, auth, tmp_db) -> None:
    alice = make_user("Alice")
    group = make_group(alice)
    response = client.post(
        f"/groups/{group.id}/members",
        data={"user_id": "__new", "name": "Eve"},
        headers={**auth(alice), **HX},
    )
    assert response.status_code == 200
    assert "Eve added to" in _events(response)["toast"]["message"]
    assert tmp_db.execute("SELECT COUNT(*) FROM users").fetchone()[0] == 2


def test_add_422_keeps_the_selection_and_name(
    client: TestClient, make_user, make_group, auth
) -> None:
    alice = make_user("Alice")
    make_user("Bob")
    group = make_group(alice)
    response = client.post(
        f"/groups/{group.id}/members",
        data={"user_id": "__new", "name": "alice"},
        headers={**auth(alice), **HX},
    )
    assert response.status_code == 422
    assert "alice is a user." in response.text
    assert 'value="alice"' in response.text
    assert '<option value="__new" selected>' in response.text
    assert "<dialog" not in response.text
    unknown = client.post(
        f"/groups/{group.id}/members", data={"user_id": "999"}, headers={**auth(alice), **HX}
    )
    assert unknown.status_code == 422
    assert "Choose a user." in unknown.text


def test_add_member_already_in_the_group(
    client: TestClient, make_user, make_group, join_group, auth
) -> None:
    alice, bob = make_user("Alice"), make_user("Bob")
    group = make_group(alice)
    join_group(group, bob)
    response = client.post(
        f"/groups/{group.id}/members", data={"user_id": str(bob.id)}, headers={**auth(alice), **HX}
    )
    assert response.status_code == 422
    assert "Bob is a member of this group." in response.text


def test_add_not_a_member_and_signed_out(client: TestClient, make_user, make_group, auth) -> None:
    group = make_group(make_user("Alice"))
    bob = make_user("Bob")
    data = {"user_id": str(bob.id)}
    url = f"/groups/{group.id}/members"
    assert client.post(url, data=data, headers={**auth(bob), **HX}).status_code == 404
    signed_out = client.post(f"/groups/{group.id}/members", data=data, headers=HX)
    assert signed_out.headers["HX-Redirect"].startswith("/login")


def test_member_dialog_removable(
    client: TestClient, make_user, make_group, join_group, auth
) -> None:
    alice, bob = make_user("Alice"), make_user("Bob")
    group = make_group(alice, "Trip")
    member_id = join_group(group, bob)
    text = client.get(f"/groups/{group.id}/members/{member_id}", headers={**auth(alice), **HX}).text
    assert "Remove from group" in text
    assert f'hx-post="/groups/{group.id}/members/{member_id}/delete"' in text
    assert 'data-confirm-title="Remove Bob?"' in text
    assert "The app removes Bob from Trip. Bob can rejoin with the invite code." in text
    assert 'data-confirm-ok="Remove member"' in text
    assert "disabled" not in text
    assert "0.00 EUR" in text


def test_member_dialog_for_me_is_leave(
    client: TestClient, make_user, make_group, auth, tmp_db
) -> None:
    alice = make_user("Alice")
    group = make_group(alice, "Trip")
    a = members_repo.find_by_user(tmp_db, group.id, alice.id).id
    text = client.get(f"/groups/{group.id}/members/{a}", headers={**auth(alice), **HX}).text
    assert "Leave group" in text
    assert f'hx-post="/groups/{group.id}/leave"' in text
    assert 'data-confirm-title="Leave Trip?"' in text
    assert "You can rejoin later with the invite code." in text


def test_member_dialog_disabled_with_a_transaction(
    client: TestClient, make_user, make_group, join_group, add_expense, auth, tmp_db
) -> None:
    alice, bob = make_user("Alice"), make_user("Bob")
    group = make_group(alice)
    a = members_repo.find_by_user(tmp_db, group.id, alice.id).id
    b = join_group(group, bob)
    add_expense(group, b, [a, b], 500)
    text = client.get(f"/groups/{group.id}/members/{b}", headers={**auth(alice), **HX}).text
    assert 'disabled="disabled"' in text
    assert "Members with transactions in this group cannot be removed." in text
    assert "+2.50 EUR" in text
    assert "Bob is owed" in text


def test_member_dialog_unknown_member_is_404(
    client: TestClient, make_user, make_group, auth
) -> None:
    alice = make_user("Alice")
    group = make_group(alice)
    response = client.get(f"/groups/{group.id}/members/999", headers={**auth(alice), **HX})
    assert response.status_code == 404


def test_member_dialog_has_no_rename(
    client: TestClient, make_user, make_group, join_group, auth
) -> None:
    alice, bob = make_user("Alice"), make_user("Bob")
    group = make_group(alice)
    member_id = join_group(group, bob)
    headers = {**auth(alice), **HX}
    url = f"/groups/{group.id}/members/{member_id}"
    assert "Rename" not in client.get(url, headers=headers).text
    assert client.get(f"{url}/rename", headers=headers).status_code in (404, 405)
    assert client.post(f"{url}/rename", data={"name": "Z"}, headers=headers).status_code in (
        404,
        405,
    )


def test_remove_member(
    client: TestClient, make_user, make_group, join_group, auth, tmp_db: sqlite3.Connection
) -> None:
    alice, bob = make_user("Alice"), make_user("Bob")
    group = make_group(alice)
    member_id = join_group(group, bob)
    response = client.post(
        f"/groups/{group.id}/members/{member_id}/delete", headers={**auth(alice), **HX}
    )
    assert response.status_code == 200
    assert _events(response)["toast"] == {"message": "Bob removed"}
    assert "members-changed" in _events(response)
    assert members_repo.find(tmp_db, group.id, member_id) is None


def test_remove_member_with_a_transaction_is_409(
    client: TestClient, make_user, make_group, join_group, add_payment, auth, tmp_db
) -> None:
    alice, bob = make_user("Alice"), make_user("Bob")
    group = make_group(alice)
    a = members_repo.find_by_user(tmp_db, group.id, alice.id).id
    b = join_group(group, bob)
    add_payment(group, b, a, 300)
    response = client.post(f"/groups/{group.id}/members/{b}/delete", headers={**auth(alice), **HX})
    assert response.status_code == 409
    assert "members-changed" in _events(response)
    assert members_repo.find(tmp_db, group.id, b) is not None


def test_remove_member_twice_is_404(
    client: TestClient, make_user, make_group, join_group, auth
) -> None:
    alice, bob = make_user("Alice"), make_user("Bob")
    group = make_group(alice)
    member_id = join_group(group, bob)
    url = f"/groups/{group.id}/members/{member_id}/delete"
    client.post(url, headers={**auth(alice), **HX})
    again = client.post(url, headers={**auth(alice), **HX})
    assert again.status_code == 404
    assert "members-changed" in _events(again)


def test_remove_signed_out_and_stranger(
    client: TestClient, make_user, make_group, join_group, auth
) -> None:
    alice, bob = make_user("Alice"), make_user("Bob")
    group = make_group(alice)
    member_id = join_group(group, bob)
    url = f"/groups/{group.id}/members/{member_id}/delete"
    assert client.post(url, headers=HX).headers["HX-Redirect"].startswith("/login")
    assert client.post(url, headers={**auth(make_user("C")), **HX}).status_code == 404


def test_remove_myself_is_refused(
    client: TestClient, make_user, make_group, auth, tmp_db: sqlite3.Connection
) -> None:
    alice = make_user("Alice")
    group = make_group(alice)
    a = members_repo.find_by_user(tmp_db, group.id, alice.id).id
    response = client.post(f"/groups/{group.id}/members/{a}/delete", headers={**auth(alice), **HX})
    assert response.status_code == 409
    assert _events(response)["toast"] == {"message": "You cannot remove yourself. Use Leave."}
    assert members_repo.find(tmp_db, group.id, a) is not None


def test_member_of_another_group_is_404(
    client: TestClient, make_user, make_group, join_group, auth
) -> None:
    alice, bob = make_user("Alice"), make_user("Bob")
    mine, other = make_group(alice, "Mine"), make_group(bob, "Other")
    foreign = join_group(other, make_user("Carol"))
    headers = {**auth(alice), **HX}
    base = f"/groups/{mine.id}/members/{foreign}"
    assert client.get(base, headers=headers).status_code == 404
    assert client.post(f"{base}/delete", headers=headers).status_code == 404
