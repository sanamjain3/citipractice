from decimal import Decimal

from app.models import Transaction, TransactionStatus
from app.repository import TransactionRepository
from app.schemas import TransactionCreate, TransactionSummary

# Only transactions still awaiting a decision can be approved or rejected.
DECIDABLE_STATUSES = {TransactionStatus.PENDING, TransactionStatus.FLAGGED}


class TransactionNotFoundError(Exception):
    def __init__(self, transaction_id: str) -> None:
        super().__init__(f"Transaction {transaction_id} not found")
        self.transaction_id = transaction_id


class InvalidTransitionError(Exception):
    def __init__(self, transaction: Transaction, target: TransactionStatus) -> None:
        super().__init__(
            f"Transaction {transaction.id} is already {transaction.status.value} "
            f"and cannot be moved to {target.value}"
        )


def assess_risk(amount: Decimal, threshold: Decimal) -> tuple[TransactionStatus, str | None]:
    """The single business rule: amounts strictly over the threshold need manual review."""
    if amount > threshold:
        return TransactionStatus.FLAGGED, f"Amount {amount:,.2f} exceeds review threshold of {threshold:,.2f}"
    return TransactionStatus.PENDING, None


class TransactionService:
    def __init__(self, repository: TransactionRepository, flag_threshold: Decimal) -> None:
        self.repository = repository
        self.flag_threshold = flag_threshold

    def create(self, data: TransactionCreate) -> Transaction:
        status, reason = assess_risk(data.amount, self.flag_threshold)
        transaction = Transaction(
            account_id=data.account_id,
            amount=data.amount,
            currency=data.currency,
            status=status,
            risk_reason=reason,
        )
        self.repository.add(transaction)
        self.repository.commit()
        return transaction

    def get(self, transaction_id: str) -> Transaction:
        transaction = self.repository.get(transaction_id)
        if transaction is None:
            raise TransactionNotFoundError(transaction_id)
        return transaction

    def list(
        self,
        status: TransactionStatus | None = None,
        account_id: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Transaction]:
        return self.repository.list(status=status, account_id=account_id, limit=limit, offset=offset)

    def approve(self, transaction_id: str) -> Transaction:
        return self._decide(transaction_id, TransactionStatus.APPROVED)

    def reject(self, transaction_id: str) -> Transaction:
        return self._decide(transaction_id, TransactionStatus.REJECTED)

    def summary(self) -> TransactionSummary:
        counts = self.repository.count_by_status()
        return TransactionSummary(
            total_count=sum(counts.values()),
            pending=counts.get(TransactionStatus.PENDING, 0),
            flagged=counts.get(TransactionStatus.FLAGGED, 0),
            approved=counts.get(TransactionStatus.APPROVED, 0),
            rejected=counts.get(TransactionStatus.REJECTED, 0),
            total_amount_by_currency=self.repository.total_amount_by_currency(),
        )

    def _decide(self, transaction_id: str, target: TransactionStatus) -> Transaction:
        transaction = self.get(transaction_id)
        if transaction.status not in DECIDABLE_STATUSES:
            raise InvalidTransitionError(transaction, target)
        transaction.status = target
        self.repository.commit()
        return transaction
