"""Application factory. Wires settings, logging, middleware, routes, static files and migrations."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

import structlog
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.balances import api as balances_api
from app.balances import routes as balances_routes
from app.core.config import get_settings
from app.core.db import connect
from app.core.errors import register_error_handlers
from app.core.logging import RequestLogMiddleware, configure_logging
from app.core.migrate import migrate
from app.expenses import api as expenses_api
from app.expenses import routes as expenses_routes
from app.groups import api as groups_api
from app.groups import routes as groups_routes
from app.members import api as members_api
from app.members import routes as members_routes
from app.payments import api as payments_api
from app.payments import routes as payments_routes
from app.users import api as users_api
from app.users import routes as users_routes

STATIC_DIR = Path(__file__).resolve().parent / "static"
log = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    configure_logging(settings)
    conn = connect(settings.database_path)
    try:
        migrate(conn)
    finally:
        conn.close()
    log.info("app.started", env=settings.env, database=str(settings.database_path))
    yield
    log.info("app.stopped")


def create_app() -> FastAPI:
    get_settings()  # fail early, for example a missing secret key in prod
    app = FastAPI(title="Splitwise Lite", lifespan=lifespan)
    app.add_middleware(RequestLogMiddleware)
    register_error_handlers(app)
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

    @app.get("/healthz")
    def healthz() -> dict[str, str]:
        return {"status": "ok"}

    app.include_router(users_routes.router)
    app.include_router(groups_routes.router)
    app.include_router(members_routes.router)
    app.include_router(balances_routes.router)
    app.include_router(expenses_routes.router)
    app.include_router(payments_routes.router)
    app.include_router(users_api.router)
    app.include_router(groups_api.router)
    app.include_router(members_api.router)
    app.include_router(expenses_api.router)
    app.include_router(payments_api.router)
    app.include_router(balances_api.router)

    return app


app = create_app()
