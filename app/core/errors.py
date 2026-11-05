"""Domain errors and the handlers that map them to HTTP. See _docs/tech/practices.md section 3."""

from typing import Any
from urllib.parse import quote

import structlog
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, RedirectResponse, Response
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.htmx import is_htmx
from app.core.templating import templates

log = structlog.get_logger()


class AppError(Exception):
    status = 500
    code = "internal_error"

    def __init__(self, message: str = "", fields: dict[str, str] | None = None) -> None:
        super().__init__(message)
        self.message = message or self.__class__.__name__
        self.fields = fields or {}


class ValidationFailed(AppError):
    status = 422
    code = "validation_failed"


class NotFound(AppError):
    status = 404
    code = "not_found"


class Conflict(AppError):
    status = 409
    code = "conflict"


class NotSignedIn(AppError):
    status = 401
    code = "not_signed_in"


def _envelope(code: str, message: str, fields: dict[str, str]) -> dict[str, Any]:
    return {"error": {"code": code, "message": message, "fields": fields}}


def _login_url(request: Request) -> str:
    path = request.url.path
    if request.url.query:
        path += "?" + request.url.query
    return f"/login?next={quote(path, safe='/')}"


def _respond(
    request: Request, status: int, code: str, message: str, fields: dict[str, str]
) -> Response:
    if request.url.path.startswith("/api/"):
        return JSONResponse(_envelope(code, message, fields), status_code=status)
    context = {"status": status, "code": code, "message": message, "fields": fields}
    context["request_id"] = getattr(request.state, "request_id", "")
    if is_htmx(request):
        return templates.TemplateResponse(
            request, "partials/core/error.html", context, status_code=status
        )
    return templates.TemplateResponse(request, "pages/error.html", context, status_code=status)


def _not_signed_in(request: Request) -> Response:
    if request.url.path.startswith("/api/"):
        return JSONResponse(_envelope("not_signed_in", "Sign in first", {}), status_code=401)
    url = _login_url(request)
    if is_htmx(request):
        return Response(status_code=200, headers={"HX-Redirect": url})
    return RedirectResponse(url, status_code=303)


def _field_name(loc: tuple[Any, ...]) -> str:
    """The last name in the location of an error. An index or no name gives "body"."""
    skip = ("body", "query", "path")
    names = [part for part in loc if isinstance(part, str) and part not in skip]
    return names[-1] if names else "body"


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(NotSignedIn)
    async def on_not_signed_in(request: Request, exc: NotSignedIn) -> Response:
        return _not_signed_in(request)

    @app.exception_handler(AppError)
    async def on_app_error(request: Request, exc: AppError) -> Response:
        return _respond(request, exc.status, exc.code, exc.message, exc.fields)

    @app.exception_handler(RequestValidationError)
    async def on_request_validation(request: Request, exc: RequestValidationError) -> Response:
        fields = {_field_name(e["loc"]): str(e["msg"]) for e in exc.errors()}
        return _respond(request, 422, "validation_failed", "Input is not valid", fields)

    @app.exception_handler(StarletteHTTPException)
    async def on_http_exception(request: Request, exc: StarletteHTTPException) -> Response:
        code = "not_found" if exc.status_code == 404 else "http_error"
        return _respond(request, exc.status_code, code, str(exc.detail), {})

    @app.exception_handler(Exception)
    async def on_unhandled(request: Request, exc: Exception) -> Response:
        request_id = getattr(request.state, "request_id", "")
        log.error("request.failed", request_id=request_id, exc_info=exc)
        return _respond(request, 500, "internal_error", "Something went wrong", {})
