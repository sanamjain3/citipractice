from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.dependencies import get_transaction_service
from app.models import TransactionStatus
from app.schemas import TransactionCreate, TransactionRead, TransactionSummary
from app.services import InvalidTransitionError, TransactionNotFoundError, TransactionService

router = APIRouter(prefix="/transactions", tags=["transactions"])


@router.get("", response_model=list[TransactionRead])
def list_transactions(
    status_filter: TransactionStatus | None = Query(default=None, alias="status"),
    account_id: str | None = Query(default=None, max_length=64),
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    service: TransactionService = Depends(get_transaction_service),
):
    return service.list(status=status_filter, account_id=account_id, limit=limit, offset=offset)


# Declared before /{transaction_id} so "summary" is not captured as an id.
@router.get("/summary", response_model=TransactionSummary)
def get_summary(service: TransactionService = Depends(get_transaction_service)):
    return service.summary()


@router.post("", response_model=TransactionRead, status_code=status.HTTP_201_CREATED)
def create_transaction(payload: TransactionCreate, service: TransactionService = Depends(get_transaction_service)):
    return service.create(payload)


@router.get("/{transaction_id}", response_model=TransactionRead)
def get_transaction(transaction_id: str, service: TransactionService = Depends(get_transaction_service)):
    try:
        return service.get(transaction_id)
    except TransactionNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc


@router.post("/{transaction_id}/approve", response_model=TransactionRead)
def approve_transaction(transaction_id: str, service: TransactionService = Depends(get_transaction_service)):
    return _decide(service.approve, transaction_id)


@router.post("/{transaction_id}/reject", response_model=TransactionRead)
def reject_transaction(transaction_id: str, service: TransactionService = Depends(get_transaction_service)):
    return _decide(service.reject, transaction_id)


def _decide(action, transaction_id: str):
    try:
        return action(transaction_id)
    except TransactionNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc
    except InvalidTransitionError as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, str(exc)) from exc
