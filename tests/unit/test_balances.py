from random import Random

from app.balances.service import compute_balances
from app.core.money import split_equal

ALICE, BOB, CARLA = 1, 2, 3
JOIN = [ALICE, BOB, CARLA]


def _random_case(rng: Random) -> tuple[list[int], list, list, list]:
    members = list(range(1, rng.randint(2, 7) + 1))
    expenses, shares = [], []
    for _ in range(rng.randint(0, 8)):
        amount = rng.randint(1, 100_000)
        participants = rng.sample(members, rng.randint(1, len(members)))
        expenses.append((rng.choice(members), amount))
        shares.extend(zip(participants, split_equal(amount, len(participants)), strict=True))
    payments = []
    for _ in range(rng.randint(0, 4)):
        sender_id, receiver_id = rng.sample(members, 2)
        payments.append((sender_id, receiver_id, rng.randint(1, 50_000)))
    return members, expenses, shares, payments


def test_acceptance_alice_pays_for_everyone() -> None:
    balances = compute_balances(
        JOIN, [(ALICE, 9000)], [(ALICE, 3000), (BOB, 3000), (CARLA, 3000)], []
    )
    assert balances == {ALICE: 6000, BOB: -3000, CARLA: -3000}


def test_acceptance_bob_pays_alice() -> None:
    balances = compute_balances(
        JOIN, [(ALICE, 9000)], [(ALICE, 3000), (BOB, 3000), (CARLA, 3000)], [(BOB, ALICE, 3000)]
    )
    assert balances == {ALICE: 3000, BOB: 0, CARLA: -3000}


def test_acceptance_first_expense_deleted() -> None:
    balances = compute_balances(JOIN, [], [], [(BOB, ALICE, 3000)])
    assert balances == {ALICE: -3000, BOB: 3000, CARLA: 0}


def test_member_without_activity_is_zero() -> None:
    assert compute_balances([ALICE, BOB], [], [], []) == {ALICE: 0, BOB: 0}


def test_random_balances_sum_to_zero() -> None:
    for seed in range(50):
        members, expenses, shares, payments = _random_case(Random(seed))
        balances = compute_balances(members, expenses, shares, payments)
        assert sum(balances.values()) == 0, seed


def test_balances_of_groups_keep_groups_apart(
    tmp_db, make_user, make_group, join_group, add_expense, add_payment
) -> None:
    from app.balances.service import balances_of_groups, group_balances
    from app.members import repo as members_repo

    alice, bob = make_user("Alice"), make_user("Bob")
    one, two, empty = make_group(alice, "One"), make_group(alice, "Two"), make_group(bob, "Empty")
    a1 = members_repo.find_by_user(tmp_db, one.id, alice.id).id
    b1 = join_group(one, bob)
    a2 = members_repo.find_by_user(tmp_db, two.id, alice.id).id
    b2 = join_group(two, bob)
    add_expense(one, a1, [a1, b1], 1000)
    add_expense(two, b2, [a2, b2], 300)
    add_payment(two, a2, b2, 50)
    ids = [one.id, two.id, empty.id]
    many = balances_of_groups(tmp_db, ids)
    assert many == {g: group_balances(tmp_db, g) for g in ids}
    assert many[one.id] == {a1: 500, b1: -500}
    assert many[two.id] == {a2: -100, b2: 100}
    assert balances_of_groups(tmp_db, []) == {}
