"""Jinja2 templates and filters. The filters delegate to money.py. Templates never compute."""

from datetime import date
from pathlib import Path
from typing import Any
from urllib.parse import unquote

from fastapi import Request
from fastapi.responses import Response
from fastapi.templating import Jinja2Templates

from app.core import money
from app.core.htmx import FLASH_COOKIE
from app.core.limits import DESCRIPTION_MAX, GROUP_NAME_MAX, NOTE_MAX, USER_NAME_MAX
from app.users.schemas import NEW_USER

TEMPLATES_DIR = Path(__file__).resolve().parent.parent / "templates"

templates = Jinja2Templates(directory=TEMPLATES_DIR)


def money_filter(minor: int, currency: str) -> str:
    return money.format_money(minor, currency)


def amount_filter(minor: int, currency: str) -> str:
    return money.format_amount(minor, currency)


def signed_money_filter(minor: int, currency: str) -> str:
    return money.format_signed(minor, currency)


def date_filter(iso: str) -> str:
    """'2026-11-05' -> '5 Nov 2026'."""
    d = date.fromisoformat(iso)
    return f"{d.day} {d.strftime('%b')} {d.year}"


templates.env.globals.update(
    NEW_USER=NEW_USER,
    GROUP_NAME_MAX=GROUP_NAME_MAX,
    USER_NAME_MAX=USER_NAME_MAX,
    DESCRIPTION_MAX=DESCRIPTION_MAX,
    NOTE_MAX=NOTE_MAX,
)
templates.env.filters["money"] = money_filter
templates.env.filters["amount"] = amount_filter
templates.env.filters["date"] = date_filter
templates.env.filters["signed_money"] = signed_money_filter
templates.env.filters["symbol"] = money.symbol
templates.env.filters["balance_label"] = money.balance_label


def render(
    request: Request, name: str, context: dict[str, Any] | None = None, status_code: int = 200
) -> Response:
    """Render a page. A flash message from the cookie goes into the page, then the cookie ends."""
    context = dict(context or {})
    flash = request.cookies.get(FLASH_COOKIE)
    if flash:
        context["flash"] = unquote(flash)
    response = templates.TemplateResponse(request, name, context, status_code=status_code)
    if flash:
        response.delete_cookie(FLASH_COOKIE)
    return response
