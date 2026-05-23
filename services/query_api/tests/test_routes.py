from fastapi.testclient import TestClient

from query_api import datastore
from query_api.main import app


client = TestClient(app)


def test_health_check_returns_ok():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_list_events_filters_by_tenant_and_optional_fields(monkeypatch):
    cleanup_calls = []
    fetch_calls = []

    def cleanup_expired_events(**kwargs):
        cleanup_calls.append(kwargs)
        return 0

    def fetch_events(**kwargs):
        fetch_calls.append(kwargs)
        return [
            {
                "event_id": "evt-1",
                "tenant_id": "tenant-a",
                "action": "download",
                "package": "example-package",
                "version": "1.0.0",
                "timestamp": "2026-05-23T10:00:00",
                "actor": "aidan",
            }
        ]

    monkeypatch.setattr(datastore, "cleanup_expired_events", cleanup_expired_events)
    monkeypatch.setattr(datastore, "fetch_events", fetch_events)

    response = client.get(
        "/events",
        params={
            "tenant": "tenant-a",
            "start_time": "2026-05-01T00:00:00",
            "end_time": "2026-05-23T23:59:59",
            "action_type": "download",
            "package_name": "example-package",
        },
    )

    assert response.status_code == 200
    assert response.json()["count"] == 1
    assert response.json()["events"][0]["event_id"] == "evt-1"
    assert cleanup_calls == []
    assert fetch_calls[0]["tenant"] == "tenant-a"
    assert fetch_calls[0]["action_type"] == "download"
    assert fetch_calls[0]["package_name"] == "example-package"


def test_list_events_rejects_invalid_time_range():
    response = client.get(
        "/events",
        params={
            "tenant": "tenant-a",
            "start_time": "2026-05-24T00:00:00",
            "end_time": "2026-05-23T00:00:00",
        },
    )

    assert response.status_code == 400
    assert response.json() == {"detail": "start_time must be before end_time"}


def test_apply_retention_policy(monkeypatch):
    def cleanup_expired_events(**kwargs):
        assert kwargs == {"tenant": "tenant-a", "retention_days": 30}
        return 3

    monkeypatch.setattr(datastore, "cleanup_expired_events", cleanup_expired_events)

    response = client.post(
        "/events/retention",
        params={"tenant": "tenant-a", "retention_days": 30},
    )

    assert response.status_code == 200
    assert response.json() == {"tenant": "tenant-a", "retention_days": 30, "deleted": 3}
