import sqlite3

import pytest

from app.core.errors import Conflict, NotFound, ValidationFailed
from app.members import repo, service
from app.users import repo as users_repo

NEW = "__new"


def test_panel_in_join_order_with_me_and_balance(
    tmp_db: sqlite3.Connection, make_user, make_group, join_group, add_expense
) -> None:
    alice, bob, carla = make_user("Alice"), make_user("Bob"), make_user("Carla")
    group = make_group(alice)
    b = join_group(group, bob)
    join_group(group, carla)
    a = repo.find_by_user(tmp_db, group.id, alice.id).id  # type: ignore[union-attr]
    add_expense(group, a, [a, b], 1001)
    panel = service.panel(tmp_db, bob, group.id)
    assert [r.member.name for r in panel.rows] == ["Alice", "Bob", "Carla"]
    assert [r.is_me for r in panel.rows] == [False, True, False]
    assert [r.balance for r in panel.rows] == [500, -500, 0]
    assert sum(r.balance for r in panel.rows) == 0


def test_panel_needs_membership(tmp_db: sqlite3.Connection, make_user, make_group) -> None:
    group = make_group(make_user("Alice"))
    with pytest.raises(NotFound):
        service.panel(tmp_db, make_user("Bob"), group.id)


def test_add_existing_user_goes_last(tmp_db: sqlite3.Connection, make_user, make_group) -> None:
    alice, bob, carla = make_user("Alice"), make_user("Bob"), make_user("Carla")
    group = make_group(alice)
    service.add_member(tmp_db, alice, group.id, str(carla.id), "")
    service.add_member(tmp_db, alice, group.id, str(bob.id), "ignored")
    assert [m.name for m in repo.list_members(tmp_db, group.id)] == ["Alice", "Carla", "Bob"]


def test_add_new_user_creates_user_and_member(
    tmp_db: sqlite3.Connection, make_user, make_group
) -> None:
    alice = make_user("Alice")
    group = make_group(alice)
    member = service.add_member(tmp_db, alice, group.id, NEW, "  Eve ")
    assert member.name == "Eve"
    assert users_repo.find_by_name(tmp_db, "Eve") is not None


@pytest.mark.parametrize(
    ("name", "message"),
    [("", "Enter a name."), ("a" * 31, "Use at most 30 characters."),
     ("ALICE", "ALICE is a user. Pick that user from the list or use a different name.")],
)  # fmt: skip
def test_add_new_user_name_rules(
    tmp_db: sqlite3.Connection, make_user, make_group, name: str, message: str
) -> None:
    alice = make_user("Alice")
    group = make_group(alice)
    with pytest.raises(ValidationFailed) as err:
        service.add_member(tmp_db, alice, group.id, NEW, name)
    assert err.value.fields == {"name": message}
    assert len(repo.list_members(tmp_db, group.id)) == 1


@pytest.mark.parametrize("choice", ["", "999", "abc", "-1", "9" * 30])
def test_add_unknown_choice(tmp_db: sqlite3.Connection, make_user, make_group, choice: str) -> None:
    alice = make_user("Alice")
    group = make_group(alice)
    with pytest.raises(ValidationFailed) as err:
        service.add_member(tmp_db, alice, group.id, choice, "")
    assert err.value.fields == {"user_id": "Choose a user."}


def test_add_a_member_twice(tmp_db: sqlite3.Connection, make_user, make_group) -> None:
    alice, bob = make_user("Alice"), make_user("Bob")
    group = make_group(alice)
    service.add_member(tmp_db, alice, group.id, str(bob.id), "")
    with pytest.raises(ValidationFailed) as err:
        service.add_member(tmp_db, alice, group.id, str(bob.id), "")
    assert err.value.fields == {"user_id": "Bob is a member of this group."}
    assert len(repo.list_members(tmp_db, group.id)) == 2


def test_add_needs_membership(tmp_db: sqlite3.Connection, make_user, make_group) -> None:
    alice, bob = make_user("Alice"), make_user("Bob")
    group = make_group(alice)
    with pytest.raises(NotFound):
        service.add_member(tmp_db, bob, group.id, str(bob.id), "")


def test_add_options_lists_users_outside_the_group(
    tmp_db: sqlite3.Connection, make_user, make_group, join_group
) -> None:
    alice, bob, carla = make_user("Alice"), make_user("Bob"), make_user("carla")
    other = make_group(alice)
    group = make_group(alice, "Second")
    join_group(group, bob)
    _, users = service.add_options(tmp_db, alice, group.id)
    assert [u.name for u in users] == ["carla"]
    assert carla.id == users[0].id
    assert other.id != group.id


def test_remove_keeps_the_user(
    tmp_db: sqlite3.Connection, make_user, make_group, join_group
) -> None:
    alice, bob = make_user("Alice"), make_user("Bob")
    group = make_group(alice)
    member_id = join_group(group, bob)
    removed = service.remove_member(tmp_db, alice, group.id, member_id)
    assert removed.name == "Bob"
    assert [m.name for m in repo.list_members(tmp_db, group.id)] == ["Alice"]
    assert users_repo.find_by_id(tmp_db, bob.id) is not None
    with pytest.raises(NotFound):
        service.remove_member(tmp_db, alice, group.id, member_id)


def test_remove_blocked_for_an_expense_payer(
    tmp_db: sqlite3.Connection, make_user, make_group, join_group, add_expense
) -> None:
    alice, bob = make_user("Alice"), make_user("Bob")
    group = make_group(alice)
    a = repo.find_by_user(tmp_db, group.id, alice.id).id  # type: ignore[union-attr]
    b = join_group(group, bob)
    add_expense(group, b, [b], 500)
    with pytest.raises(Conflict):
        service.remove_member(tmp_db, alice, group.id, b)
    assert not service.detail(tmp_db, alice, group.id, b).removable
    assert service.detail(tmp_db, alice, group.id, a).removable
    assert len(repo.list_members(tmp_db, group.id)) == 2


def test_remove_blocked_for_an_expense_participant(
    tmp_db: sqlite3.Connection, make_user, make_group, join_group, add_expense
) -> None:
    alice, bob = make_user("Alice"), make_user("Bob")
    group = make_group(alice)
    a = repo.find_by_user(tmp_db, group.id, alice.id).id  # type: ignore[union-attr]
    b = join_group(group, bob)
    add_expense(group, a, [a, b], 500)
    with pytest.raises(Conflict):
        service.remove_member(tmp_db, alice, group.id, b)


@pytest.mark.parametrize("role", ["sender", "receiver"])
def test_remove_blocked_for_a_payment(
    tmp_db: sqlite3.Connection, make_user, make_group, join_group, add_payment, role: str
) -> None:
    alice, bob = make_user("Alice"), make_user("Bob")
    group = make_group(alice)
    a = repo.find_by_user(tmp_db, group.id, alice.id).id  # type: ignore[union-attr]
    b = join_group(group, bob)
    add_payment(group, *((b, a) if role == "sender" else (a, b)), 300)
    with pytest.raises(Conflict):
        service.remove_member(tmp_db, alice, group.id, b)


def test_transactions_of_another_group_do_not_block(
    tmp_db: sqlite3.Connection, make_user, make_group, join_group, add_expense
) -> None:
    alice, bob = make_user("Alice"), make_user("Bob")
    busy, quiet = make_group(alice, "Busy"), make_group(alice, "Quiet")
    b_busy = join_group(busy, bob)
    b_quiet = join_group(quiet, bob)
    add_expense(busy, b_busy, [b_busy], 500)
    service.remove_member(tmp_db, alice, quiet.id, b_quiet)


def test_leave_removes_the_member_of_the_user(
    tmp_db: sqlite3.Connection, make_user, make_group, join_group
) -> None:
    alice, bob = make_user("Alice"), make_user("Bob")
    group = make_group(alice)
    join_group(group, bob)
    assert service.leave_group(tmp_db, bob, group.id).id == group.id
    assert [m.name for m in repo.list_members(tmp_db, group.id)] == ["Alice"]
    with pytest.raises(NotFound):
        service.leave_group(tmp_db, bob, group.id)  # second leave: not a member any more


def test_leave_blocked_with_a_transaction(
    tmp_db: sqlite3.Connection, make_user, make_group, add_expense
) -> None:
    alice = make_user("Alice")
    group = make_group(alice)
    a = repo.find_by_user(tmp_db, group.id, alice.id).id  # type: ignore[union-attr]
    add_expense(group, a, [a], 500)
    with pytest.raises(Conflict):
        service.leave_group(tmp_db, alice, group.id)


def test_last_member_can_leave_the_group_stays(
    tmp_db: sqlite3.Connection, make_user, make_group
) -> None:
    alice = make_user("Alice")
    group = make_group(alice)
    service.leave_group(tmp_db, alice, group.id)
    assert repo.list_members(tmp_db, group.id) == []
    assert tmp_db.execute("SELECT COUNT(*) FROM groups").fetchone()[0] == 1
