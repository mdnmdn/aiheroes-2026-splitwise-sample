"""Ids from the client. An id that no row can have becomes 0, so it is an unknown id."""

from typing import Annotated, Any

from pydantic import BeforeValidator

MAX_ID = 2**63 - 1  # the largest SQLite INTEGER


def parse_id(value: Any) -> int:
    """The id as an int, or 0 if the value is not an id from 1 to MAX_ID. No row has id 0."""
    text = str(value).strip()
    if not (text.isascii() and text.isdecimal()) or len(text) > 19:
        return 0
    number = int(text)
    return number if 1 <= number <= MAX_ID else 0


Id = Annotated[int, BeforeValidator(parse_id)]
"""Type of a path id. An invalid or out-of-range id gives the not-found answer of the route."""
