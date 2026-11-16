import enum
import uuid
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import DateTime, Enum, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class TransactionStatus(str, enum.Enum):
    PENDING = "PENDING"
    FLAGGED = "FLAGGED"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Transaction(Base):
    __tablename__ = "transactions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    account_id: Mapped[str] = mapped_column(String(64), index=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(14, 2))
    currency: Mapped[str] = mapped_column(String(3))
    status: Mapped[TransactionStatus] = mapped_column(
        # Stored as VARCHAR + CHECK so it behaves the same on SQLite and PostgreSQL.
        Enum(TransactionStatus, name="transaction_status", native_enum=False, length=16),
        index=True,
    )
    risk_reason: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, index=True)

    def __repr__(self) -> str:
        return f"<Transaction {self.id} {self.amount} {self.currency} {self.status.value}>"
