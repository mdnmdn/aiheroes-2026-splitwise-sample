"""Form models and value types of the members feature."""

from dataclasses import dataclass

from pydantic import BaseModel, StrictInt


@dataclass(frozen=True)
class Member:
    id: int
    user_id: int
    name: str


@dataclass(frozen=True)
class MemberRow:
    """A member with the balance in minor units of the base currency of the group."""

    member: Member
    balance: int
    is_me: bool


class AddMemberForm(BaseModel):
    user_id: str = ""
    name: str = ""


class MemberAddIn(BaseModel):
    """Body of add: user_id of an existing user, or name of a new user."""

    user_id: StrictInt | None = None
    name: str | None = None


class MemberOut(BaseModel):
    id: int
    user_id: int
    name: str
