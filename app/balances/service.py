"""Balances of the members. Pure functions on minor units."""

import sqlite3
from collections.abc import Iterable

import structlog

from app.balances import repo
from app.balances.schemas import FILTERS, Breakdown, DayGroup, Line, Summary, TxList, TxRow
from app.core.money import format_money
from app.members import repo as members_repo

log = structlog.get_logger()


def compute_balances(
    member_ids: list[int],
    expenses: Iterable[tuple[int, int]],
    shares: Iterable[tuple[int, int]],
    payments: Iterable[tuple[int, int, int]],
) -> dict[int, int]:
    """Balance per member: paid minus shares, plus payments sent, minus payments received.

    expenses: (payer_id, amount). shares: (member_id, share).
    payments: (sender_id, receiver_id, amount).
    """
    balances = dict.fromkeys(member_ids, 0)
    for payer_id, amount in expenses:
        balances[payer_id] += amount
    for member_id, share in shares:
        balances[member_id] -= share
    for sender_id, receiver_id, amount in payments:
        balances[sender_id] += amount
        balances[receiver_id] -= amount
    return balances


def balances_of_groups(conn: sqlite3.Connection, group_ids: list[int]) -> dict[int, dict[int, int]]:
    """Group id to the balance of each member. Four queries for all groups. Never stored."""
    if not group_ids:
        return {}
    members = repo.member_ids(conn, group_ids)
    expenses = repo.expenses(conn, group_ids)
    shares = repo.shares(conn, group_ids)
    payments = repo.payments(conn, group_ids)
    result = {}
    for g in group_ids:
        result[g] = compute_balances(members[g], expenses[g], shares[g], payments[g])
        _check_invariant(g, result[g])
    return result


def _check_invariant(group_id: int, balances: dict[int, int]) -> bool:
    """True if the balances sum to zero. If not, log the event. Never raise."""
    total = sum(balances.values())
    if total != 0:
        log.error("balance.invariant_violated", group_id=group_id, total=total)
    return total == 0


def group_balances(conn: sqlite3.Connection, group_id: int) -> dict[int, int]:
    """Balance of each member of the group, computed from the rows. Never stored."""
    return balances_of_groups(conn, [group_id])[group_id]


def transaction_list(
    conn: sqlite3.Connection, group_id: int, my_member_id: int, filter_: str = "all"
) -> TxList:
    """Expenses and payments by day, newest first. Mine: the member is payer, participant,
    sender or receiver. Inside a day: newest entry time, then higher id."""
    members = members_repo.list_members(conn, group_id)
    names = {m.id: m.name for m in members}
    mode = filter_ if filter_ in FILTERS else "all"
    in_expense = repo.participants(conn, group_id)
    entries: list[tuple[str, str, int, int, bool, TxRow]] = []
    for r in repo.expense_rows(conn, group_id):
        people = in_expense.get(r["id"], [])
        if len(people) == len(members):
            who = f"everyone ({len(people)})"
        else:
            who = ", ".join(names[i] for i in people)
        row = TxRow(
            "expense", r["id"], r["date"], r["amount"], r["description"],
            f"{names[r['payer_id']]} paid · for {who}",
        )  # fmt: skip
        mine = r["payer_id"] == my_member_id or my_member_id in people
        entries.append((r["date"], r["created_at"], r["id"], 0, mine, row))
    for r in repo.payment_rows(conn, group_id):
        title = f"{names[r['sender_id']]} → {names[r['receiver_id']]}"
        row = TxRow("payment", r["id"], r["date"], r["amount"], title, r["note"])
        mine = my_member_id in (r["sender_id"], r["receiver_id"])
        entries.append((r["date"], r["created_at"], r["id"], 1, mine, row))
    entries.sort(key=lambda e: e[:4], reverse=True)
    shown = [e for e in entries if mode == "all" or e[4]]
    days: list[DayGroup] = []
    for entry in shown:
        if not days or days[-1].date != entry[0]:
            days.append(DayGroup(entry[0], []))
        days[-1].rows.append(entry[5])
    return TxList(days, len(shown), len(entries), mode)


def summary(conn: sqlite3.Connection, group_id: int) -> Summary:
    """The figures of the balances card."""
    balances = group_balances(conn, group_id)
    expenses = repo.expenses(conn, [group_id])[group_id]
    payments = repo.payments(conn, [group_id])[group_id]
    return Summary(
        balances=balances,
        total_spent=sum(amount for _, amount in expenses),
        is_settled=all(balance == 0 for balance in balances.values()),
        has_transactions=bool(expenses or payments),
    )


def breakdown(conn: sqlite3.Connection, group_id: int, member_id: int, currency: str) -> Breakdown:
    """The lines behind the balance of one member, newest first. The deltas add up to the balance.

    Expense: paid minus share. Payment: +amount if sent, minus amount if received.
    """
    names = {m.id: m.name for m in members_repo.list_members(conn, group_id)}
    my_shares = repo.member_shares(conn, group_id, member_id)
    entries: list[tuple[str, str, int, int, Line]] = []
    for r in repo.expense_rows(conn, group_id):
        share = my_shares.get(r["id"], 0)
        paid = r["amount"] if r["payer_id"] == member_id else 0
        if r["id"] not in my_shares and not paid:
            continue
        meta = " · ".join(
            part
            for part in (
                f"Paid {format_money(paid, currency)}" if paid else "",
                f"share {format_money(share, currency)}" if share else "",
            )
            if part
        )
        line = Line("expense", r["date"], r["description"], meta, paid - share)
        entries.append((r["date"], r["created_at"], r["id"], 0, line))
    for r in repo.payment_rows(conn, group_id):
        if r["sender_id"] == member_id:
            title = f"Paid {names[r['receiver_id']]}"
            line = Line("payment", r["date"], title, "Payment · sent", r["amount"])
        elif r["receiver_id"] == member_id:
            title = f"Received from {names[r['sender_id']]}"
            line = Line("payment", r["date"], title, "Payment · received", -r["amount"])
        else:
            continue
        entries.append((r["date"], r["created_at"], r["id"], 1, line))
    entries.sort(key=lambda e: e[:4], reverse=True)
    lines = [e[4] for e in entries]
    return Breakdown(lines, sum(line.delta for line in lines))
