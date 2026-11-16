from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import Transaction, TransactionStatus


class TransactionRepository:
    """Data access only. No business rules live here."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def add(self, transaction: Transaction) -> Transaction:
        self.session.add(transaction)
        self.session.flush()
        return transaction

    def add_all(self, transactions: list[Transaction]) -> None:
        self.session.add_all(transactions)
        self.session.flush()

    def get(self, transaction_id: str) -> Transaction | None:
        return self.session.get(Transaction, transaction_id)

    def list(
        self,
        status: TransactionStatus | None = None,
        account_id: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Transaction]:
        stmt = select(Transaction).order_by(Transaction.created_at.desc(), Transaction.id)
        if status is not None:
            stmt = stmt.where(Transaction.status == status)
        if account_id:
            stmt = stmt.where(Transaction.account_id == account_id)
        return list(self.session.scalars(stmt.limit(limit).offset(offset)))

    def count(self) -> int:
        return self.session.scalar(select(func.count()).select_from(Transaction)) or 0

    def count_by_status(self) -> dict[TransactionStatus, int]:
        rows = self.session.execute(select(Transaction.status, func.count()).group_by(Transaction.status))
        return {status: count for status, count in rows}

    def total_amount_by_currency(self) -> dict[str, Decimal]:
        rows = self.session.execute(
            select(Transaction.currency, func.sum(Transaction.amount))
            .group_by(Transaction.currency)
            .order_by(Transaction.currency)
        )
        return {currency: Decimal(total or 0) for currency, total in rows}

    def commit(self) -> None:
        self.session.commit()
