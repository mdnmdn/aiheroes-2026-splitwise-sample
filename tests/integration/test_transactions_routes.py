import sqlite3

from fastapi.testclient import TestClient

HX = {"HX-Request": "true"}


def _member_id(tmp_db: sqlite3.Connection, user_id: int) -> int:
    return tmp_db.execute("SELECT id FROM members WHERE user_id = ?", (user_id,)).fetchone()["id"]


def test_empty_state(client: TestClient, make_user, make_group, auth) -> None:
    alice = make_user("Alice")
    group = make_group(alice)
    response = client.get(f"/groups/{group.id}/transactions", headers={**auth(alice), **HX})
    text = response.text
    assert response.status_code == 200
    assert text.lstrip().startswith('<div class="card" id="expenses-region"')
    assert "ledger-changed from:body, members-changed from:body" in text
    assert "No transactions yet" in text and "Add expense" in text
    assert "0 of 0" in text and "<html" not in text


def test_list_filter_and_counter(
    client: TestClient, tmp_db, make_user, make_group, join_group, add_expense, add_payment, auth
) -> None:
    alice, bob, carla = make_user("Alice"), make_user("Bob"), make_user("Carla")
    group = make_group(alice)
    b, c = join_group(group, bob), join_group(group, carla)
    a = _member_id(tmp_db, alice.id)
    add_expense(group, a, [a, b, c], 9000)
    add_expense(group, b, [b, c], 600)
    add_payment(group, c, b, 100)
    url = f"/groups/{group.id}/transactions"
    everything = client.get(url, headers={**auth(alice), **HX}).text
    assert "3 of 3" in everything and everything.count('class="day-group"') == 1
    assert 'class="tag payment od-fixed">Expense<' in everything
    assert 'class="tag internal od-fixed">Payment<' in everything
    assert "Carla → Bob" in everything and "Alice paid · for everyone (3)" in everything
    assert f'hx-get="/groups/{group.id}/expenses/1/edit"' in everything
    assert f'hx-get="/groups/{group.id}/payments/1/edit"' in everything
    mine = client.get(url + "?filter=mine", headers={**auth(alice), **HX}).text
    assert "1 of 3" in mine and 'id="txFilter-mine" name="filter" value="mine" checked' in mine
    assert "Carla → Bob" not in mine
    nobody = client.get(url + "?filter=mine", headers={**auth(make_user("Zed")), **HX})
    assert nobody.status_code == 404


def test_mine_with_nothing_for_me(
    client: TestClient, tmp_db, make_user, make_group, join_group, add_expense, auth
) -> None:
    alice, bob, carla = make_user("Alice"), make_user("Bob"), make_user("Carla")
    group = make_group(alice)
    b, c = join_group(group, bob), join_group(group, carla)
    add_expense(group, b, [b, c], 600)
    text = client.get(
        f"/groups/{group.id}/transactions?filter=mine", headers={**auth(alice), **HX}
    ).text
    assert "Nothing involves you yet" in text and "0 of 1" in text


def test_not_htmx_and_signed_out(client: TestClient, make_user, make_group, auth) -> None:
    alice = make_user("Alice")
    group = make_group(alice)
    url = f"/groups/{group.id}/transactions"
    response = client.get(url, headers=auth(alice), follow_redirects=False)
    assert (response.status_code, response.headers["location"]) == (303, f"/groups/{group.id}")
    assert client.get(url, headers=HX).headers["HX-Redirect"].startswith("/login")


def test_group_page_has_actions_and_the_list(
    client: TestClient, tmp_db, make_user, make_group, join_group, add_expense, auth
) -> None:
    alice, bob = make_user("Alice"), make_user("Bob")
    group = make_group(alice)
    b = join_group(group, bob)
    add_expense(group, b, [b], 600)
    text = client.get(f"/groups/{group.id}", headers=auth(alice)).text
    assert f'hx-get="/groups/{group.id}/expenses/new"' in text
    assert f'hx-get="/groups/{group.id}/payments/new"' in text
    assert 'class="actionbar mobile-only"' in text
    assert 'id="expenses-region"' in text and "Bob paid · for Bob" in text
    assert text.index('id="members-region"') < text.index('id="expenses-region"')
