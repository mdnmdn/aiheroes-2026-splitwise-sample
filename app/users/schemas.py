"""Form models of the sign-in."""

from pydantic import BaseModel

NEW_USER = "__new"


class LoginForm(BaseModel):
    user_id: str = ""
    name: str = ""
    next: str = ""


class UserIn(BaseModel):
    name: str = ""


class UserOut(BaseModel):
    id: int
    name: str


class UserWithToken(UserOut):
    token: str
