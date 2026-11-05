import json
import sqlite3

from fastapi.testclient import TestClient

from app.balances.service import group_balances
from app.core import clock

HX = {"HX-Request": "true"}


def _events(response) -> dict:
    return json.loads(response.headers["HX-Trigger"])


def _setup(make_user, make_group, join_group):
    alice, bob = make_user("Alice"), make_user("Bob")
    group = make_group(alice)
    return alice, bob, group, join_group(group, bob)


def _body(a: int, b: int, **extra) -> dict:
    data = {
        "description": "Dinner",
        "amount": "10.00",
        "expense_date": clock.today_iso(),
        "payer_id": str(a),
        "p": [str(a), str(b)],
    }
    return {**data, **extra}


def _member_id(tmp_db: sqlite3.Connection, user_id: int) -> int:
    return tmp_db.execute("SELECT id FROM members WHERE user_id = ?", (user_id,)).fetchone()["id"]


def test_new_dialog_fragment(client: TestClient, make_user, make_group, join_group, auth) -> None:
    alice, bob, group, b = _setup(make_user, make_group, join_group)
    response = client.get(f"/groups/{group.id}/expenses/new", headers={**auth(bob), **HX})
    text = response.text
    assert response.status_code == 200
    assert text.lstrip().startswith('<dialog id="expense-dialog"')
    assert "Add expense" in text and ">Delete<" not in text
    assert f'<option value="{b}" selected>Bob</option>' in text
    assert text.count('type="checkbox"') == 2 and text.count(" checked>") == 2
    assert "2 participants" in text and "€" in text


def test_new_dialog_not_htmx_redirects_and_signed_out(
    client: TestClient, make_user, make_group, auth
) -> None:
    alice = make_user("Alice")
    group = make_group(alice)
    url = f"/groups/{group.id}/expenses/new"
    response = client.get(url, headers=auth(alice), follow_redirects=False)
    assert (response.status_code, response.headers["location"]) == (303, f"/groups/{group.id}")
    assert client.get(url, headers=HX).headers["HX-Redirect"].startswith("/login")
    stranger = client.get(url, headers={**auth(make_user("Zed")), **HX})
    assert stranger.status_code == 404


def test_preview_fragment(client: TestClient, make_user, make_group, join_group, auth) -> None:
    alice, bob, group, b = _setup(make_user, make_group, join_group)
    url = f"/groups/{group.id}/expenses/preview?amount=10&p={b}"
    response = client.get(url, headers={**auth(alice), **HX})
    text = response.text
    assert response.status_code == 200
    assert f'id="share-{b}" hx-swap-oob="true">10.00 EUR<' in text
    assert "1 participant · 10.00 EUR each" in text
    assert "Select all" in text
    bad_url = f"/groups/{group.id}/expenses/preview?amount=x&p={b}"
    bad = client.get(bad_url, headers={**auth(alice), **HX})
    assert 'hx-swap-oob="true"></span>' in bad.text
    signed_out = client.get(url, headers=HX)
    assert signed_out.headers["HX-Redirect"].startswith("/login")


def test_add_expense(client: TestClient, tmp_db, make_user, make_group, join_group, auth) -> None:
    alice, bob, group, b = _setup(make_user, make_group, join_group)
    a = _member_id(tmp_db, alice.id)
    response = client.post(
        f"/groups/{group.id}/expenses", data=_body(a, b), headers={**auth(alice), **HX}
    )
    assert response.status_code == 200 and response.text == ""
    assert response.headers["HX-Reswap"] == "none"
    assert _events(response) == {
        "toast": {"message": "Expense added"},
        "close-dialog": {},
        "ledger-changed": {},
    }
    assert group_balances(tmp_db, group.id) == {a: 500, b: -500}


def test_add_expense_422_rerenders_the_form(
    client: TestClient, tmp_db, make_user, make_group, join_group, auth
) -> None:
    alice, bob, group, b = _setup(make_user, make_group, join_group)
    a = _member_id(tmp_db, alice.id)
    body = _body(a, b, description="", amount="abc")
    response = client.post(f"/groups/{group.id}/expenses", data=body, headers={**auth(alice), **HX})
    text = response.text
    assert response.status_code == 422
    assert text.lstrip().startswith('<form class="dlg" id="expenseForm"')
    assert "Fix 2 fields to continue:" in text
    assert "Add a short description." in text
    assert "Use digits only, for example 12.50." in text
    assert 'value="abc"' in text
    assert tmp_db.execute("SELECT COUNT(*) FROM expenses").fetchone()[0] == 0


def test_edit_dialog_and_save(
    client: TestClient, tmp_db, make_user, make_group, join_group, add_expense, auth
) -> None:
    alice, bob, group, b = _setup(make_user, make_group, join_group)
    a = _member_id(tmp_db, alice.id)
    eid = add_expense(group, a, [a, b], 9000)
    dialog = client.get(f"/groups/{group.id}/expenses/{eid}/edit", headers={**auth(bob), **HX}).text
    assert "Edit expense" in dialog and 'value="90.00"' in dialog
    assert 'data-confirm-title="Delete this expense?"' in dialog
    assert "The app deletes Dinner (90.00 EUR) and recalculates the balances." in dialog
    assert f'hx-post="/groups/{group.id}/expenses/{eid}/delete"' in dialog
    body = _body(a, b, amount="20", description="Taxi")
    response = client.post(
        f"/groups/{group.id}/expenses/{eid}", data=body, headers={**auth(bob), **HX}
    )
    assert response.status_code == 200
    assert _events(response)["toast"] == {"message": "Expense updated"}
    assert group_balances(tmp_db, group.id) == {a: 1000, b: -1000}
    invalid = client.post(
        f"/groups/{group.id}/expenses/{eid}",
        data=_body(a, b, amount="0"),
        headers={**auth(bob), **HX},
    )
    assert invalid.status_code == 422 and "Edit expense" in invalid.text
    assert "The amount must be more than zero." in invalid.text


def test_delete_expense_twice(
    client: TestClient, tmp_db, make_user, make_group, join_group, add_expense, auth
) -> None:
    alice, bob, group, b = _setup(make_user, make_group, join_group)
    a = _member_id(tmp_db, alice.id)
    eid = add_expense(group, a, [a, b], 9000)
    url = f"/groups/{group.id}/expenses/{eid}/delete"
    first = client.post(url, headers={**auth(alice), **HX})
    assert first.status_code == 200
    assert _events(first)["toast"] == {"message": "Expense deleted"}
    assert group_balances(tmp_db, group.id) == {a: 0, b: 0}
    second = client.post(url, headers={**auth(alice), **HX})
    assert second.status_code == 404
    events = _events(second)
    assert events["toast"] == {"message": "That expense does not exist."}
    assert "ledger-changed" in events


def test_expense_of_another_group_is_404(
    client: TestClient, tmp_db, make_user, make_group, join_group, add_expense, auth
) -> None:
    alice, bob, group, b = _setup(make_user, make_group, join_group)
    a = _member_id(tmp_db, alice.id)
    eid = add_expense(group, a, [a, b], 9000)
    zed = make_user("Zed")
    other = make_group(zed, name="Other")
    zed_headers = {**auth(zed), **HX}
    z = _member_id(tmp_db, zed.id)
    own = f"/groups/{other.id}/expenses/{eid}"
    assert client.get(own + "/edit", headers=zed_headers).status_code == 404
    save = client.post(own, data=_body(z, z, p=[str(z)]), headers=zed_headers)
    assert save.status_code == 404
    assert client.post(own + "/delete", headers=zed_headers).status_code == 404
    # Not a member of the group in the URL: also 404, and nothing changed.
    foreign = client.post(f"/groups/{group.id}/expenses/{eid}/delete", headers=zed_headers)
    assert foreign.status_code == 404
    assert group_balances(tmp_db, group.id) == {a: 4500, b: -4500}


def test_signed_out_mutations(client: TestClient, make_user, make_group) -> None:
    group = make_group(make_user("Alice"))
    response = client.post(f"/groups/{group.id}/expenses", data={}, headers=HX)
    assert response.headers["HX-Redirect"].startswith("/login")


def test_form_carries_hx_disabled_elt(
    client: TestClient, make_user, make_group, join_group, auth
) -> None:
    alice, bob, group, b = _setup(make_user, make_group, join_group)
    text = client.get(f"/groups/{group.id}/expenses/new", headers={**auth(bob), **HX}).text
    assert 'hx-disabled-elt="find button[type=submit]"' in text


def test_save_on_deleted_expense_is_404(
    client: TestClient, tmp_db, make_user, make_group, join_group, auth
) -> None:
    alice, bob, group, b = _setup(make_user, make_group, join_group)
    a = _member_id(tmp_db, alice.id)
    headers = {**auth(alice), **HX}
    client.post(f"/groups/{group.id}/expenses", data=_body(a, b), headers=headers)
    eid = tmp_db.execute("SELECT id FROM expenses").fetchone()["id"]
    client.post(f"/groups/{group.id}/expenses/{eid}/delete", headers=headers)
    for body in (_body(a, b), _body(a, b, amount="-1")):
        response = client.post(f"/groups/{group.id}/expenses/{eid}", data=body, headers=headers)
        assert response.status_code == 404
        assert _events(response)["toast"] == {"message": "That expense does not exist."}


def test_save_422_when_expense_vanishes_meanwhile_is_404(
    client: TestClient, tmp_db, make_user, make_group, join_group, auth, monkeypatch
) -> None:
    from app.core.errors import ValidationFailed
    from app.expenses import service

    alice, bob, group, b = _setup(make_user, make_group, join_group)
    a = _member_id(tmp_db, alice.id)
    headers = {**auth(alice), **HX}
    client.post(f"/groups/{group.id}/expenses", data=_body(a, b), headers=headers)
    eid = tmp_db.execute("SELECT id FROM expenses").fetchone()["id"]

    def race(*args, **kwargs):
        tmp_db.execute("DELETE FROM expenses WHERE id = ?", (eid,))
        raise ValidationFailed("Fix the fields.", fields={"amount": "x"})

    monkeypatch.setattr(service, "update_expense", race)
    response = client.post(f"/groups/{group.id}/expenses/{eid}", data=_body(a, b), headers=headers)
    assert response.status_code == 404


def test_edit_changing_payer_and_participants_resplits(
    client: TestClient, tmp_db, make_user, make_group, join_group, auth
) -> None:
    alice, bob, group, b = _setup(make_user, make_group, join_group)
    a = _member_id(tmp_db, alice.id)
    c = join_group(group, make_user("Carla"))
    headers = {**auth(alice), **HX}
    client.post(f"/groups/{group.id}/expenses", data=_body(a, b), headers=headers)
    eid = tmp_db.execute("SELECT id FROM expenses").fetchone()["id"]
    body = _body(b, c, amount="10.01", p=[str(a), str(b), str(c)], payer_id=str(c))
    saved = client.post(f"/groups/{group.id}/expenses/{eid}", data=body, headers=headers)
    assert _events(saved)["toast"] == {"message": "Expense updated"}
    shares = tmp_db.execute(
        "SELECT member_id, share FROM expense_shares WHERE expense_id = ?", (eid,)
    ).fetchall()
    assert {r["member_id"]: r["share"] for r in shares} == {a: 334, b: 334, c: 333}
    assert group_balances(tmp_db, group.id) == {a: -334, b: -334, c: 668}
