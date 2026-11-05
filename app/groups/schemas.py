"""Form models and value types of the groups feature."""

from dataclasses import dataclass

from pydantic import BaseModel

FILTERS = ("all", "owe", "owed")


@dataclass(frozen=True)
class Group:
    id: int
    name: str
    currency: str
    invite_code: str


@dataclass(frozen=True)
class GroupRow:
    """One row of the groups home. balance is in minor units of the base currency."""

    id: int
    name: str
    currency: str
    member_count: int
    transaction_count: int
    balance: int


@dataclass(frozen=True)
class GroupList:
    rows: list[GroupRow]
    total: int


class GroupForm(BaseModel):
    name: str = ""
    currency: str = "EUR"


class JoinForm(BaseModel):
    code: str = ""


class GroupIn(BaseModel):
    """Body of create. currency is a code of the base currencies."""

    name: str = ""
    currency: str = "EUR"


class GroupRename(BaseModel):
    name: str = ""


class GroupJoin(BaseModel):
    code: str = ""


class GroupOut(BaseModel):
    id: int
    name: str
    currency: str
    invite_code: str


class GroupRowOut(BaseModel):
    """balance is in minor units of currency."""

    id: int
    name: str
    currency: str
    member_count: int
    transaction_count: int
    balance: int
