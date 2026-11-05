import pytest

from app.core import money


@pytest.mark.parametrize(
    ("amount", "n", "expected"),
    [
        (1000, 3, [334, 333, 333]),
        (1, 3, [1, 0, 0]),
        (2, 3, [1, 1, 0]),
        (100, 4, [25, 25, 25, 25]),
        (0, 3, [0, 0, 0]),
        (500, 1, [500]),
        (10**15 + 1, 2, [5 * 10**14 + 1, 5 * 10**14]),
    ],
)
def test_split_equal(amount: int, n: int, expected: list[int]) -> None:
    shares = money.split_equal(amount, n)
    assert shares == expected
    assert sum(shares) == amount


def test_split_equal_jpy_has_no_decimals() -> None:
    assert money.split_equal(100, 3) == [34, 33, 33]
    assert money.format_amount(100, "JPY") == "100"


def test_split_equal_rejects_bad_input() -> None:
    with pytest.raises(ValueError):
        money.split_equal(100, 0)
    with pytest.raises(ValueError):
        money.split_equal(-1, 2)


@pytest.mark.parametrize(
    ("minor", "currency", "text"),
    [
        (1000, "EUR", "10.00"),
        (1, "EUR", "0.01"),
        (123456789, "USD", "1,234,567.89"),
        (-250, "EUR", "-2.50"),
        (1500, "JPY", "1,500"),
        (12345, "KWD", "12.345"),
    ],
)
def test_format_amount(minor: int, currency: str, text: str) -> None:
    assert money.format_amount(minor, currency) == text


def test_format_money_adds_currency_code() -> None:
    assert money.format_money(1050, "eur") == "10.50 EUR"


@pytest.mark.parametrize(
    ("text", "currency", "minor"),
    [
        ("10", "EUR", 1000),
        ("10.5", "EUR", 1050),
        ("10,50", "EUR", 1050),
        (" 0.01 ", "EUR", 1),
        ("500", "JPY", 500),
        ("1.234", "KWD", 1234),
    ],
)
def test_parse_amount(text: str, currency: str, minor: int) -> None:
    assert money.parse_amount(text, currency) == minor


@pytest.mark.parametrize(
    ("text", "currency", "message"),
    [
        ("", "EUR", "Enter an amount."),
        ("   ", "EUR", "Enter an amount."),
        ("abc", "EUR", "Use digits only, for example 12.50."),
        ("-5", "EUR", "Use digits only, for example 12.50."),
        ("12.", "EUR", "Use digits only, for example 12.50."),
        ("1.234", "EUR", "Use at most 2 decimals."),
        ("1.5", "JPY", "This currency has no decimals."),
        ("100000000", "EUR", "The amount is too large."),
        ("0", "EUR", "The amount must be more than zero."),
        ("0.00", "EUR", "The amount must be more than zero."),
    ],
)
def test_parse_amount_rejects(text: str, currency: str, message: str) -> None:
    with pytest.raises(ValueError, match=message.replace(".", r"\.")):
        money.parse_amount(text, currency)


def test_parse_amount_largest_and_spaces() -> None:
    assert money.parse_amount("99999999.99", "EUR") == 9_999_999_999
    assert money.parse_amount("1 250,5", "EUR") == 125050


def test_to_input_round_trips() -> None:
    assert money.to_input(1050, "EUR") == "10.50"
    assert money.parse_amount(money.to_input(7, "EUR"), "EUR") == 7


def test_signed_format_uses_a_real_minus() -> None:
    assert money.format_signed(1200, "EUR") == "+12.00 EUR"
    assert money.format_signed(-500, "EUR") == "−5.00 EUR"
    assert money.format_signed(0, "EUR") == "0.00 EUR"
    assert money.format_signed(-5, "JPY") == "−5 JPY"


def test_balance_label() -> None:
    assert [money.balance_label(v) for v in (1, -1, 0)] == ["is owed", "owes", "settled"]


def test_the_15_currencies_have_a_symbol() -> None:
    assert len(money.CURRENCIES) == 15
    assert money.CURRENCIES[0] == "EUR"
    assert money.symbol("EUR") == "€"
    assert money.symbol("ZZZ") == "ZZZ"


def test_parse_amount_rejects_huge_digit_text_without_python_limit_text() -> None:
    for text in ("9" * 5000, "9" * 5000 + ".5", "1" + "0" * 4999):
        with pytest.raises(ValueError, match=r"^The amount is too large\.$"):
            money.parse_amount(text, "EUR")
    assert money.parse_amount("0" * 5000 + "12", "EUR") == 1200


def test_date_filter_pads_nothing_for_small_years() -> None:
    from app.core.templating import date_filter

    assert date_filter("0001-01-01") == "1 Jan 1"
    assert date_filter("2026-11-05") == "5 Nov 2026"
