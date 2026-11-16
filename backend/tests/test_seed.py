from decimal import Decimal


def test_startup_seeds_eight_records(seeded_client):
    transactions = seeded_client.get("/api/transactions").json()
    assert len(transactions) == 8

    summary = seeded_client.get("/api/transactions/summary").json()
    assert (summary["pending"], summary["flagged"], summary["approved"], summary["rejected"]) == (2, 2, 2, 2)


def test_seeded_flags_follow_business_rule(seeded_client):
    for tx in seeded_client.get("/api/transactions").json():
        if tx["amount"] > 10000:
            assert tx["risk_reason"] is not None
        else:
            assert tx["risk_reason"] is None


def test_seed_is_idempotent(seeded_client):
    from app.seed import seed_transactions

    db = seeded_client.app.state.db
    with db.session_factory() as session:
        assert seed_transactions(session, Decimal("10000")) == 0
    assert len(seeded_client.get("/api/transactions").json()) == 8


def test_no_seed_when_disabled(client):
    assert client.get("/api/transactions").json() == []
