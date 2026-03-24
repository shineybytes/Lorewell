from pathlib import Path
from shutil import copyfileobj
from fastapi import FastAPI, UploadFile, File, Depends, HTTPException
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session

from app.config import settings
from app.db import Base, engine, get_db
from app.models import Event, Asset, ScheduledPost
from app.media_validation import validate_media_file
from app.schemas import (
        EventCreate,
        PostCreate,
        GenerateRequest,
        ApproveRequest,
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


@app.post("/posts",
          summary="Creates a post container with time scheduler",
          description="",
          response_description="")
def create_post(payload: PostCreate, db: Session = Depends(get_db)):
    if payload.publish_at.tzinfo is not None:
        raise HTTPException(
                status_code=400,
                detail="publish_at must not include a timezone or z suffix when publish_timezone is provided"
        )
    try:
        tz = ZoneInfo(payload.publish_timezone)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid timezone")

    local_dt = payload.publish_at.replace(tzinfo=tz)
    publish_at_utc = local_dt.astimezone(timezone.utc).replace(tzinfo=None)

    post = ScheduledPost(
            event_id=payload.event_id,
            asset_id=payload.asset_id,
            publish_at=publish_at_utc,
            publish_timezone=payload.publish_timezone
            )
    db.add(post)
    db.commit()
    db.refresh(post)
    return {"post_id": post.id, "status": post.status}


@app.post("/posts/generate")
def generate_post(payload: GenerateRequest, db: Session = Depends(get_db)):
    post = db.query(ScheduledPost).filter(ScheduledPost.id == payload.post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    event = db.query(Event).filter(Event.id == post.event_id).first()
    asset = db.query(Asset).filter(Asset.id == post.asset_id).first()
    if not event or not asset:
        raise HTTPException(status_code=404, detail="Related event or asset not found")

    result = generate_caption_package(event, asset)

    post.caption_final = result.get("caption_medium")
    post.hashtags_final = " ".join(result.get("hashtags", []))
    post.accessibility_text = result.get("accessibility_text")
    db.commit()

    return result


@app.post("/posts/{post_id}/approve")
def approve_post(post_id: int, payload: ApproveRequest, db: Session = Depends(get_db)):
    post = db.query(ScheduledPost).filter(ScheduledPost.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    post.caption_final = payload.caption_final
    post.hashtags_final = payload.hashtags_final
    post.accessibility_text = payload.accessibility_text
    post.status = "approved"
    db.commit()
    return {"ok": True, "status": post.status}


@app.get("/posts")
def list_posts(db: Session = Depends(get_db)):
    posts = db.query(ScheduledPost).order_by(ScheduledPost.publish_at.asc()).all()
    return [
            {
                "id": p.id,
                "event_id": p.event_id,
                "asset_id": p.asset_id,
                "publish_at": p.publish_at.isoformat(),
                "publish_timezone": p.publish_timezone,
                "status": p.status,
                "caption_final": p.caption_final,
                "hashtags_final": p.hashtags_final,
                "error_message": p.error_message,
                "published_instagram_id": p.published_instagram_id,
                }
            for p in posts
            ]
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
