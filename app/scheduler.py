from datetime import UTC, datetime, timedelta

from apscheduler.schedulers.background import BackgroundScheduler
from sqlalchemy.orm import Session

from app.db import SessionLocal
from app.instagram import (
    create_media_container,
    publish_container,
    wait_until_container_ready,
)
from app.models import ApprovedPost, Asset, Schedule


SCHEDULER_JOB_ID = "due_posts"
SCHEDULER_TICK_SECONDS = 30
PUBLISHING_STALE_MINUTES = 15

scheduler = BackgroundScheduler()


def process_due_posts() -> None:
    print("DEBUG scheduler tick")
    db: Session = SessionLocal()

    try:
        now = datetime.now(UTC).replace(tzinfo=None)

        stale_cutoff = now - timedelta(minutes=PUBLISHING_STALE_MINUTES)

        stale_publishing = (
            db.query(Schedule)
            .filter(Schedule.status == "publishing")
            .filter(Schedule.publishing_started_at.is_not(None))
            .filter(Schedule.publishing_started_at <= stale_cutoff)
            .all()
        )

        for schedule in stale_publishing:
            schedule.status = "failed"
            schedule.error_message = "Publishing attempt became stale and was marked failed"
            schedule.last_attempt_error = schedule.error_message
            schedule.publishing_started_at = None
            db.add(schedule)
        
        db.commit()

        schedules = (
            db.query(Schedule)
            .filter(Schedule.status == "scheduled")
            .filter(Schedule.publish_at <= now)
            .all()
        )
        print(f"DEBUG found {len(schedules)} due schedules")

        for schedule in schedules:
            try:
                schedule.status = "publishing"
                schedule.publishing_started_at = datetime.now(UTC).replace(tzinfo=None)
                schedule.publish_attempts += 1
                schedule.last_attempt_error = None
                schedule.error_message = None
                db.add(schedule)
                db.commit()
                db.refresh(schedule)

                approved_post = (
                    db.query(ApprovedPost)
                    .filter(ApprovedPost.id == schedule.approved_post_id)
                    .first()
                )
                if approved_post is None:
                    raise RuntimeError(
                        f"ApprovedPost {schedule.approved_post_id} not found"
                    )

                asset = (
                    db.query(Asset)
                    .filter(Asset.id == approved_post.selected_asset_id)
                    .first()
                )
                if asset is None:
                    raise RuntimeError(
                        f"Asset {approved_post.selected_asset_id} not found"
                    )

                caption_parts: list[str] = []

                if approved_post.caption_final:
                    caption_parts.append(approved_post.caption_final.strip())

                if approved_post.hashtags_final:
                    caption_parts.append(approved_post.hashtags_final.strip())

                full_caption = "\n\n".join(part for part in caption_parts if part)

                container_id = create_media_container(
                    file_path=asset.file_path,
                    caption=full_caption,
                    media_type=asset.media_type,
                )

                wait_until_container_ready(container_id)
                published_id = publish_container(container_id)

                schedule.status = "published"
                schedule.published_instagram_id = published_id
                schedule.error_message = None
                schedule.last_attempt_error = None
                schedule.publishing_started_at = None
                db.add(schedule)
                db.commit()
                db.refresh(schedule)

            except Exception as e:
                schedule.status = "failed"
                schedule.error_message = str(e)
                schedule.last_attempt_error = str(e)
                schedule.publishing_started_at = None
                db.add(schedule)
                db.commit()

    finally:
        db.close()


def start_scheduler() -> None:
    if scheduler.get_job(SCHEDULER_JOB_ID) is None:
        scheduler.add_job(
            process_due_posts,
            "interval",
            seconds=SCHEDULER_TICK_SECONDS,
            id=SCHEDULER_JOB_ID,
            replace_existing=True,
        )

    if not scheduler.running:
        scheduler.start()
