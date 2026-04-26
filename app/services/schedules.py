from datetime import UTC, datetime
from zoneinfo import ZoneInfo

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.domain.statuses import ScheduleStatus
from app.models import ApprovedPost, Asset, Schedule
from app.schemas import ScheduleCreate, ScheduleResponse


def get_approved_post_or_404(approved_post_id: int, db: Session) -> ApprovedPost:
    approved = (
        db.query(ApprovedPost)
        .filter(ApprovedPost.id == approved_post_id)
        .first()
    )
    if not approved:
        raise HTTPException(status_code=404, detail="ApprovedPost not found")
    return approved


def get_schedule_or_404(schedule_id: int, db: Session) -> Schedule:
    schedule = db.query(Schedule).filter(Schedule.id == schedule_id).first()
    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found")
    return schedule


def create_schedule_record(
    approved_post_id: int,
    payload: ScheduleCreate,
    db: Session,
) -> ScheduleResponse:
    approved = get_approved_post_or_404(approved_post_id, db)

    if payload.publish_at.tzinfo is not None:
        raise HTTPException(
            status_code=400,
            detail="publish_at must not include timezone or Z suffix",
        )

    try:
        tz = ZoneInfo(payload.publish_timezone)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid timezone")

    local_dt = payload.publish_at.replace(tzinfo=tz)
    publish_at_utc = local_dt.astimezone(UTC).replace(tzinfo=None)

    sched = Schedule(
        approved_post_id=approved.id,
        publish_at=publish_at_utc,
        publish_timezone=payload.publish_timezone,
        status=ScheduleStatus.SCHEDULED,
    )

    db.add(sched)
    db.commit()
    db.refresh(sched)

    return ScheduleResponse(schedule_id=sched.id, status=sched.status)


def publish_now_record(approved_post_id: int, db: Session) -> ScheduleResponse:
    approved = get_approved_post_or_404(approved_post_id, db)

    sched = Schedule(
        approved_post_id=approved.id,
        publish_at=datetime.now(UTC).replace(tzinfo=None),
        publish_timezone="UTC",
        status=ScheduleStatus.SCHEDULED,
    )

    db.add(sched)
    db.commit()
    db.refresh(sched)

    return ScheduleResponse(schedule_id=sched.id, status=sched.status)


def list_schedule_records(db: Session) -> list[dict]:
    schedules = db.query(Schedule).order_by(Schedule.publish_at.asc()).all()

    results = []
    for s in schedules:
        approved = (
            db.query(ApprovedPost)
            .filter(ApprovedPost.id == s.approved_post_id)
            .first()
        )

        asset = None
        if approved:
            asset = (
                db.query(Asset)
                .filter(Asset.id == approved.selected_asset_id)
                .first()
            )

        results.append(
            {
                "id": s.id,
                "approved_post_id": s.approved_post_id,
                "publish_at": s.publish_at.isoformat(),
                "publish_timezone": s.publish_timezone,
                "status": s.status,
                "error_message": s.error_message,
                "published_instagram_id": s.published_instagram_id,
                "caption_final": approved.caption_final if approved else "",
                "hashtags_final": (
                    approved.hashtags_final.split()
                    if approved and approved.hashtags_final
                    else []
                ),
                "accessibility_text": approved.accessibility_text if approved else None,
                "asset_file_path": asset.file_path if asset else None,
                "asset_media_type": asset.media_type if asset else None,
                "selected_asset_id": approved.selected_asset_id if approved else None,
                "failure_acknowledged": s.failure_acknowledged,
            }
        )

    return results


def toggle_schedule_acknowledged(schedule_id: int, db: Session) -> dict:
    schedule = get_schedule_or_404(schedule_id, db)

    schedule.failure_acknowledged = not schedule.failure_acknowledged

    db.add(schedule)
    db.commit()
    db.refresh(schedule)

    return {
        "id": schedule.id,
        "failure_acknowledged": schedule.failure_acknowledged,
    }


def retry_schedule_record(schedule_id: int, db: Session) -> dict:
    schedule = get_schedule_or_404(schedule_id, db)

    if schedule.status != ScheduleStatus.FAILED:
        raise HTTPException(
            status_code=400,
            detail="Only failed schedules can be retried",
        )

    new_schedule = Schedule(
        approved_post_id=schedule.approved_post_id,
        publish_at=datetime.now(UTC).replace(tzinfo=None),
        publish_timezone=schedule.publish_timezone,
        status=ScheduleStatus.SCHEDULED,
        error_message=None,
        failure_acknowledged=False,
    )

    db.add(new_schedule)
    db.commit()
    db.refresh(new_schedule)

    return {
        "schedule_id": new_schedule.id,
        "status": new_schedule.status,
    }


def archive_all_failed_records(db: Session) -> dict:
    schedules = (
        db.query(Schedule)
        .filter(
            Schedule.status == ScheduleStatus.FAILED,
            Schedule.failure_acknowledged == False,
        )
        .all()
    )

    for s in schedules:
        s.failure_acknowledged = True

    db.commit()

    return {"count": len(schedules)}


def restore_all_failed_records(db: Session) -> dict:
    schedules = (
        db.query(Schedule)
        .filter(
            Schedule.status == ScheduleStatus.FAILED,
            Schedule.failure_acknowledged == True,
        )
        .all()
    )

    for s in schedules:
        s.failure_acknowledged = False

    db.commit()

    return {"count": len(schedules)}


def delete_schedule_record(schedule_id: int, db: Session) -> dict:
    schedule = get_schedule_or_404(schedule_id, db)

    if schedule.status == ScheduleStatus.PUBLISHED:
        raise HTTPException(
            status_code=400,
            detail="Published schedules cannot be unscheduled",
        )

    db.delete(schedule)
    db.commit()

    return {"status": "deleted"}
