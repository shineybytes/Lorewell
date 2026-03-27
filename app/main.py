from pathlib import Path
from shutil import copyfileobj
from fastapi import FastAPI, UploadFile, File, Depends, HTTPException
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session

from app.config import settings
from app.db import Base, engine, get_db
from app.models import Event, Asset, Post, ApprovedPost, Schedule
from app.media_validation import validate_media_file
from app.schemas import (
        EventCreate,
        PostDraftCreate,
        ApprovePostRequest,
        ScheduleCreate,
        TimeConvertRequest,
        TimeConvertResponse
)
from app.ai import generate_caption_package
from app.scheduler import start_scheduler

from zoneinfo import ZoneInfo, available_timezones
from datetime import timezone

app = FastAPI(title="Lorewell")

Path(settings.media_dir).mkdir(parents=True, exist_ok=True)
Base.metadata.create_all(bind=engine)
app.mount("/media", StaticFiles(directory=settings.media_dir), name="media")


@app.on_event("startup")
def startup_event():
    start_scheduler()


@app.get("/")
def root():
    return {"ok": True, "message": "Lorewell running"}


@app.post("/events",
          summary="Creates an Event object with metadata",
          description="Creates a cool event",
          response_description="Returns the ID of the event for reference")
def create_event(payload: EventCreate, db: Session = Depends(get_db)):
    event = Event(**payload.model_dump())
    db.add(event)
    db.commit()
    db.refresh(event)
    return {"id": event.id}


@app.post("/events/{event_id}/upload",
          summary="Annotates to an event ID a media file",
          description="This attaches either a photo or video compliant to Instagram restrictions to an event",
          response_description="The media ID and whether it is an image or video")
def upload_asset(event_id: int, file: UploadFile = File(...), db: Session = Depends(get_db)):
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    contents = file.file.read()
    file_size = len(contents)

    media_type, validation_error = validate_media_file(file.filename, file_size)
    if validation_error:
        raise HTTPException(status_code=400, detail=validation_error)

    safe_name = Path(file.filename).name
    save_path = Path(settings.media_dir) / safe_name

    with save_path.open("wb") as buffer:
        buffer.write(contents)

    asset = Asset(event_id=event_id, file_path=str(save_path), media_type=media_type)
    db.add(asset)
    db.commit()
    db.refresh(asset)
    return {"asset_id": asset.id, "media_type": asset.media_type}


def create_post(payload: PostDraftCreate, db: Session):
    asset = db.query(Asset).filter(Asset.id == payload.asset_id).first()
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    if payload.event_id:
        event = db.query(Event).filter(Event.id == payload.event_id).first()
        if not event:
            raise HTTPException(status_code=404, detail="Event not found")
    post = Post(
        event_id=payload.event_id,
        primary_asset_id=payload.asset_id,
        brand_voice=payload.brand_voice,
        cta_hint=payload.cta_hint,
        generation_notes=payload.generation_notes,
        status="draft"
    )

    db.add(post)
    db.commit()
    db.refresh(post)

    return {"post_id": post.id, "status": post.status}


@app.post("/posts")
def create_post_route(
    payload: PostDraftCreate,
    db: Session = Depends(get_db),
):
    return create_post(payload, db)

@app.post("/posts/{post_id}/generate")
def generate_post(post_id: int, db: Session = Depends(get_db)):

    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    asset = db.query(Asset).filter(Asset.id == post.primary_asset_id).first()
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")

    event = None
    if post.event_id:
        event = db.query(Event).filter(Event.id == post.event_id).first()

    result = generate_caption_package(event, asset)

    post.generated_caption_options = result.get("caption_medium")
    post.generated_hashtag_options = " ".join(result.get("hashtags", []))
    post.generated_accessibility_options = result.get("accessibility_text")

    post.status = "generated"

    db.commit()

    return result

@app.post("/posts/{post_id}/approve")
def approve_post(post_id: int, payload: ApprovePostRequest, db: Session = Depends(get_db)):
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    approved = ApprovedPost(
        post_id=post.id,
        selected_asset_id=post.primary_asset_id,
        caption_final=payload.caption_final,
        hashtags_final=payload.hashtags_final,
        accessibility_text=payload.accessibility_text,
    )

    post.status = "approved"

    db.add(approved)
    db.commit()
    db.refresh(approved)

    return {
        "approved_post_id": approved.id,
        "status": "approved",
    }

@app.get("/posts")
def list_posts(db: Session = Depends(get_db)):
    posts = db.query(Post).all()

    return [
        {
            "id": p.id,
            "event_id": p.event_id,
            "asset_id": p.primary_asset_id,
            "status": p.status,
            "created_at": p.created_at.isoformat(),
        }
        for p in posts
    ]

@app.post("/approved-posts/{approved_post_id}/schedule")
def schedule_post(
    approved_post_id: int,
    payload: ScheduleCreate,
    db: Session = Depends(get_db),
):

    approved = (
        db.query(ApprovedPost)
        .filter(ApprovedPost.id == approved_post_id)
        .first()
    )

    if not approved:
        raise HTTPException(status_code=404, detail="ApprovedPost not found")

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
    publish_at_utc = local_dt.astimezone(timezone.utc).replace(tzinfo=None)

    sched = Schedule(
        approved_post_id=approved.id,
        publish_at=publish_at_utc,
        publish_timezone=payload.publish_timezone,
        status="scheduled",
    )

    db.add(sched)
    db.commit()
    db.refresh(sched)

    return {"schedule_id": sched.id, "status": sched.status}

@app.get("/timezones")
def list_timezones():
    return sorted(available_timezones())

@app.post("/time/convert", response_model=TimeConvertResponse)
def convert_time(payload: TimeConvertRequest):
    if payload.local_datetime.tzinfo is not None:
        raise HTTPException(
                status_code=400,
                detail="local_datetime must not include a timezone or a Z suffix"
                )
    try:
        tz = ZoneInfo(payload.timezone)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid timezone")

    local_dt = payload.local_datetime.replace(tzinfo=tz)
    utc_dt = local_dt.astimezone(timezone.utc)

    return TimeConvertResponse(
            local_datetime=payload.local_datetime.isoformat(),
            timezone=payload.timezone,
            utc_datetime=utc_dt.replace(tzinfo=None).isoformat()
            )
@app.get("/schedules")
def list_schedules(db: Session = Depends(get_db)):
    schedules = db.query(Schedule).order_by(Schedule.publish_at.asc()).all()
    return [
        {
            "id": s.id,
            "approved_post_id": s.approved_post_id,
            "publish_at": s.publish_at.isoformat(),
            "publish_timezone": s.publish_timezone,
            "status": s.status,
            "error_message": s.error_message,
            "published_instagram_id": s.published_instagram_id,
        }
        for s in schedules
    ]
import os
from pathlib import Path
from app.db import engine

@app.get("/debug/db")
def debug_db(db: Session = Depends(get_db)):
    schedules = db.query(Schedule).all()
    return {
        "cwd": os.getcwd(),
        "settings_database_url": settings.database_url,
        "engine_url": str(engine.url),
        "bound_url": str(db.get_bind().url),
        "resolved_local_db": str(Path("./lorewell.db").resolve()),
        "schedule_count": len(schedules),
        "schedule_ids": [s.id for s in schedules],
    }
