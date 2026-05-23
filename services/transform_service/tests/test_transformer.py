import pytest

from transform_service.models import TransformedRecord
from transform_service import transformer
from transform_service.transformer import transform_record


@pytest.fixture
def saved_records(monkeypatch):
    records = []

    def save_transformed_record(record):
        records.append(record)
        return record

    monkeypatch.setattr(transformer, "save_transformed_record", save_transformed_record)
    return records


def test_transform_record_returns_transformed_record(saved_records):
    raw_data = {
        "event_id": "evt-123",
        "tenant_id": "tenant-a",
        "action": "download",
        "package": "example-package",
        "version": "1.0.0",
        "timestamp": "2026-05-23T00:00:00Z",
        "actor": "aidan",
    }

    record = transform_record(raw_data)

    assert record == TransformedRecord(
        event_id="evt-123",
        tenant_id="tenant-a",
        action="download",
        package="example-package",
        version="1.0.0",
        timestamp="2026-05-23T00:00:00Z",
        actor="aidan",
    )
    assert saved_records == [record]


def test_transform_record_coerces_present_values_to_strings(saved_records):
    raw_data = {
        "event_id": 123,
        "tenant_id": 456,
        "action": "download",
        "package": "example-package",
        "version": 1.2,
        "timestamp": "2026-05-23T00:00:00Z",
        "actor": 789,
    }

    record = transform_record(raw_data)

    assert record.event_id == "123"
    assert record.tenant_id == "456"
    assert record.version == "1.2"
    assert record.actor == "789"
    assert saved_records == [record]


def test_transform_record_preserves_optional_null_fields(saved_records):
    raw_data = {
        "event_id": None,
        "tenant_id": "tenant-a",
        "action": "download",
        "package": "example-package",
        "version": "1.0.0",
        "timestamp": "2026-05-23T00:00:00Z",
        "actor": None,
    }

    record = transform_record(raw_data)

    assert record.event_id is None
    assert record.actor is None
    assert record.timestamp == "2026-05-23T00:00:00Z"
    assert saved_records == [record]


def test_transform_record_defaults_missing_fields_to_empty_strings(saved_records):
    record = transform_record({})

    assert record == TransformedRecord(
        event_id=None,
        tenant_id="",
        action="",
        package="",
        version="",
        timestamp="",
        actor=None,
    )
    assert saved_records == [record]


@pytest.mark.parametrize(
    "bad_raw_data",
    [
        pytest.param([], id="list"),
        pytest.param((), id="tuple"),
        pytest.param("not a dict", id="string"),
        pytest.param(1, id="integer"),
        pytest.param(1.5, id="float"),
        pytest.param(True, id="boolean"),
        pytest.param(None, id="null"),
    ],
)
def test_transform_record_rejects_bad_raw_data_types(bad_raw_data, saved_records):
    with pytest.raises(TypeError, match="raw_data must be a dict"):
        transform_record(bad_raw_data)

    assert saved_records == []
