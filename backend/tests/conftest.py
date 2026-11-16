from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app


def make_settings(**overrides) -> Settings:
    # _env_file=None keeps tests independent of whatever is in backend/.env.
    values = {"database_url": "sqlite://", "seed_on_startup": False, "log_level": "DEBUG"}
    values.update(overrides)
    return Settings(_env_file=None, **values)


@pytest.fixture
def client() -> Iterator[TestClient]:
    """Fresh, empty in-memory database per test."""
    with TestClient(create_app(make_settings())) as test_client:
        yield test_client


@pytest.fixture
def seeded_client() -> Iterator[TestClient]:
    """Fresh in-memory database with the 8 startup sample records."""
    with TestClient(create_app(make_settings(seed_on_startup=True))) as test_client:
        yield test_client


@pytest.fixture
def create_tx(client: TestClient):
    def _create(amount: float, account_id: str = "ACC-TEST", currency: str = "USD") -> dict:
        response = client.post(
            "/api/transactions", json={"account_id": account_id, "amount": amount, "currency": currency}
        )
        assert response.status_code == 201, response.text
        return response.json()

    return _create
