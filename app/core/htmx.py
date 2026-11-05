"""HTMX helpers: request check, HX-Trigger events and toasts."""

import json
from typing import Any
from urllib.parse import quote

from fastapi import Request
from fastapi.responses import HTMLResponse, RedirectResponse, Response


def is_htmx(request: Request) -> bool:
    return request.headers.get("HX-Request") == "true"


def toast(message: str) -> dict[str, Any]:
    """Event dict for the toast area that app.js owns."""
    return {"toast": {"message": message}}


def set_events(response: Response, events: dict[str, Any]) -> Response:
    """Set HX-Trigger. An event maps to its detail dict: {"ledger-changed": {}}."""
    if events:
        response.headers["HX-Trigger"] = json.dumps(events)
    return response


def htmx_response(
    content: str | Response, events: dict[str, Any] | None = None, status: int = 200
) -> Response:
    """Fragment response with HX-Trigger events."""
    response = HTMLResponse(content, status_code=status) if isinstance(content, str) else content
    return set_events(response, events or {})


FLASH_COOKIE = "sw_flash"


def flash(response: Response, message: str) -> Response:
    """Keep a message across a redirect. The next page shows it as a toast."""
    response.set_cookie(FLASH_COOKIE, quote(message), max_age=60, httponly=True, samesite="lax")
    return response


def mutation_response(
    response: Response | None = None,
    *,
    message: str = "",
    events: dict[str, Any] | None = None,
    close_dialog: bool = True,
    status: int = 200,
) -> Response:
    """Answer of a successful dialog mutation: no swap of the form, events for the page.

    The body can hold out-of-band fragments. Regions that listen to an event reload themselves.
    """
    response = response or Response(status_code=status)
    all_events: dict[str, Any] = {}
    if message:
        all_events.update(toast(message))
    if close_dialog:
        all_events["close-dialog"] = {}
    all_events.update(events or {})
    response.headers["HX-Reswap"] = "none"
    return set_events(response, all_events)


def location_header(url: str) -> str:
    """HX-Location value: an htmx navigation that keeps the user header of the tab."""
    return json.dumps({"path": url, "target": "body", "swap": "innerHTML"})


def redirect_to(request: Request, url: str, message: str = "", status: int = 200) -> Response:
    """Go to a page. HTMX gets HX-Location, a plain request gets 303. The message is a flash."""
    if is_htmx(request):
        response: Response = Response(status_code=status)
        response.headers["HX-Location"] = location_header(url)
    else:
        response = RedirectResponse(url, status_code=303)
    return flash(response, message) if message else response


def fragment_only(request: Request, page_url: str) -> Response | None:
    """A fragment URL opened as a page goes to the page that holds the fragment."""
    return None if is_htmx(request) else RedirectResponse(page_url, status_code=303)
