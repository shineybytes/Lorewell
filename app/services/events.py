from zoneinfo import ZoneInfo

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models import Asset, Event, Post
from app.schemas import EventCreate, EventResponse


def validate_event_datetime(event: Event) -> None:
    if event.event_date and not event.event_timezone:
        raise HTTPException(
            status_code=400,
            detail="event_timezone required when event_date is provided",
        )

    if event.event_timezone and not event.event_date:
        raise HTTPException(
            status_code=400,
            detail="event_date required when event_timezone is provided",
        )

    if event.event_date and event.event_date.tzinfo is not None:
        raise HTTPException(
            status_code=400,
            detail="event_date must not include timezone or Z suffix",
        )

    if event.event_timezone:
        try:
            ZoneInfo(event.event_timezone)
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid timezone")


def get_event_or_404(event_id: int, db: Session) -> Event:
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    return event


def to_event_response(event: Event) -> EventResponse:
    return EventResponse(
        id=event.id,
        title=event.title,
        event_type=event.event_type,
        location=event.location,
        event_date=event.event_date,
        event_timezone=event.event_timezone,
        recap=event.recap,
        keywords=event.keywords,
        vendors=event.vendors,
        event_guidance=event.event_guidance,
    )


def create_event_record(payload: EventCreate, db: Session) -> EventResponse:
    event = Event(**payload.model_dump())
    validate_event_datetime(event)

    db.add(event)
    db.commit()
    db.refresh(event)

    return to_event_response(event)


def update_event_record(
    event_id: int,
    payload: EventCreate,
    db: Session,
) -> EventResponse:
    event = get_event_or_404(event_id, db)

    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(event, field, value)

    validate_event_datetime(event)

    db.add(event)
    db.commit()
    db.refresh(event)

    return to_event_response(event)


def delete_event_record(event_id: int, db: Session) -> dict:
    event = get_event_or_404(event_id, db)

    db.query(Asset).filter(Asset.event_id == event_id).update(
        {"event_id": None},
        synchronize_session=False,
    )

    db.query(Post).filter(Post.event_id == event_id).update(
        {"event_id": None},
        synchronize_session=False,
    )

    db.delete(event)
    db.commit()

    return {"status": "deleted"}
