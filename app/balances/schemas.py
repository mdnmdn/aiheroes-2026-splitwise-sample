"""Value types of the balances feature."""

from dataclasses import dataclass

from pydantic import BaseModel

FILTERS = ("all", "mine")


@dataclass(frozen=True)
class TxRow:
    """One row of the transaction list. kind is "expense" or "payment"."""

    kind: str
    id: int
    date: str
    amount: int
    title: str
    meta: str


@dataclass(frozen=True)
class DayGroup:
    date: str
    rows: list[TxRow]


@dataclass(frozen=True)
class TxList:
    days: list[DayGroup]
    shown: int
    total: int
    filter: str


@dataclass(frozen=True)
class Summary:
    """What the balances card shows. balances: member id to minor units, in join order."""

    balances: dict[int, int]
    total_spent: int
    is_settled: bool
    has_transactions: bool


@dataclass(frozen=True)
class Line:
    """One line of the member breakdown. delta: signed minor units."""

    kind: str
    date: str
    title: str
    meta: str
    delta: int


@dataclass(frozen=True)
class Breakdown:
    lines: list[Line]
    balance: int


class BalanceOut(BaseModel):
    """balance is in minor units of currency. Positive: the member is owed money."""

    member_id: int
    balance: int
    currency: str


class TransactionOut(BaseModel):
    """One expense or payment. kind is "expense" or "payment". amount is in minor units."""

    kind: str
    id: int
    date: str
    amount: int
    currency: str
    title: str
    meta: str
