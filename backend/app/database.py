from sqlalchemy import create_engine, text
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from sqlalchemy.pool import StaticPool


class Base(DeclarativeBase):
    pass


class Database:
    """Owns the engine and session factory for one database URL.

    Only the URL changes between SQLite and PostgreSQL; everything else is portable SQLAlchemy.
    """

    def __init__(self, url: str) -> None:
        kwargs: dict = {}
        if url.startswith("sqlite"):
            # FastAPI runs sync endpoints in a threadpool, so allow cross-thread use.
            kwargs["connect_args"] = {"check_same_thread": False}
            if url in ("sqlite://", "sqlite:///:memory:"):
                # One shared connection so an in-memory DB survives across sessions (tests).
                kwargs["poolclass"] = StaticPool
        else:
            kwargs["pool_pre_ping"] = True
        self.engine = create_engine(url, **kwargs)
        self.session_factory = sessionmaker(bind=self.engine, autoflush=False, expire_on_commit=False)

    def create_all(self) -> None:
        # Import models so they are registered on Base.metadata.
        from app import models  # noqa: F401

        Base.metadata.create_all(self.engine)

    def ping(self) -> bool:
        with self.engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True

    def dispose(self) -> None:
        self.engine.dispose()
