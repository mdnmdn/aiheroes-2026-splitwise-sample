"""Money: integer minor units, display text and the equal split. No floats."""

import re

DEFAULT_DECIMALS = 2
CURRENCY_DECIMALS = {
    "BIF": 0, "CLP": 0, "DJF": 0, "GNF": 0, "ISK": 0, "JPY": 0, "KMF": 0, "KRW": 0,
    "PYG": 0, "RWF": 0, "UGX": 0, "VND": 0, "VUV": 0, "XAF": 0, "XOF": 0, "XPF": 0,
    "BHD": 3, "IQD": 3, "JOD": 3, "KWD": 3, "LYD": 3, "OMR": 3, "TND": 3,
}  # fmt: skip
CURRENCY_SYMBOLS = {
    "EUR": "€", "USD": "$", "GBP": "£", "CHF": "CHF", "JPY": "¥", "CAD": "CA$", "AUD": "A$",
    "SEK": "SEK", "NOK": "NOK", "DKK": "DKK", "PLN": "PLN", "CZK": "CZK", "INR": "₹",
    "BRL": "R$", "MXN": "MX$",
}  # fmt: skip
CURRENCIES = tuple(CURRENCY_SYMBOLS)  # the 15 base currencies of a group
MINUS = "\u2212"
_AMOUNT_RE = re.compile(r"^([0-9]+)(?:\.([0-9]+))?$")
MAX_MAJOR = 100_000_000  # the integer part must be less than this


def decimals(currency: str) -> int:
    return CURRENCY_DECIMALS.get(currency.upper(), DEFAULT_DECIMALS)


def format_amount(minor: int, currency: str) -> str:
    """Minor units to text with a thousands separator, for example 123456 EUR -> 1,234.56."""
    places = decimals(currency)
    sign = "-" if minor < 0 else ""
    whole, frac = divmod(abs(minor), 10**places)
    text = f"{whole:,}"
    return f"{sign}{text}.{frac:0{places}d}" if places else f"{sign}{text}"


def format_money(minor: int, currency: str) -> str:
    return f"{format_amount(minor, currency)} {currency.upper()}"


def symbol(currency: str) -> str:
    return CURRENCY_SYMBOLS.get(currency.upper(), currency.upper())


def format_signed(minor: int, currency: str) -> str:
    """With a sign and a real minus: +12.00 EUR, −5.00 EUR, 0.00 EUR."""
    if minor > 0:
        return "+" + format_money(minor, currency)
    if minor < 0:
        return MINUS + format_money(-minor, currency)
    return format_money(0, currency)


def balance_label(minor: int) -> str:
    return "is owed" if minor > 0 else "owes" if minor < 0 else "settled"


def parse_amount(text: str, currency: str) -> int:
    """Text to minor units, with no float. Raises ValueError with the message of the field error.

    Rules: _docs/features/expenses.md "Amount input". Accepts 12, 12.5 and 12,50.
    """
    cleaned = "".join(text.split()).replace(",", ".", 1)
    if not cleaned:
        raise ValueError("Enter an amount.")
    match = _AMOUNT_RE.match(cleaned)
    if not match:
        raise ValueError("Use digits only, for example 12.50.")
    whole, frac = match.group(1).lstrip("0") or "0", match.group(2) or ""
    places = decimals(currency)
    if len(frac) > places:
        if not places:
            raise ValueError("This currency has no decimals.")
        raise ValueError(f"Use at most {places} decimals.")
    if len(whole) > len(str(MAX_MAJOR - 1)) or int(whole) >= MAX_MAJOR:
        raise ValueError("The amount is too large.")
    minor = int(whole) * 10**places + int(frac.ljust(places, "0") or 0)
    if minor <= 0:
        raise ValueError("The amount must be more than zero.")
    return minor


def to_input(minor: int, currency: str) -> str:
    """Minor units to a plain value for an input field: 1234 EUR -> 12.34."""
    places = decimals(currency)
    whole, frac = divmod(abs(minor), 10**places)
    sign = "-" if minor < 0 else ""
    return f"{sign}{whole}.{frac:0{places}d}" if places else f"{sign}{whole}"


def split_equal(amount_minor: int, n: int) -> list[int]:
    """Split into n shares. The remainder goes one unit each to the first shares (join order)."""
    if n < 1:
        raise ValueError("n must be at least 1")
    if amount_minor < 0:
        raise ValueError("amount must not be negative")
    base, rest = divmod(amount_minor, n)
    return [base + (1 if i < rest else 0) for i in range(n)]
