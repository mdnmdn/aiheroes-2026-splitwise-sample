import sqlite3

import pytest

from app.balances.service import group_balances
from app.core import clock
from app.core.errors import ValidationFailed
from app.members import repo as members_repo
from app.payments import service
from app.payments.schemas import PaymentForm


@pytest.fixture
def duo(tmp_db: sqlite3.Connection, make_user, make_group, join_group):
    alice, bob = make_user("Alice"), make_user("Bob")
    group = make_group(alice)
    a = members_repo.find_by_user(tmp_db, group.id, alice.id).id  # type: ignore[union-attr]
    return alice, bob, group, a, join_group(group, bob)


def _form(sender, receiver, **extra) -> PaymentForm:
    values = {
        "sender_id": str(sender),
        "receiver_id": str(receiver),
        "amount": "30.00",
        "payment_date": clock.today_iso(),
        "note": "",
    }
    return PaymentForm(**{**values, **extra})


def test_payment_moves_balances_and_sums_to_zero(tmp_db, duo) -> None:
    alice, bob, group, a, b = duo
    service.record_payment(tmp_db, bob, group.id, _form(b, a))
    assert group_balances(tmp_db, group.id) == {a: -3000, b: 3000}


def test_sender_and_receiver_must_differ(tmp_db, duo) -> None:
    alice, _, group, a, _ = duo
    with pytest.raises(ValidationFailed) as err:
        service.record_payment(tmp_db, alice, group.id, _form(a, a))
    assert err.value.fields == {"receiver_id": "Sender and receiver must be different members."}


def test_sender_and_receiver_must_be_members(tmp_db, duo, make_user, make_group) -> None:
    alice, _, group, a, _ = duo
    other = make_group(make_user("Zed"), name="Other")
    outsider = members_repo.list_members(tmp_db, other.id)[0].id
    with pytest.raises(ValidationFailed) as err:
        service.record_payment(tmp_db, alice, group.id, _form(outsider, a))
    assert err.value.fields == {"sender_id": "Choose the sender."}
    with pytest.raises(ValidationFailed) as err:
        service.record_payment(tmp_db, alice, group.id, _form(a, outsider))
    assert list(err.value.fields) == ["receiver_id"]


def test_note_length_and_trim(tmp_db, duo) -> None:
    alice, _, group, a, b = duo
    pid = service.record_payment(tmp_db, alice, group.id, _form(a, b, note="  " + "n" * 100 + " "))
    assert len(service.get(tmp_db, group.id, pid).note) == 100
    with pytest.raises(ValidationFailed) as err:
        service.record_payment(tmp_db, alice, group.id, _form(a, b, note="n" * 101))
    assert err.value.fields == {"note": "Use at most 100 characters."}


def test_amount_and_date_rules(tmp_db, duo, monkeypatch) -> None:
    alice, _, group, a, b = duo
    monkeypatch.setattr(clock, "today_iso", lambda: "2026-11-05")
    form = _form(a, b, amount="0", payment_date="2026-11-06")
    with pytest.raises(ValidationFailed) as err:
        service.record_payment(tmp_db, alice, group.id, form)
    assert err.value.fields == {
        "amount": "The amount must be more than zero.",
        "payment_date": "The payment date cannot be in the future.",
    }
    with pytest.raises(ValidationFailed) as err:
        service.record_payment(tmp_db, alice, group.id, _form(a, b, payment_date=""))
    assert err.value.fields == {"payment_date": "Pick a payment date."}


def test_edit_keeps_id_and_entry_time_then_delete(tmp_db, duo) -> None:
    alice, _, group, a, b = duo
    pid = service.record_payment(tmp_db, alice, group.id, _form(a, b))
    first = tmp_db.execute("SELECT created_at FROM payments WHERE id = ?", (pid,)).fetchone()
    service.update_payment(tmp_db, alice, group.id, pid, _form(b, a, amount="5", note="Cash"))
    payment = service.get(tmp_db, group.id, pid)
    stored = (payment.sender_id, payment.receiver_id, payment.amount, payment.note)
    assert stored == (b, a, 500, "Cash")
    row = tmp_db.execute("SELECT created_at FROM payments WHERE id = ?", (pid,)).fetchone()
    assert row["created_at"] == first["created_at"]
    service.delete_payment(tmp_db, alice, group.id, pid)
    assert group_balances(tmp_db, group.id) == {a: 0, b: 0}
    with pytest.raises(service.PaymentNotFound):
        service.delete_payment(tmp_db, alice, group.id, pid)


def test_form_view_defaults(tmp_db, duo) -> None:
    _, bob, group, a, b = duo
    view = service.form_view(tmp_db, bob, group.id)
    assert (view.values.sender_id, view.values.receiver_id) == (str(b), str(a))
    pid = service.record_payment(tmp_db, bob, group.id, _form(b, a))
    stored = service.form_view(tmp_db, bob, group.id, payment_id=pid)
    assert stored.confirm_body == "Bob → Alice, 30.00 EUR. The app recalculates the balances."


def test_validation_runs_inside_the_transaction(tmp_db, duo, monkeypatch) -> None:
    alice, _, group, a, b = duo
    seen: list[bool] = []
    real = service.validate

    def spy(*args):
        seen.append(tmp_db.in_transaction)
        return real(*args)

    monkeypatch.setattr(service, "validate", spy)
    pid = service.record_payment(tmp_db, alice, group.id, _form(a, b))
    service.update_payment(tmp_db, alice, group.id, pid, _form(b, a))
    assert seen == [True, True]


def test_has_other_member(tmp_db, make_user, make_group, join_group) -> None:
    alice = make_user("Alice")
    group = make_group(alice)
    assert not service.has_other_member(tmp_db, group.id)
    join_group(group, make_user("Bob"))
    assert service.has_other_member(tmp_db, group.id)
