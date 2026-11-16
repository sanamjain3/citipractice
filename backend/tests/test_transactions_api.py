from datetime import datetime, timedelta

import pytest


def test_create_small_transaction_is_pending(create_tx):
    tx = create_tx(250.5)
    assert tx["status"] == "PENDING"
    assert tx["risk_reason"] is None
    assert tx["amount"] == 250.5
    assert len(tx["id"]) == 36
    assert datetime.fromisoformat(tx["created_at"]).utcoffset() == timedelta(0)


def test_create_large_transaction_is_flagged(create_tx):
    tx = create_tx(10000.01)
    assert tx["status"] == "FLAGGED"
    assert "exceeds review threshold" in tx["risk_reason"]


def test_currency_is_normalised(client):
    response = client.post("/api/transactions", json={"account_id": " ACC-9 ", "amount": 10, "currency": "eur"})
    assert response.status_code == 201
    assert response.json()["currency"] == "EUR"
    assert response.json()["account_id"] == "ACC-9"


@pytest.mark.parametrize(
    "payload",
    [
        {"account_id": "ACC-1", "amount": 0},
        {"account_id": "ACC-1", "amount": -5},
        {"account_id": "ACC-1", "amount": 10.123},
        {"account_id": "ACC-1", "amount": 10, "currency": "US"},
        {"account_id": "", "amount": 10},
        {"amount": 10},
    ],
)
def test_create_rejects_invalid_payload(client, payload):
    assert client.post("/api/transactions", json=payload).status_code == 422


def test_get_by_id_and_not_found(client, create_tx):
    tx = create_tx(100)
    assert client.get(f"/api/transactions/{tx['id']}").json() == tx
    assert client.get("/api/transactions/does-not-exist").status_code == 404


def test_list_filters_by_status_and_account(client, create_tx):
    create_tx(100, account_id="A")
    create_tx(20000, account_id="A")
    create_tx(30000, account_id="B")

    assert len(client.get("/api/transactions").json()) == 3
    flagged = client.get("/api/transactions", params={"status": "FLAGGED"}).json()
    assert {t["account_id"] for t in flagged} == {"A", "B"}
    assert len(client.get("/api/transactions", params={"account_id": "A"}).json()) == 2
    assert client.get("/api/transactions", params={"status": "BOGUS"}).status_code == 422


def test_approve_pending_and_reject_flagged(client, create_tx):
    pending = create_tx(100)
    flagged = create_tx(50000)

    approved = client.post(f"/api/transactions/{pending['id']}/approve")
    assert approved.status_code == 200
    assert approved.json()["status"] == "APPROVED"

    rejected = client.post(f"/api/transactions/{flagged['id']}/reject")
    assert rejected.status_code == 200
    assert rejected.json()["status"] == "REJECTED"
    # The original risk reason is kept for audit purposes.
    assert rejected.json()["risk_reason"] == flagged["risk_reason"]


def test_decided_transaction_cannot_change(client, create_tx):
    tx = create_tx(100)
    client.post(f"/api/transactions/{tx['id']}/approve")

    for action in ("approve", "reject"):
        response = client.post(f"/api/transactions/{tx['id']}/{action}")
        assert response.status_code == 409
        assert "already APPROVED" in response.json()["detail"]


def test_decide_unknown_transaction_is_404(client):
    assert client.post("/api/transactions/nope/approve").status_code == 404


def test_summary(client, create_tx):
    create_tx(100)
    create_tx(20000)
    to_approve = create_tx(300, currency="EUR")
    client.post(f"/api/transactions/{to_approve['id']}/approve")

    assert client.get("/api/transactions/summary").json() == {
        "total_count": 3,
        "pending": 1,
        "flagged": 1,
        "approved": 1,
        "rejected": 0,
        "total_amount_by_currency": {"EUR": 300.0, "USD": 20100.0},
    }
