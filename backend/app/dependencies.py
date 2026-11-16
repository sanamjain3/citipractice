from collections.abc import Iterator

from fastapi import Depends, Request
from sqlalchemy.orm import Session

from app.config import Settings
from app.database import Database
from app.repository import TransactionRepository
from app.services import TransactionService


def get_app_settings(request: Request) -> Settings:
    return request.app.state.settings


def get_database(request: Request) -> Database:
    return request.app.state.db


def get_session(db: Database = Depends(get_database)) -> Iterator[Session]:
    session = db.session_factory()
    try:
        yield session
    finally:
        session.close()  # rolls back anything not committed


def get_transaction_service(
    session: Session = Depends(get_session),
    settings: Settings = Depends(get_app_settings),
) -> TransactionService:
    return TransactionService(TransactionRepository(session), settings.flag_threshold)
