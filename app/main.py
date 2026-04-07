import os
from datetime import datetime, timezone, UTC
from pathlib import Path
from zoneinfo import ZoneInfo, available_timezones

from contextlib import asynccontextmanager
from fastapi import Depends, FastAPI, File, HTTPException, UploadFile
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from app.ai import analyze_media, generate_caption_package
from app.config import settings
from app.db import Base, engine, get_db
from app.media_validation import validate_media_file
from app.models import ApprovedPost, Asset, Event, Post, Schedule
from app.scheduler import start_scheduler
from app.schemas import (
    ApprovePostRequest,
    ApprovedPostResponse,
    AssetAnalyzeRequest,
    AssetAnalyzeResponse,
    AssetApproveRequest,
    AssetApproveResponse,
    AssetResponse,
    EventCreate,
    EventResponse,
    PostDraftCreate,
    PostDraftCreateResponse,
    PostDraftUpdate,
    PostGenerationResponse,
    ScheduleCreate,
    ScheduleResponse,
    TimeConvertRequest,
    TimeConvertResponse,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    start_scheduler()
    yield

app = FastAPI(title="Lorewell", lifespan=lifespan)


def init_app() -> None:
    Path(settings.media_dir).mkdir(parents=True, exist_ok=True)
    Base.metadata.create_all(bind=engine)
    app.mount("/media", StaticFiles(directory=settings.media_dir), name="media")
    app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


init_app()



def analyze_asset_record(asset: Asset, db: Session, user_correction: str | None = None) -> Asset:
    try:
        result = analyze_media(asset.file_path, asset.media_type, user_correction=user_correction)

        asset.analysis_user_correction = user_correction
        asset.vision_summary_generated = result.get("visual_summary")
        asset.accessibility_text_generated = result.get("accessibility_text")
        asset.analysis_status = "analyzed"
        asset.analysis_error_message = None

    except Exception as e:
        asset.analysis_status = "failed"
        asset.analysis_error_message = str(e)

    db.add(asset)
    db.commit()
    db.refresh(asset)
    return asset


def create_post(payload: PostDraftCreate, db: Session) -> PostDraftCreateResponse:
    asset = db.query(Asset).filter(Asset.id == payload.asset_id).first()
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")

    if payload.event_id is not None:
        event = db.query(Event).filter(Event.id == payload.event_id).first()
        if not event:
            raise HTTPException(status_code=404, detail="Event not found")

    post = Post(
        event_id=payload.event_id,
        primary_asset_id=payload.asset_id,
        brand_voice=payload.brand_voice,
        cta_goal=payload.cta_goal,
        generation_notes=payload.generation_notes,
        status="draft",
    )

    db.add(post)
    db.commit()
    db.refresh(post)

    return PostDraftCreateResponse(
        post_id=post.id,
        status=post.status,
    )


@app.get("/")
def root():
    return {"ok": True, "message": "Lorewell running"}

def validate_event_datetime(event: Event) -> None:
    if event.event_date and not event.event_timezone:
        raise HTTPException(400, "event_timezone required when event_date is provided")

    if event.event_timezone and not event.event_date:
        raise HTTPException(400, "event_date required when event_timezone is provided")

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

@app.post("/events", response_model=EventResponse)
def create_event(payload: EventCreate, db: Session = Depends(get_db)):
    event = Event(**payload.model_dump())
    validate_event_datetime(event)
    db.add(event)
    db.commit()
    db.refresh(event)

    return to_event_response(event)


@app.post("/events/{event_id}/assets")
def upload_asset(
    event_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
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

    asset = Asset(
        event_id=event_id,
        file_path=str(save_path),
        media_type=media_type,
        analysis_status="pending",
    )
    db.add(asset)
    db.commit()
    db.refresh(asset)

    asset = analyze_asset_record(asset, db)

    return {
        "asset_id": asset.id,
        "media_type": asset.media_type,
        "analysis_status": asset.analysis_status,
        "vision_summary_generated": asset.vision_summary_generated,
        "accessibility_text_generated": asset.accessibility_text_generated,
    }


@app.get("/events/{event_id}/assets", response_model=list[AssetResponse])
def list_event_assets(event_id: int, db: Session = Depends(get_db)):
    assets = db.query(Asset).filter(Asset.event_id == event_id).all()
    return [
        AssetResponse(
            id=a.id,
            event_id=a.event_id,
            file_path=a.file_path,
            media_type=a.media_type,
            analysis_status=a.analysis_status,
            vision_summary_generated=a.vision_summary_generated,
            accessibility_text_generated=a.accessibility_text_generated,
            accessibility_text_final=a.accessibility_text_final,
            analysis_error_message=a.analysis_error_message,
            analysis_user_correction=a.analysis_user_correction
        )
        for a in assets
    ]


@app.post("/assets/{asset_id}/analyze", response_model=AssetAnalyzeResponse)
def analyze_asset(
        asset_id: int,
        payload:AssetAnalyzeRequest,
        db: Session = Depends(get_db)
):
    asset = db.query(Asset).filter(Asset.id == asset_id).first()
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")

    asset = analyze_asset_record(asset, db, user_correction=payload.user_correction)

    return AssetAnalyzeResponse(
        asset_id=asset.id,
        analysis_status=asset.analysis_status,
        vision_summary_generated=asset.vision_summary_generated,
        accessibility_text_generated=asset.accessibility_text_generated,
        analysis_error_message=asset.analysis_error_message,
    )


@app.post("/assets/{asset_id}/approve", response_model=AssetApproveResponse)
def approve_asset(
    asset_id: int,
    payload: AssetApproveRequest,
    db: Session = Depends(get_db),
):
    asset = db.query(Asset).filter(Asset.id == asset_id).first()
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")

    asset.accessibility_text_final = payload.accessibility_text_final
    asset.analysis_status = "approved"
    asset.analysis_error_message = None

    db.add(asset)
    db.commit()
    db.refresh(asset)

    return AssetApproveResponse(
        asset_id=asset.id,
        analysis_status=asset.analysis_status,
        accessibility_text_final=asset.accessibility_text_final or "",
    )


@app.post("/posts", response_model=PostDraftCreateResponse)
def create_post_route(
    payload: PostDraftCreate,
    db: Session = Depends(get_db),
):
    return create_post(payload, db)


@app.post("/posts/{post_id}/generate", response_model=PostGenerationResponse)
def generate_post(post_id: int, db: Session = Depends(get_db)):
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    asset = db.query(Asset).filter(Asset.id == post.primary_asset_id).first()
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")

    event = None
    if post.event_id is not None:
        event = db.query(Event).filter(Event.id == post.event_id).first()

    result = generate_caption_package(event, asset, post)

    post.generated_caption_options = result.get("caption_medium")
    post.generated_hashtag_options = " ".join(result.get("hashtags", []))
    post.generated_accessibility_options = (
        asset.accessibility_text_final
        or result.get("accessibility_text")
    )
    post.status = "generated"
    post.error_message = None

    db.add(post)
    db.commit()
    db.refresh(post)

    return PostGenerationResponse(
        post_id=post.id,
        status=post.status,
        caption_short=result.get("caption_short"),
        caption_medium=result.get("caption_medium"),
        caption_long=result.get("caption_long"),
        hashtags=result.get("hashtags", []),
        accessibility_text=post.generated_accessibility_options,
        seo_keywords=result.get("seo_keywords", []),
        visual_summary=result.get("visual_summary"),
    )


@app.post("/posts/{post_id}/approve", response_model=ApprovedPostResponse)
def approve_post(
    post_id: int,
    payload: ApprovePostRequest,
    db: Session = Depends(get_db),
):
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    asset = db.query(Asset).filter(Asset.id == post.primary_asset_id).first()
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")

    final_accessibility_text = (
            payload.accessibility_text
            or asset.accessibility_text_final
            or asset.accessibility_text_generated
    )

    approved = ApprovedPost(
        post_id=post.id,
        selected_asset_id=post.primary_asset_id,
        caption_final=payload.caption_final,
        hashtags_final=" ".join(payload.hashtags_final),
        accessibility_text=final_accessibility_text,
    )

    post.status = "approved"

    db.add(approved)
    db.add(post)
    db.commit()
    db.refresh(approved)

    return ApprovedPostResponse(
        approved_post_id=approved.id,
        status="approved",
    )


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


@app.post("/approved-posts/{approved_post_id}/schedule", response_model=ScheduleResponse)
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
    publish_at_utc = local_dt.astimezone(UTC).replace(tzinfo=None)

    sched = Schedule(
        approved_post_id=approved.id,
        publish_at=publish_at_utc,
        publish_timezone=payload.publish_timezone,
        status="scheduled",
    )

    db.add(sched)
    db.commit()
    db.refresh(sched)

    return ScheduleResponse(
        schedule_id=sched.id,
        status=sched.status,
    )


@app.get("/timezones")
def list_timezones():
    return sorted(
        tz for tz in available_timezones()
        if "/" in tz and not tz.startswith("Etc/")
    )


@app.post("/time/convert", response_model=TimeConvertResponse)
def convert_time(payload: TimeConvertRequest):
    if payload.local_datetime.tzinfo is not None:
        raise HTTPException(
            status_code=400,
            detail="local_datetime must not include a timezone or a Z suffix",
        )

    try:
        tz = ZoneInfo(payload.timezone)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid timezone")

    local_dt = payload.local_datetime.replace(tzinfo=tz)
    utc_dt = local_dt.astimezone(UTC)

    return TimeConvertResponse(
        local_datetime=payload.local_datetime.isoformat(),
        timezone=payload.timezone,
        utc_datetime=utc_dt.replace(tzinfo=None).isoformat(),
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

@app.get("/events/{event_id}", response_model=EventResponse)
def get_event(event_id: int, db: Session = Depends(get_db)):
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    return to_event_response(event)

@app.get("/events")
def list_events(db: Session = Depends(get_db)):
    events = db.query(Event).all()
    return [to_event_response(e) for e in events]

@app.get("/posts/{post_id}")
def get_post(post_id: int, db: Session = Depends(get_db)):
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    return {
        "id": post.id,
        "event_id": post.event_id,
        "asset_id": post.primary_asset_id,
        "brand_voice": post.brand_voice,
        "cta_goal": post.cta_goal,
        "generation_notes": post.generation_notes,
        "generated_caption_options": post.generated_caption_options,
        "generated_hashtag_options": post.generated_hashtag_options,
        "generated_accessibility_options": post.generated_accessibility_options,
        "status": post.status,
        "error_message": post.error_message,
        "created_at": post.created_at.isoformat(),
    }
@app.patch("/posts/{post_id}", response_model=PostDraftCreateResponse)
def update_post_route(
    post_id: int,
    payload: PostDraftUpdate,
    db: Session = Depends(get_db),
):
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    post.brand_voice = payload.brand_voice
    post.cta_goal = payload.cta_goal
    post.generation_notes = payload.generation_notes

    db.add(post)
    db.commit()
    db.refresh(post)

    return PostDraftCreateResponse(
        post_id=post.id,
        status=post.status,
    )

@app.get("/approved-posts")
def list_approved_posts(db: Session = Depends(get_db)):
    approved_posts = db.query(ApprovedPost).all()

    return [
        {
            "id": a.id,
            "post_id": a.post_id,
            "selected_asset_id": a.selected_asset_id,
            "caption_final": a.caption_final,
            "hashtags_final": a.hashtags_final.split() if a.hashtags_final else [],
            "accessibility_text": a.accessibility_text,
            "status": "approved",
        }
        for a in approved_posts
    ]
