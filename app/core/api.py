"""Shared types of the JSON API under /api/v1. See _docs/tech/guide-api.md."""

from typing import Annotated

from pydantic import Field, StrictInt

Minor = Annotated[StrictInt, Field(description="Money in minor units, an integer")]
"""An amount in minor units. A float, a string or a bool is not valid."""
