import sqlite3
from datetime import date, timedelta

import pytest

from app.balances.service import group_balances, transaction_list
from app.core import clock
from app.core.errors import NotFound, ValidationFailed
from app.expenses import service
from app.expenses.schemas import ExpenseForm
from app.members import repo as members_repo


@pytest.fixture
def trio(tmp_db: sqlite3.Connection, make_user, make_group, join_group):
    """Alice, Bob, Carla in one EUR group. Returns users, group and member ids."""
    alice, bob, carla = make_user("Alice"), make_user("Bob"), make_user("Carla")
    group = make_group(alice)
    ids = [members_repo.find_by_user(tmp_db, group.id, alice.id).id]  # type: ignore[union-attr]
    ids += [join_group(group, bob), join_group(group, carla)]
    return alice, bob, group, ids


def _form(ids, amount="10.00", payer=None, parts=None, **extra) -> ExpenseForm:
    values = {
        "description": "Dinner",
        "amount": amount,
        "expense_date": clock.today_iso(),
        "payer_id": str(payer or ids[0]),
        "p": [str(i) for i in (ids if parts is None else parts)],
    }
    return ExpenseForm(**{**values, **extra})


def _shares(conn: sqlite3.Connection, expense_id: int) -> dict[int, int]:
    rows = conn.execute(
        "SELECT member_id, share FROM expense_shares WHERE expense_id = ?", (expense_id,)
    )
    return {r["member_id"]: r["share"] for r in rows}


def test_ten_euro_for_three_gives_334_333_333(tmp_db, trio) -> None:
    alice, _, group, ids = trio
    expense_id = service.add_expense(tmp_db, alice, group.id, _form(ids))
    assert _shares(tmp_db, expense_id) == {ids[0]: 334, ids[1]: 333, ids[2]: 333}


def test_one_cent_for_three(tmp_db, trio) -> None:
    alice, _, group, ids = trio
    expense_id = service.add_expense(tmp_db, alice, group.id, _form(ids, amount="0.01"))
    assert _shares(tmp_db, expense_id) == {ids[0]: 1, ids[1]: 0, ids[2]: 0}


def test_remainder_follows_join_order_not_selection_order(tmp_db, trio) -> None:
    alice, _, group, ids = trio
    form = _form(ids, amount="0.02", parts=[ids[2], ids[1], ids[0]])
    expense_id = service.add_expense(tmp_db, alice, group.id, form)
    assert _shares(tmp_db, expense_id) == {ids[0]: 1, ids[1]: 1, ids[2]: 0}


def test_amount_is_stored_in_minor_units(tmp_db, trio) -> None:
    alice, _, group, ids = trio
    expense_id = service.add_expense(tmp_db, alice, group.id, _form(ids, amount="12,50"))
    assert service.get(tmp_db, group.id, expense_id).amount == 1250


def test_jpy_has_no_decimals(tmp_db, make_user, make_group) -> None:
    alice = make_user("Alice")
    group = make_group(alice, currency="JPY")
    me = members_repo.find_by_user(tmp_db, group.id, alice.id).id  # type: ignore[union-attr]
    expense_id = service.add_expense(tmp_db, alice, group.id, _form([me], amount="1500"))
    assert service.get(tmp_db, group.id, expense_id).amount == 1500
    with pytest.raises(ValidationFailed) as err:
        service.add_expense(tmp_db, alice, group.id, _form([me], amount="1500.5"))
    assert err.value.fields == {"amount": "This currency has no decimals."}


def test_payer_can_be_outside_the_participants(tmp_db, trio) -> None:
    alice, _, group, ids = trio
    form = _form(ids, payer=ids[2], parts=ids[:2])
    expense_id = service.add_expense(tmp_db, alice, group.id, form)
    balances = group_balances(tmp_db, group.id)
    assert balances == {ids[0]: -500, ids[1]: -500, ids[2]: 1000}
    assert set(_shares(tmp_db, expense_id)) == set(ids[:2])


def test_all_field_errors_together(tmp_db, trio) -> None:
    alice, _, group, ids = trio
    form = ExpenseForm(description=" ", amount="", expense_date="", payer_id="", p=[])
    with pytest.raises(ValidationFailed) as err:
        service.add_expense(tmp_db, alice, group.id, form)
    assert err.value.fields == {
        "description": "Add a short description.",
        "amount": "Enter an amount.",
        "expense_date": "Pick an expense date.",
        "payer_id": "Choose who paid.",
        "participants": "Pick at least one participant.",
    }


def test_description_length(tmp_db, trio) -> None:
    alice, _, group, ids = trio
    service.add_expense(tmp_db, alice, group.id, _form(ids, description="x" * 100))
    with pytest.raises(ValidationFailed) as err:
        service.add_expense(tmp_db, alice, group.id, _form(ids, description="x" * 101))
    assert err.value.fields == {"description": "Use at most 100 characters."}


def test_future_date_is_rejected_with_the_clock(tmp_db, trio, monkeypatch) -> None:
    alice, _, group, ids = trio
    monkeypatch.setattr(clock, "today_iso", lambda: "2026-11-05")
    service.add_expense(tmp_db, alice, group.id, _form(ids, expense_date="2026-11-05"))
    with pytest.raises(ValidationFailed) as err:
        service.add_expense(tmp_db, alice, group.id, _form(ids, expense_date="2026-11-06"))
    assert err.value.fields == {"expense_date": "The expense date cannot be in the future."}
    tomorrow = (date.today() + timedelta(days=2)).isoformat()
    monkeypatch.undo()
    with pytest.raises(ValidationFailed):
        service.add_expense(tmp_db, alice, group.id, _form(ids, expense_date=tomorrow))


@pytest.mark.parametrize("text", ["2026-13-01", "5 Nov 2026", "20261105", "2026-1-5"])
def test_bad_date_text(tmp_db, trio, text) -> None:
    alice, _, group, ids = trio
    with pytest.raises(ValidationFailed) as err:
        service.add_expense(tmp_db, alice, group.id, _form(ids, expense_date=text))
    assert err.value.fields == {"expense_date": "Pick an expense date."}


def test_payer_and_participants_must_be_members(tmp_db, trio, make_user, make_group) -> None:
    alice, _, group, ids = trio
    other = make_group(make_user("Zed"), name="Other")
    outsider = members_repo.list_members(tmp_db, other.id)[0].id
    with pytest.raises(ValidationFailed) as err:
        service.add_expense(tmp_db, alice, group.id, _form(ids, payer=outsider))
    assert err.value.fields == {"payer_id": "Choose who paid."}
    with pytest.raises(ValidationFailed) as err:
        service.add_expense(tmp_db, alice, group.id, _form(ids, parts=[ids[0], outsider]))
    assert list(err.value.fields) == ["participants"]
    with pytest.raises(ValidationFailed):
        service.add_expense(tmp_db, alice, group.id, _form(ids, parts=["abc"]))
    assert transaction_list(tmp_db, group.id, ids[0]).total == 0  # nothing was written


def test_edit_keeps_equal_split_and_recomputes_shares(tmp_db, trio) -> None:
    alice, _, group, ids = trio
    expense_id = service.add_expense(tmp_db, alice, group.id, _form(ids))
    query = "SELECT created_at FROM expenses WHERE id = ?"
    before = tmp_db.execute(query, (expense_id,)).fetchone()
    form = _form(ids, amount="9.01", parts=ids[:2], description="Taxi", payer=ids[1])
    service.update_expense(tmp_db, alice, group.id, expense_id, form)
    expense = service.get(tmp_db, group.id, expense_id)
    assert (expense.description, expense.amount, expense.payer_id) == ("Taxi", 901, ids[1])
    assert expense.shares == {ids[0]: 451, ids[1]: 450}
    after = tmp_db.execute("SELECT created_at FROM expenses WHERE id = ?", (expense_id,)).fetchone()
    assert after["created_at"] == before["created_at"]
    assert sum(group_balances(tmp_db, group.id).values()) == 0


def test_edit_with_errors_changes_nothing(tmp_db, trio) -> None:
    alice, _, group, ids = trio
    expense_id = service.add_expense(tmp_db, alice, group.id, _form(ids))
    with pytest.raises(ValidationFailed):
        service.update_expense(tmp_db, alice, group.id, expense_id, _form(ids, amount="0"))
    assert service.get(tmp_db, group.id, expense_id).amount == 1000


def test_delete_removes_expense_and_shares(tmp_db, trio) -> None:
    alice, _, group, ids = trio
    expense_id = service.add_expense(tmp_db, alice, group.id, _form(ids))
    service.delete_expense(tmp_db, alice, group.id, expense_id)
    assert _shares(tmp_db, expense_id) == {}
    assert group_balances(tmp_db, group.id) == dict.fromkeys(ids, 0)
    with pytest.raises(service.ExpenseNotFound):
        service.delete_expense(tmp_db, alice, group.id, expense_id)


def test_expense_of_another_group_is_not_found(tmp_db, trio, make_user, make_group) -> None:
    alice, _, group, ids = trio
    zed = make_user("Zed")
    other = make_group(zed, name="Other")
    expense_id = service.add_expense(tmp_db, alice, group.id, _form(ids))
    with pytest.raises(service.ExpenseNotFound):
        service.update_expense(tmp_db, zed, other.id, expense_id, _form([ids[0]]))
    with pytest.raises(service.ExpenseNotFound):
        service.delete_expense(tmp_db, zed, other.id, expense_id)
    with pytest.raises(NotFound):
        service.form_view(tmp_db, zed, group.id)  # not a member of the group


def test_preview_hints(trio, tmp_db) -> None:
    _, _, group, ids = trio
    members = members_repo.list_members(tmp_db, group.id)
    even = service.build_preview(members, "9.00", [str(i) for i in ids], "EUR")
    assert even.hint == "3 participants · 3.00 EUR each"
    assert even.all_selected and set(even.shares.values()) == {300}
    odd = service.build_preview(members, "10.00", [str(ids[2]), str(ids[0])], "EUR")
    assert odd.hint == "2 participants · 5.00 EUR each"
    assert list(odd.shares) == [ids[0], ids[2]]
    uneven = service.build_preview(members, "10.00", [str(i) for i in ids], "EUR")
    assert uneven.hint == "3 participants · the first 1 in join order get one minor unit more"
    assert list(uneven.shares.values()) == [334, 333, 333]
    assert service.build_preview(members, "x", [str(ids[0])], "EUR").shares == {}
    assert service.build_preview(members, "10", [], "EUR").hint == "Choose who shares this expense."
    one = service.build_preview(members, "", [str(ids[0])], "EUR")
    assert one.hint == "1 participant" and not one.all_selected


def test_form_view_defaults_and_stored_values(tmp_db, trio) -> None:
    _, bob, group, ids = trio
    view = service.form_view(tmp_db, bob, group.id)
    assert view.values.payer_id == str(ids[1])
    assert view.values.p == [str(i) for i in ids]
    assert view.values.expense_date == clock.today_iso()
    expense_id = service.add_expense(tmp_db, bob, group.id, _form(ids, amount="90"))
    stored = service.form_view(tmp_db, bob, group.id, expense_id=expense_id)
    assert stored.values.amount == "90.00"
    assert stored.confirm_body == (
        "The app deletes Dinner (90.00 EUR) and recalculates the balances."
    )


def test_validation_runs_inside_the_transaction(tmp_db, trio, monkeypatch) -> None:
    alice, _, group, ids = trio
    seen: list[bool] = []
    real = service.validate

    def spy(*args):
        seen.append(tmp_db.in_transaction)
        return real(*args)

    monkeypatch.setattr(service, "validate", spy)
    expense_id = service.add_expense(tmp_db, alice, group.id, _form(ids))
    service.update_expense(tmp_db, alice, group.id, expense_id, _form(ids))
    assert seen == [True, True]
    assert not tmp_db.in_transaction
