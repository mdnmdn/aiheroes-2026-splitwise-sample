import json
import sqlite3

from fastapi.testclient import TestClient

from app.balances.service import group_balances
from app.core import clock

HX = {"HX-Request": "true"}


def _events(response) -> dict:
    return json.loads(response.headers["HX-Trigger"])


def _member_id(tmp_db: sqlite3.Connection, user_id: int) -> int:
    return tmp_db.execute("SELECT id FROM members WHERE user_id = ?", (user_id,)).fetchone()["id"]


def _setup(make_user, make_group, join_group):
    alice, bob = make_user("Alice"), make_user("Bob")
    group = make_group(alice)
    return alice, bob, group, join_group(group, bob)


def _body(sender: int, receiver: int, **extra) -> dict:
    data = {
        "sender_id": str(sender),
        "receiver_id": str(receiver),
        "amount": "30.00",
        "payment_date": clock.today_iso(),
        "note": "",
    }
    return {**data, **extra}


def test_new_dialog_defaults(client: TestClient, make_user, make_group, join_group, auth) -> None:
    alice, bob, group, b = _setup(make_user, make_group, join_group)
    response = client.get(f"/groups/{group.id}/payments/new", headers={**auth(bob), **HX})
    text = response.text
    assert response.status_code == 200
    assert text.lstrip().startswith('<dialog id="payment-dialog"')
    assert "Add payment" in text and ">Delete<" not in text
    assert "Records money that one member gave to another member." in text
    assert f'<option value="{b}" selected>Bob</option>' in text  # sender: me
    assert "Alice</option>" in text and "Save payment" in text


def test_new_dialog_with_one_member_opens_the_invite(
    client: TestClient, make_user, make_group, auth
) -> None:
    alice = make_user("Alice")
    group = make_group(alice)
    response = client.get(f"/groups/{group.id}/payments/new", headers={**auth(alice), **HX})
    assert response.status_code == 200
    assert "Invite to group" in response.text and group.invite_code in response.text
    assert _events(response) == {"toast": {"message": "Add one more member first."}}


def test_dialog_not_htmx_and_signed_out(client: TestClient, make_user, make_group, auth) -> None:
    alice = make_user("Alice")
    group = make_group(alice)
    url = f"/groups/{group.id}/payments/new"
    redirect = client.get(url, headers=auth(alice), follow_redirects=False)
    assert (redirect.status_code, redirect.headers["location"]) == (303, f"/groups/{group.id}")
    assert client.get(url, headers=HX).headers["HX-Redirect"].startswith("/login")
    assert client.get(url, headers={**auth(make_user("Zed")), **HX}).status_code == 404


def test_record_payment(
    client: TestClient, tmp_db, make_user, make_group, join_group, auth
) -> None:
    alice, bob, group, b = _setup(make_user, make_group, join_group)
    a = _member_id(tmp_db, alice.id)
    response = client.post(
        f"/groups/{group.id}/payments", data=_body(b, a), headers={**auth(bob), **HX}
    )
    assert response.status_code == 200 and response.text == ""
    assert response.headers["HX-Reswap"] == "none"
    assert _events(response) == {
        "toast": {"message": "Payment recorded"},
        "close-dialog": {},
        "ledger-changed": {},
    }
    assert group_balances(tmp_db, group.id) == {a: -3000, b: 3000}


def test_record_422(client: TestClient, tmp_db, make_user, make_group, join_group, auth) -> None:
    alice, bob, group, b = _setup(make_user, make_group, join_group)
    a = _member_id(tmp_db, alice.id)
    body = _body(a, a, amount="", note="x" * 101)
    response = client.post(f"/groups/{group.id}/payments", data=body, headers={**auth(alice), **HX})
    text = response.text
    assert response.status_code == 422
    assert text.lstrip().startswith('<form class="dlg" id="paymentForm"')
    assert "Fix 3 fields to continue:" in text
    assert "Sender and receiver must be different members." in text
    assert "Enter an amount." in text and "Use at most 100 characters." in text
    assert tmp_db.execute("SELECT COUNT(*) FROM payments").fetchone()[0] == 0


def test_edit_and_delete(
    client: TestClient, tmp_db, make_user, make_group, join_group, add_payment, auth
) -> None:
    alice, bob, group, b = _setup(make_user, make_group, join_group)
    a = _member_id(tmp_db, alice.id)
    pid = add_payment(group, b, a, 3000)
    headers = {**auth(alice), **HX}
    dialog = client.get(f"/groups/{group.id}/payments/{pid}/edit", headers=headers).text
    assert "Edit payment" in dialog and 'value="30.00"' in dialog
    assert 'data-confirm-title="Delete this payment?"' in dialog
    assert "Bob → Alice, 30.00 EUR. The app recalculates the balances." in dialog
    saved = client.post(
        f"/groups/{group.id}/payments/{pid}", data=_body(a, b, amount="5"), headers=headers
    )
    assert _events(saved)["toast"] == {"message": "Payment updated"}
    assert group_balances(tmp_db, group.id) == {a: 500, b: -500}
    invalid = client.post(
        f"/groups/{group.id}/payments/{pid}", data=_body(a, b, amount="-1"), headers=headers
    )
    assert invalid.status_code == 422 and "Edit payment" in invalid.text
    gone = client.post(f"/groups/{group.id}/payments/{pid}/delete", headers=headers)
    assert _events(gone)["toast"] == {"message": "Payment deleted"}
    assert group_balances(tmp_db, group.id) == {a: 0, b: 0}
    again = client.post(f"/groups/{group.id}/payments/{pid}/delete", headers=headers)
    assert again.status_code == 404
    assert _events(again)["toast"] == {"message": "That payment does not exist."}


def test_payment_of_another_group_is_404(
    client: TestClient, tmp_db, make_user, make_group, join_group, add_payment, auth
) -> None:
    alice, bob, group, b = _setup(make_user, make_group, join_group)
    a = _member_id(tmp_db, alice.id)
    pid = add_payment(group, b, a, 3000)
    zed = make_user("Zed")
    other = make_group(zed, name="Other")
    z = _member_id(tmp_db, zed.id)
    headers = {**auth(zed), **HX}
    assert client.get(f"/groups/{other.id}/payments/{pid}/edit", headers=headers).status_code == 404
    save = client.post(f"/groups/{other.id}/payments/{pid}", data=_body(z, z), headers=headers)
    assert save.status_code == 404
    for gid in (other.id, group.id):
        response = client.post(f"/groups/{gid}/payments/{pid}/delete", headers=headers)
        assert response.status_code == 404
    assert group_balances(tmp_db, group.id) == {a: -3000, b: 3000}


def test_signed_out_mutation(client: TestClient, make_user, make_group) -> None:
    group = make_group(make_user("Alice"))
    response = client.post(f"/groups/{group.id}/payments", data={}, headers=HX)
    assert response.headers["HX-Redirect"].startswith("/login")


def test_form_carries_hx_disabled_elt(
    client: TestClient, make_user, make_group, join_group, auth
) -> None:
    alice, bob, group, b = _setup(make_user, make_group, join_group)
    text = client.get(f"/groups/{group.id}/payments/new", headers={**auth(bob), **HX}).text
    assert 'hx-disabled-elt="find button[type=submit]"' in text


def test_save_on_deleted_payment_is_404(
    client: TestClient, tmp_db, make_user, make_group, join_group, add_payment, auth
) -> None:
    alice, bob, group, b = _setup(make_user, make_group, join_group)
    a = _member_id(tmp_db, alice.id)
    pid = add_payment(group, b, a, 3000)
    headers = {**auth(alice), **HX}
    client.post(f"/groups/{group.id}/payments/{pid}/delete", headers=headers)
    for body in (_body(a, b), _body(a, b, amount="-1")):
        response = client.post(f"/groups/{group.id}/payments/{pid}", data=body, headers=headers)
        assert response.status_code == 404
        assert _events(response)["toast"] == {"message": "That payment does not exist."}


def test_save_422_when_payment_vanishes_meanwhile_is_404(
    client: TestClient, tmp_db, make_user, make_group, join_group, add_payment, auth, monkeypatch
) -> None:
    from app.core.errors import ValidationFailed
    from app.payments import service

    alice, bob, group, b = _setup(make_user, make_group, join_group)
    a = _member_id(tmp_db, alice.id)
    pid = add_payment(group, b, a, 3000)

    def race(*args, **kwargs):
        tmp_db.execute("DELETE FROM payments WHERE id = ?", (pid,))
        raise ValidationFailed("Fix the fields.", fields={"amount": "x"})

    monkeypatch.setattr(service, "update_payment", race)
    response = client.post(
        f"/groups/{group.id}/payments/{pid}", data=_body(a, b), headers={**auth(alice), **HX}
    )
    assert response.status_code == 404


def test_record_rejects_member_of_another_group(
    client: TestClient, tmp_db, make_user, make_group, join_group, auth
) -> None:
    alice, bob, group, b = _setup(make_user, make_group, join_group)
    a = _member_id(tmp_db, alice.id)
    zed = make_user("Zed")
    make_group(zed, name="Other")
    z = _member_id(tmp_db, zed.id)
    headers = {**auth(alice), **HX}
    for body in (_body(z, a), _body(a, z)):
        response = client.post(f"/groups/{group.id}/payments", data=body, headers=headers)
        assert response.status_code == 422
    assert group_balances(tmp_db, group.id) == {a: 0, b: 0}
