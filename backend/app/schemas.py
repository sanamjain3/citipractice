from datetime import datetime, timezone
from decimal import Decimal
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, PlainSerializer, field_validator

from app.models import TransactionStatus

# Exact Decimal internally; plain JSON number on the wire so clients don't parse strings.
Money = Annotated[Decimal, PlainSerializer(float, return_type=float, when_used="json")]


class TransactionCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    account_id: str = Field(min_length=1, max_length=64, examples=["ACC-1001"])
    amount: Decimal = Field(gt=0, max_digits=14, decimal_places=2, examples=[2500.00])
    currency: str = Field(default="USD", pattern=r"^[A-Za-z]{3}$", examples=["USD"])

    @field_validator("currency")
    @classmethod
    def uppercase_currency(cls, value: str) -> str:
        return value.upper()


class TransactionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    account_id: str
    amount: Money
    currency: str
    status: TransactionStatus
    risk_reason: str | None
    created_at: datetime

    @field_validator("created_at")
    @classmethod
    def assume_utc(cls, value: datetime) -> datetime:
        # SQLite drops tzinfo; all timestamps are written in UTC.
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)


class TransactionSummary(BaseModel):
    total_count: int
    pending: int
    flagged: int
    approved: int
    rejected: int
    total_amount_by_currency: dict[str, Money]


class HealthResponse(BaseModel):
    status: str
    database: str
