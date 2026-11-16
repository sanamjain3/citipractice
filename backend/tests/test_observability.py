import json
import logging

from app.logging_config import JsonFormatter


def test_health_ok(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "database": "ok"}


def test_health_reports_database_failure(client, monkeypatch):
    def broken_ping():
        raise RuntimeError("db down")

    monkeypatch.setattr(client.app.state.db, "ping", broken_ping)
    response = client.get("/health")
    assert response.status_code == 503
    assert response.json()["database"] == "unreachable"


def _request_logs(caplog):
    return [r for r in caplog.records if r.name == "app.request"]


def test_request_is_logged_with_required_fields(client, caplog):
    with caplog.at_level(logging.INFO, logger="app.request"):
        response = client.get("/api/transactions/missing")

    records = _request_logs(caplog)
    assert len(records) == 1
    record = records[0]
    assert record.method == "GET"
    assert record.path == "/api/transactions/missing"
    assert record.status_code == 404
    assert isinstance(record.duration_ms, float) and record.duration_ms >= 0
    assert record.request_id == response.headers["X-Request-ID"]
    assert len(record.request_id) == 32


def test_incoming_request_id_is_propagated(client, caplog):
    with caplog.at_level(logging.INFO, logger="app.request"):
        response = client.get("/health", headers={"X-Request-ID": "trace-abc.123"})

    assert response.headers["X-Request-ID"] == "trace-abc.123"
    assert _request_logs(caplog)[0].request_id == "trace-abc.123"


def test_unsafe_request_id_is_replaced(client):
    response = client.get("/health", headers={"X-Request-ID": "bad id\twith spaces"})
    assert response.headers["X-Request-ID"] != "bad id\twith spaces"
    assert len(response.headers["X-Request-ID"]) == 32


def test_json_formatter_includes_extra_fields():
    record = logging.LogRecord("app.request", logging.INFO, __file__, 1, "request completed", (), None)
    record.request_id = "abc"
    record.status_code = 200
    payload = json.loads(JsonFormatter().format(record))
    assert payload["message"] == "request completed"
    assert payload["request_id"] == "abc"
    assert payload["status_code"] == 200
    assert payload["level"] == "INFO"
