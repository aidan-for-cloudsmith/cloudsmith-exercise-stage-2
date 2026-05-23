from datetime import UTC, datetime

from fastapi import APIRouter, HTTPException, Query

from query_api import datastore
from query_api.models import ActionType, EventListResponse, EventResponse, RetentionResponse

router = APIRouter()


@router.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/events", response_model=EventListResponse)
def list_events(
    tenant: str = Query(..., min_length=1),
    start_time: datetime | None = None,
    end_time: datetime | None = None,
    action_type: ActionType | None = None,
    package_name: str | None = None,
) -> EventListResponse:
    if (
        start_time is not None
        and end_time is not None
        and _comparable_datetime(start_time) > _comparable_datetime(end_time)
    ):
        raise HTTPException(status_code=400, detail="start_time must be before end_time")

    try:
        events = datastore.fetch_events(
            tenant=tenant,
            start_time=start_time,
            end_time=end_time,
            action_type=action_type.value if action_type is not None else None,
            package_name=package_name,
        )
    except datastore.InvalidTenantError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    event_responses = [EventResponse(**event) for event in events]
    return EventListResponse(events=event_responses, count=len(event_responses))


@router.post("/events/retention", response_model=RetentionResponse)
def apply_retention_policy(
    tenant: str = Query(..., min_length=1),
    retention_days: int = Query(datastore.EVENT_RETENTION_DAYS, ge=1),
) -> RetentionResponse:
    try:
        deleted = datastore.cleanup_expired_events(tenant=tenant, retention_days=retention_days)
    except datastore.InvalidTenantError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return RetentionResponse(tenant=tenant, retention_days=retention_days, deleted=deleted)


def _comparable_datetime(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value
    return value.astimezone(UTC).replace(tzinfo=None)
