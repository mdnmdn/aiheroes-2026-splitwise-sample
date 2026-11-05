import pytest

from app.core.ids import MAX_ID, parse_id


@pytest.mark.parametrize(
    ("value", "expected"),
    [("1", 1), (" 7 ", 7), (str(MAX_ID), MAX_ID), (5, 5)],
)
def test_parse_id_valid(value, expected) -> None:
    assert parse_id(value) == expected


@pytest.mark.parametrize(
    "value", ["0", "-1", "abc", "", "1.5", "²", str(MAX_ID + 1), "9" * 40, "٣"]
)
def test_parse_id_invalid_is_zero(value) -> None:
    assert parse_id(value) == 0
