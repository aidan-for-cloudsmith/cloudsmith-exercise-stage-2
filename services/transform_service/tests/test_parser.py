import json

import pytest

from transform_service.models import FailedRecord, TransformedRecord
from transform_service.parser import parse_raw_data


def raw(data: dict) -> str:
    return json.dumps(data)


VALID_DATA = {
    "event_id": "evt-1",
    "tenant_id": "tenant-a",
    "action": "download",
    "package": "my-package",
    "version": "1.0.0",
    "timestamp": "2026-05-24T00:00:00Z",
    "actor": "aidan",
}


def test_parse_raw_data_returns_transformed_record_for_valid_data():
    """All fields present returns a TransformedRecord."""
    record = parse_raw_data(raw(VALID_DATA))

    assert isinstance(record, TransformedRecord)
    assert record.event_id == "evt-1"
    assert record.tenant_id == "tenant-a"
    assert record.action == "download"
    assert record.package == "my-package"
    assert record.version == "1.0.0"
    assert record.timestamp == "2026-05-24T00:00:00Z"
    assert record.actor == "aidan"


def test_parse_raw_data_requires_tenant_id():
    """Missing tenant_id returns a FailedRecord."""
    data = {**VALID_DATA, "tenant_id": None}

    record = parse_raw_data(raw(data))

    assert isinstance(record, FailedRecord)
    assert record.error_code == "missing_tenant_id"


def test_parse_raw_data_requires_package():
    """Missing package returns a FailedRecord."""
    data = {**VALID_DATA, "package": None}

    record = parse_raw_data(raw(data))

    assert isinstance(record, FailedRecord)
    assert record.error_code == "missing_package"


def test_parse_raw_data_requires_version():
    """Missing version returns a FailedRecord."""
    data = {**VALID_DATA, "version": None}

    record = parse_raw_data(raw(data))

    assert isinstance(record, FailedRecord)
    assert record.error_code == "missing_version"


def test_parse_raw_data_generates_uuid_for_missing_event_id():
    """Missing event_id is filled with a generated uuid."""
    data = {**VALID_DATA, "event_id": None}

    record = parse_raw_data(raw(data))

    assert isinstance(record, TransformedRecord)
    assert record.event_id is not None
    assert len(record.event_id) == 36  # uuid4 string length


def test_parse_raw_data_defaults_action_to_unknown():
    """Missing action defaults to 'unknown'."""
    data = {**VALID_DATA, "action": None}

    record = parse_raw_data(raw(data))

    assert isinstance(record, TransformedRecord)
    assert record.action == "unknown"


def test_parse_raw_data_defaults_timestamp_to_empty_string():
    """Missing timestamp defaults to empty string."""
    data = {**VALID_DATA, "timestamp": None}

    record = parse_raw_data(raw(data))

    assert isinstance(record, TransformedRecord)
    assert record.timestamp == ""


def test_parse_raw_data_defaults_actor_to_empty_string():
    """Missing actor defaults to empty string."""
    data = {**VALID_DATA, "actor": None}

    record = parse_raw_data(raw(data))

    assert isinstance(record, TransformedRecord)
    assert record.actor == ""


def test_parse_raw_data_returns_failed_record_for_invalid_json():
    """Malformed JSON returns a FailedRecord."""
    record = parse_raw_data("not valid json{{{")

    assert isinstance(record, FailedRecord)
    assert record.error_code == "json_decode_error"


def test_parse_raw_data_returns_failed_record_for_non_dict_json():
    """JSON that is not a dict returns a FailedRecord."""
    record = parse_raw_data(json.dumps([1, 2, 3]))

    assert isinstance(record, FailedRecord)
    assert record.error_code == "invalid_type"
