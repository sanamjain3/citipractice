import logging
from datetime import timedelta
from decimal import Decimal

from sqlalchemy.orm import Session

from app.models import Transaction, TransactionStatus, utcnow
from app.repository import TransactionRepository
from app.services import assess_risk

logger = logging.getLogger("app.seed")

# (account_id, amount, currency, decision already taken or None)
# Picked to cover both sides of the threshold, the exact boundary, and every status.
SAMPLE_TRANSACTIONS: list[tuple[str, str, str, TransactionStatus | None]] = [
    ("ACC-1001", "250.00", "USD", None),                         # PENDING
    ("ACC-1002", "12500.00", "USD", None),                       # FLAGGED
    ("ACC-1003", "980.50", "EUR", TransactionStatus.APPROVED),
    ("ACC-1004", "45000.00", "USD", None),                       # FLAGGED
    ("ACC-1005", "75.25", "GBP", TransactionStatus.REJECTED),
    ("ACC-1006", "9999.99", "USD", None),                        # PENDING, just under threshold
    ("ACC-1007", "10000.00", "USD", TransactionStatus.APPROVED), # exactly at threshold: not flagged
    ("ACC-1008", "18250.00", "EUR", TransactionStatus.REJECTED), # flagged, then rejected
]


def seed_transactions(session: Session, flag_threshold: Decimal) -> int:
    """Insert the sample records if the table is empty. Returns how many were inserted."""
    repository = TransactionRepository(session)
    if repository.count() > 0:
        return 0

    now = utcnow()
    records = []
    for index, (account_id, amount, currency, decision) in enumerate(SAMPLE_TRANSACTIONS):
        value = Decimal(amount)
        status, reason = assess_risk(value, flag_threshold)
        records.append(
            Transaction(
                account_id=account_id,
                amount=value,
                currency=currency,
                status=decision or status,
                risk_reason=reason,
                created_at=now - timedelta(hours=index),
            )
        )
    repository.add_all(records)
    repository.commit()
    logger.info("seeded sample transactions", extra={"count": len(records)})
    return len(records)
