"""Form models and value types of the payments feature."""

from dataclasses import dataclass

from pydantic import BaseModel, StrictInt

from app.core.api import Minor
from app.groups.schemas import Group
from app.members.schemas import Member


class PaymentForm(BaseModel):
    """Raw text of the dialog. "Mark as paid" builds the same form."""

    sender_id: str = ""
    receiver_id: str = ""
    amount: str = ""
    payment_date: str = ""
    note: str = ""


@dataclass(frozen=True)
class Payment:
    id: int
    group_id: int
    sender_id: int
    receiver_id: int
    amount: int
    payment_date: str
    note: str


@dataclass(frozen=True)
class PaymentData:
    sender_id: int
    receiver_id: int
    amount: int
    payment_date: str
    note: str


@dataclass(frozen=True)
class PaymentView:
    """Context of the payment dialog."""

    group: Group
    members: list[Member]
    values: PaymentForm
    errors: dict[str, str]
    payment_id: int | None = None
    today: str = ""
    confirm_body: str = ""


class PaymentIn(BaseModel):
    """Body of the JSON API. amount is in minor units of the currency of the group."""

    sender_id: StrictInt = 0
    receiver_id: StrictInt = 0
    amount: Minor
    payment_date: str = ""
    note: str = ""


class PaymentOut(BaseModel):
    id: int
    group_id: int
    sender_id: int
    receiver_id: int
    amount: int
    currency: str
    payment_date: str
    note: str
