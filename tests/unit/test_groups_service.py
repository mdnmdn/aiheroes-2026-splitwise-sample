import re
import sqlite3
from collections.abc import Callable

import pytest

from app.core.errors import NotFound, ValidationFailed
from app.core.session import User
from app.groups import repo, service
from app.groups.schemas import Group
from app.members import repo as members_repo

CODE_FORMAT = re.compile(r"[A-Z0-9X]{3}-[ABCDEFGHJKMNPQRSTUVWXYZ23456789]{4}")


@pytest.mark.parametrize(
    ("name", "expected"),
    [
        ("Lisbon trip", "LIS"),
        ("ab", "ABX"),
        ("a", "AXX"),
        ("  7 up!", "7UP"),
        ("!!!", "GRP"),
        ("", "GRP"),
        ("é-a", "AXX"),
    ],
)
def test_invite_prefix(name: str, expected: str) -> None:
    assert service.invite_prefix(name) == expected


def test_draw_code_has_the_format() -> None:
    for _ in range(50):
        assert CODE_FORMAT.fullmatch(service.draw_code("Lisbon trip", lambda c: False))


def test_draw_code_draws_again_when_taken() -> None:
    seen: list[str] = []

    def taken(code: str) -> bool:
        seen.append(code)
        return len(seen) < 3

    code = service.draw_code("Ski", taken)
    assert len(seen) == 3
    assert code == seen[-1]


@pytest.mark.parametrize(
    ("raw", "message"),
    [("", "Give the group a name."), ("   ", "Give the group a name."),
     ("a" * 51, "Use at most 50 characters.")],
)  # fmt: skip
def test_name_errors(raw: str, message: str) -> None:
    with pytest.raises(ValidationFailed) as err:
        service.validate_name(raw)
    assert err.value.fields == {"name": message}


def test_name_is_trimmed_and_may_have_50_characters() -> None:
    assert service.validate_name("  " + "a" * 50 + "  ") == "a" * 50


def test_currency_must_be_one_of_the_15(tmp_db: sqlite3.Connection, make_user, make_group) -> None:
    user = make_user("Alice")
    with pytest.raises(ValidationFailed) as err:
        service.create_group(tmp_db, user, "Trip", "XXX")
    assert "currency" in err.value.fields
    assert make_group(user, "Trip", "JPY").currency == "JPY"


def test_create_makes_group_code_and_first_member(
    tmp_db: sqlite3.Connection, make_user: Callable[[str], User]
) -> None:
    alice = make_user("Alice")
    group = service.create_group(tmp_db, alice, "  Lisbon trip ", "usd")
    assert (group.name, group.currency) == ("Lisbon trip", "USD")
    assert group.invite_code.startswith("LIS-")
    assert CODE_FORMAT.fullmatch(group.invite_code)
    assert [m.name for m in members_repo.list_members(tmp_db, group.id)] == ["Alice"]


def test_group_names_need_not_be_unique(tmp_db: sqlite3.Connection, make_user, make_group) -> None:
    alice = make_user("Alice")
    first, second = make_group(alice, "Trip"), make_group(alice, "Trip")
    assert first.id != second.id
    assert first.invite_code != second.invite_code


def test_create_retries_when_the_code_is_taken_at_insert(
    tmp_db: sqlite3.Connection, make_user, make_group, monkeypatch: pytest.MonkeyPatch
) -> None:
    alice = make_user("Alice")
    existing = make_group(alice, "Trip")
    codes = iter([existing.invite_code, existing.invite_code, "TRI-AAAA"])
    # The pre-check says free, the unique index says taken: the service draws again.
    monkeypatch.setattr(service, "draw_code", lambda name, taken: next(codes))
    assert service.create_group(tmp_db, alice, "Trip", "EUR").invite_code == "TRI-AAAA"


def test_rename_keeps_code_and_currency(tmp_db: sqlite3.Connection, make_user, make_group) -> None:
    alice = make_user("Alice")
    group = make_group(alice, "Trip", "CHF")
    updated = service.update_group(tmp_db, alice, group.id, " Ski week ")
    assert updated.name == "Ski week"
    stored = repo.find(tmp_db, group.id)
    assert stored == Group(group.id, "Ski week", "CHF", group.invite_code)


def test_rename_validates_and_needs_membership(
    tmp_db: sqlite3.Connection, make_user, make_group
) -> None:
    alice, bob = make_user("Alice"), make_user("Bob")
    group = make_group(alice)
    with pytest.raises(ValidationFailed):
        service.update_group(tmp_db, alice, group.id, "")
    with pytest.raises(NotFound):
        service.update_group(tmp_db, bob, group.id, "Hack")
    assert repo.find(tmp_db, group.id).name == group.name  # type: ignore[union-attr]


def test_require_member(tmp_db: sqlite3.Connection, make_user, make_group) -> None:
    alice, bob = make_user("Alice"), make_user("Bob")
    group = make_group(alice)
    found, member = service.require_member(tmp_db, alice, group.id)
    assert found.id == group.id
    assert member.name == "Alice"
    with pytest.raises(NotFound, match="not available"):
        service.require_member(tmp_db, bob, group.id)
    with pytest.raises(NotFound):
        service.require_member(tmp_db, alice, 999)


def test_join_is_case_insensitive_and_adds_last(
    tmp_db: sqlite3.Connection, make_user, make_group
) -> None:
    alice, bob, carla = make_user("Alice"), make_user("Bob"), make_user("Carla")
    group = make_group(alice)
    result = service.join(tmp_db, bob, f"  {group.invite_code.lower()} ")
    assert result.joined
    assert result.group.id == group.id
    service.join(tmp_db, carla, group.invite_code)
    names = [m.name for m in members_repo.list_members(tmp_db, group.id)]
    assert names == ["Alice", "Bob", "Carla"]


def test_join_when_already_a_member_adds_no_row(
    tmp_db: sqlite3.Connection, make_user, make_group
) -> None:
    alice = make_user("Alice")
    group = make_group(alice)
    result = service.join(tmp_db, alice, group.invite_code)
    assert not result.joined
    assert len(members_repo.list_members(tmp_db, group.id)) == 1


def test_join_errors(tmp_db: sqlite3.Connection, make_user) -> None:
    alice = make_user("Alice")
    with pytest.raises(ValidationFailed) as empty:
        service.join(tmp_db, alice, "   ")
    assert empty.value.fields == {"code": "Enter an invite code."}
    with pytest.raises(ValidationFailed) as unknown:
        service.join(tmp_db, alice, "NOP-AAAA")
    assert unknown.value.fields["code"].startswith("No group uses this code.")


def test_rejoin_goes_last(tmp_db: sqlite3.Connection, make_user, make_group, join_group) -> None:
    alice, bob = make_user("Alice"), make_user("Bob")
    group = make_group(alice)
    join_group(group, bob)
    bob_member = members_repo.find_by_user(tmp_db, group.id, bob.id)
    assert bob_member is not None
    members_repo.delete(tmp_db, bob_member.id)
    join_group(group, bob)
    service.join(tmp_db, alice, group.invite_code)
    assert [m.name for m in members_repo.list_members(tmp_db, group.id)] == ["Alice", "Bob"]


def _setup_balances(tmp_db, make_user, make_group, join_group, add_expense):
    alice, bob, carla = make_user("Alice"), make_user("Bob"), make_user("Carla")
    lisbon = make_group(alice, "lisbon trip")
    flat = make_group(alice, "Flat 3B")
    ski = make_group(alice, "Ski")
    a_l = members_repo.find_by_user(tmp_db, lisbon.id, alice.id).id
    b_l = join_group(lisbon, bob)
    a_f = members_repo.find_by_user(tmp_db, flat.id, alice.id).id
    b_f = join_group(flat, bob)
    join_group(ski, carla)
    add_expense(lisbon, a_l, [a_l, b_l], 1001)  # Alice is owed 500 (share 501)
    add_expense(flat, b_f, [a_f, b_f], 1000)  # Alice owes 500
    return alice, lisbon, flat, ski


def test_list_sorted_by_name_without_case_and_counts(
    tmp_db: sqlite3.Connection, make_user, make_group, join_group, add_expense, add_payment
) -> None:
    alice, lisbon, *_ = _setup_balances(tmp_db, make_user, make_group, join_group, add_expense)
    members = members_repo.list_members(tmp_db, lisbon.id)
    add_payment(lisbon, members[1].id, members[0].id, 100)
    result = service.list_groups(tmp_db, alice)
    assert result.total == 3
    assert [r.name for r in result.rows] == ["Flat 3B", "lisbon trip", "Ski"]
    by_name = {r.name: r for r in result.rows}
    assert by_name["lisbon trip"].member_count == 2
    assert by_name["lisbon trip"].transaction_count == 2  # one expense and one payment
    assert by_name["Ski"].transaction_count == 0


def test_list_balance_of_the_current_user(
    tmp_db: sqlite3.Connection, make_user, make_group, join_group, add_expense
) -> None:
    alice, *_ = _setup_balances(tmp_db, make_user, make_group, join_group, add_expense)
    balances = {r.name: r.balance for r in service.list_groups(tmp_db, alice).rows}
    assert balances == {"Flat 3B": -500, "lisbon trip": 500, "Ski": 0}


@pytest.mark.parametrize(
    ("filter_", "names"),
    [
        ("all", ["Flat 3B", "lisbon trip", "Ski"]),
        ("owe", ["Flat 3B"]),
        ("owed", ["lisbon trip"]),
        ("nonsense", ["Flat 3B", "lisbon trip", "Ski"]),
    ],
)
def test_list_filter(
    tmp_db: sqlite3.Connection, make_user, make_group, join_group, add_expense, filter_, names
) -> None:
    alice, *_ = _setup_balances(tmp_db, make_user, make_group, join_group, add_expense)
    result = service.list_groups(tmp_db, alice, "", filter_)
    assert [r.name for r in result.rows] == names
    assert result.total == 3


def test_list_search_is_a_substring_without_case(
    tmp_db: sqlite3.Connection, make_user, make_group, join_group, add_expense
) -> None:
    alice, *_ = _setup_balances(tmp_db, make_user, make_group, join_group, add_expense)
    assert [r.name for r in service.list_groups(tmp_db, alice, " LISB ").rows] == ["lisbon trip"]
    assert [r.name for r in service.list_groups(tmp_db, alice, "o").rows] == ["lisbon trip"]
    assert service.list_groups(tmp_db, alice, "zzz").rows == []
    assert service.list_groups(tmp_db, alice, "zzz").total == 3
    both = service.list_groups(tmp_db, alice, "s", "owed")
    assert [r.name for r in both.rows] == ["lisbon trip"]


def test_list_only_has_groups_of_the_user(
    tmp_db: sqlite3.Connection, make_user, make_group
) -> None:
    alice, bob = make_user("Alice"), make_user("Bob")
    make_group(alice)
    assert service.list_groups(tmp_db, bob).total == 0
