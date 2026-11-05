import sqlite3

import pytest

from app.core.errors import ValidationFailed
from app.users import service


@pytest.mark.parametrize(
    ("name", "expected"),
    [
        ("", "Enter a name."),
        ("Al", None),
        ("a" * 30, None),
        ("a" * 31, "Use at most 30 characters."),
    ],
)
def test_name_error(name: str, expected: str | None) -> None:
    assert service.name_error(name) == expected


@pytest.mark.parametrize(
    "value",
    ["/", "/groups/1", "/groups/1?q=ski&filter=mine", "/a_b-c.d/e%20f", "/x?next=%2Fgroups"],
)
def test_safe_next_keeps_local_path(value: str) -> None:
    assert service.safe_next(value) == value


@pytest.mark.parametrize(
    "value",
    [None, "", "groups", "//evil.example", "https://evil.example"]
    + ["/\\evil", "/a:b", "/a b", "/<x>"],
)
def test_safe_next_rejects_other_values(value: str | None) -> None:
    assert service.safe_next(value) == "/"


def test_validate_name_trims_and_checks_case_insensitive(tmp_db: sqlite3.Connection) -> None:
    created = service.sign_in(tmp_db, "__new", "  Alice ")
    assert created.name == "Alice"
    with pytest.raises(ValidationFailed) as err:
        service.validate_name(tmp_db, "ALICE")
    assert err.value.fields["name"] == (
        "ALICE is a user. Pick that user from the list or use a different name."
    )
    assert service.validate_name(tmp_db, "ALICE", except_id=created.id) == "ALICE"


@pytest.mark.parametrize("user_id", ["", "abc", "99", "-1", "1.5", "9" * 20])
def test_sign_in_rejects_unknown_user(tmp_db: sqlite3.Connection, user_id: str) -> None:
    with pytest.raises(ValidationFailed) as err:
        service.sign_in(tmp_db, user_id, "")
    assert err.value.fields == {"user_id": service.CHOOSE_ERROR}


def test_sign_in_picks_existing_user(tmp_db: sqlite3.Connection) -> None:
    created = service.sign_in(tmp_db, "__new", "Bob")
    assert service.sign_in(tmp_db, str(created.id), "ignored") == created
