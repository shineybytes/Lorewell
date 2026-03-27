from datetime import datetime, timedelta, UTC
from apscheduler.schedulers.background import BackgroundScheduler
from sqlalchemy.orm import Session

from app.db import SessionLocal
from app.models import Schedule, ApprovedPost, Asset
from app.instagram import (
        create_media_container,
        publish_container,
        wait_until_container_ready
        )
from app.config import settings
import os
from pathlib import Path

scheduler = BackgroundScheduler()


def process_due_posts():
    # print("DEBUG scheduler tick")
    db: Session = SessionLocal()
    # print("DEBUG bound engine url:", db.get_bind().url)
    # print("DEBUG cwd:", os.getcwd())
    # print("DEBUG settings.database_url:", settings.database_url)
    # print("DEBUG resolved local lorewell.db:", Path("./lorewell.db").resolve())
    try:
        now = datetime.now(UTC).replace(tzinfo=None)
        grace_start = now - timedelta(minutes=5)
        # print(f"DEBUG database_url {settings.database_url}")
        # print(f"DEBUG now: {now}\nDEBUG grace_start: {grace_start}")

        schedules = (
            db.query(Schedule)
            .filter(Schedule.status == "scheduled")
            .filter(Schedule.publish_at <= now)
            .filter(Schedule.publish_at >= grace_start)
            .all()
            )
        # all_scheduled = db.query(Schedule).filter(Schedule.status == "scheduled").all() # I was double checking that the scheduler was grabbing everything

        # print("DEBUG all scheduled:", " ".join([f"({s.id}, {s.publish_at}, {s.status})" for s in all_scheduled]))
        # print("DEBUG due scheduled:", " ".join([f"({s.id}, {s.publish_at}, {s.status})" for s in schedules]))

        # print(f"DEBUG found {len(schedules)} schedules")

        for s in schedules:
            # print(f"DEBUG process schedule {s.id}: publish_at {s.publish_at}; status {s.status}")
            try:
                s.status = "publishing"
                db.commit()

                approved = (
                    db.query(ApprovedPost)
                    .filter(ApprovedPost.id == s.approved_post_id)
                    .first()
                    )

                if approved is None:
                    raise RuntimeError(f"ApprovedPost {s.approved_post_id} not found")

                asset = db.query(Asset).filter(Asset.id == approved.selected_asset_id).first()
                if asset is None:
                    raise RuntimeError(f"Asset {approved.selected_asset_id} not found")

                full_caption = (approved.caption_final or "").strip()
                if approved.hashtags_final:
                    full_caption += "\n\n" + approved.hashtags_final.strip()

                container_id = create_media_container(
                        asset.file_path,
                        full_caption,
                        asset.media_type
                        )
                wait_until_container_ready(container_id)
                published_id = publish_container(container_id)

                s.status = "published"
                s.published_instagram_id = published_id
                s.error_message = None
                db.commit()

            except Exception as e:
                s.status = "failed"
                s.error_message = str(e)
                db.commit()
    finally:
        db.close()

def start_scheduler():
    if not scheduler.running:
        scheduler.add_job(
            process_due_posts,
            "interval",
            seconds=30,
            id="due_posts",
            replace_existing=True,
            )
        scheduler.start()
