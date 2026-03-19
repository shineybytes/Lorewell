from datetime import datetime, timedelta
from apscheduler.schedulers.background import BackgroundScheduler
from sqlalchemy.orm import Session
from app.db import SessionLocal
from app.models import ScheduledPost, Asset
from app.instagram import create_media_container, publish_container

scheduler = BackgroundScheduler()


def process_due_posts():
    db: Session = SessionLocal()
    try:
        now = datetime.utcnow()
        grace_start = now - timedelta(minutes=5)
        posts = (
            db.query(ScheduledPost)
            .filter(ScheduledPost.status == "approved")
            .filter(ScheduledPost.publish_at <= now)
            .filter(ScheduledPost.publish_at >= grace_start)
            .all()
        )

        for post in posts:
            try:
                post.status = "publishing"
                db.commit()

                asset = db.query(Asset).filter(Asset.id == post.asset_id).first()
                if asset is None:
                    raise RuntimeError(f"Asset {post.asset_id} not found")

                full_caption = (post.caption_final or "").strip()
                if post.hashtags_final:
                    full_caption += "\n\n" + post.hashtags_final.strip()

                container_id = create_media_container(
                    asset.file_path,
                    full_caption,
                    asset.media_type,
                )
                published_id = publish_container(container_id)

                post.status = "published"
                post.published_instagram_id = published_id
                post.error_message = None
                db.commit()
            except Exception as e:
                post.status = "failed"
                post.error_message = str(e)
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
