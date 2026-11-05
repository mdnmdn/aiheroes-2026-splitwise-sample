"""Form models and value types of the expenses feature."""

from dataclasses import dataclass, field

from pydantic import BaseModel, StrictInt

from app.core.api import Minor
from app.groups.schemas import Group
from app.members.schemas import Member


class ExpenseForm(BaseModel):
    """Raw text of the dialog. p holds the member ids of the participants."""

    description: str = ""
    amount: str = ""
    expense_date: str = ""
    payer_id: str = ""
    p: list[str] = []


@dataclass(frozen=True)
class Expense:
    id: int
    group_id: int
    description: str
    amount: int
    expense_date: str
    payer_id: int
    shares: dict[int, int]  # member id -> share in minor units, in join order


@dataclass(frozen=True)
class ExpenseData:
    """Validated values, ready to store. participant_ids are in join order."""

    description: str
    amount: int
    expense_date: str
    payer_id: int
    participant_ids: list[int]


@dataclass(frozen=True)
class Preview:
    """What the participant tiles show. shares maps a member id to minor units."""

    shares: dict[int, int]
    hint: str
    all_selected: bool


@dataclass(frozen=True)
class ExpenseView:
    """Context of the expense dialog."""

    group: Group
    members: list[Member]
    values: ExpenseForm
    errors: dict[str, str]
    preview: Preview
    expense_id: int | None = None
    today: str = ""
    confirm_body: str = field(default="")


class ExpenseIn(BaseModel):
    """Body of the JSON API. amount is in minor units of the currency of the group."""

    description: str = ""
    amount: Minor
    expense_date: str = ""
    payer_id: StrictInt = 0
    participant_ids: list[StrictInt] = []


class ShareOut(BaseModel):
    member_id: int
    amount: int


class ExpenseOut(BaseModel):
    id: int
    group_id: int
    description: str
    amount: int
    currency: str
    expense_date: str
    payer_id: int
    shares: list[ShareOut]
