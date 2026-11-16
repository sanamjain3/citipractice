from decimal import Decimal

import pytest

from app.models import TransactionStatus
from app.services import assess_risk

THRESHOLD = Decimal("10000")


@pytest.mark.parametrize(
    "amount, expected",
    [
        ("0.01", TransactionStatus.PENDING),
        ("9999.99", TransactionStatus.PENDING),
        ("10000.00", TransactionStatus.PENDING),  # "over 10000" is strict
        ("10000.01", TransactionStatus.FLAGGED),
        ("250000.00", TransactionStatus.FLAGGED),
    ],
)
def test_assess_risk_threshold(amount: str, expected: TransactionStatus):
    status, reason = assess_risk(Decimal(amount), THRESHOLD)
    assert status == expected
    assert (reason is not None) == (expected == TransactionStatus.FLAGGED)


def test_flag_reason_mentions_amount_and_threshold():
    _, reason = assess_risk(Decimal("12500"), THRESHOLD)
    assert reason == "Amount 12,500.00 exceeds review threshold of 10,000.00"
