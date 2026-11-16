import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import Settings, get_settings
from app.database import Database
from app.logging_config import configure_logging
from app.middleware import RequestLoggingMiddleware
from app.routers import health, transactions
from app.seed import seed_transactions

logger = logging.getLogger("app")


def create_app(settings: Settings | None = None) -> FastAPI:
    """App factory: tests pass their own Settings (e.g. an in-memory database)."""
    settings = settings or get_settings()
    configure_logging(settings.log_level)
    db = Database(settings.database_url)

    @asynccontextmanager
    async def lifespan(_: FastAPI):
        db.create_all()
        if settings.seed_on_startup:
            with db.session_factory() as session:
                seed_transactions(session, settings.flag_threshold)
        logger.info("startup complete", extra={"database": db.engine.url.render_as_string(hide_password=True)})
        yield
        db.dispose()

    app = FastAPI(title=settings.app_name, version="0.1.0", lifespan=lifespan)
    app.state.settings = settings
    app.state.db = db

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_methods=["GET", "POST"],
        allow_headers=["Content-Type", "X-Request-ID"],
        expose_headers=["X-Request-ID"],
    )
    # Added last so it is the outermost layer and times the whole request.
    app.add_middleware(RequestLoggingMiddleware)

    app.include_router(health.router)
    app.include_router(transactions.router, prefix="/api")
    return app


app = create_app()
