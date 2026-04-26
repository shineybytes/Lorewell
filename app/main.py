import os
from contextlib import asynccontextmanager
from datetime import UTC
from pathlib import Path

from fastapi import Depends, FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session

from app.config import settings
from app.db import Base, engine, get_db
from app.models import ApprovedPost, Asset, Event, Schedule
from app.scheduler import start_scheduler
from app.schemas import (
    ApprovePostRequest,
    ApprovedPostResponse,
    AssetAnalyzeRequest,
    AssetAnalyzeResponse,
    AssetAnalysisProposalResponse,
    AssetApplyAnalysisRequest,
    AssetApproveRequest,
    AssetApproveResponse,
    AssetEventUpdate,
    AssetRenameRequest,
    AssetResponse,
    EventCreate,
    EventResponse,
    PostDraftContentUpdate,
    PostDraftCreate,
    PostDraftCreateResponse,
    PostDraftUpdate,
    PostGenerateRequest,
    PostGenerationResponse,
    ScheduleCreate,
    ScheduleResponse,
    TimeConvertRequest,
    TimeConvertResponse,
)
from app.services.assets import (
    analyze_asset_record,
    apply_asset_analysis,
    approve_asset_record,
    build_asset_response,
    create_uploaded_asset,
    delete_asset_record,
    get_asset_or_404,
    propose_asset_analysis as propose_asset_analysis_service,
    rename_asset_record,
    update_asset_event_record,
)
from app.services.events import (
    create_event_record,
    delete_event_record,
    get_event_or_404,
    to_event_response,
    update_event_record,
)
from app.services.posts import (
    approve_post_record,
    create_post_record,
    delete_post_record,
    fork_approved_post_to_draft_record,
    generate_post_record,
    get_post_record,
    list_post_records,
    update_post_draft_content_record,
    update_post_record,
)
from app.services.schedules import (
    archive_all_failed_records,
    create_schedule_record,
    delete_schedule_record,
    list_schedule_records,
    publish_now_record,
    restore_all_failed_records,
    retry_schedule_record,
    toggle_schedule_acknowledged,
)

from app.services.approved_posts import list_approved_post_records
from app.services.time import convert_local_time_to_utc, list_available_timezones


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


@app.get("/")
def root():
    return {"ok": True, "message": "Lorewell running"}


# =========================
# Events
# =========================

@app.post("/events", response_model=EventResponse)
def create_event(payload: EventCreate, db: Session = Depends(get_db)):
    return create_event_record(payload, db)


@app.patch("/events/{event_id}", response_model=EventResponse)
def update_event(
    event_id: int,
    payload: EventCreate,
    db: Session = Depends(get_db),
):
    return update_event_record(event_id, payload, db)


@app.get("/events/{event_id}", response_model=EventResponse)
def get_event(event_id: int, db: Session = Depends(get_db)):
    event = get_event_or_404(event_id, db)
    return to_event_response(event)


@app.get("/events")
def list_events(db: Session = Depends(get_db)):
    events = db.query(Event).all()
    return [to_event_response(e) for e in events]


@app.delete("/events/{event_id}")
def delete_event(event_id: int, db: Session = Depends(get_db)):
    return delete_event_record(event_id, db)


# =========================
# Assets
# =========================

@app.post("/events/{event_id}/assets")
def upload_asset(
    event_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    return create_uploaded_asset(db=db, file=file, event_id=event_id)


@app.post("/assets/upload")
def upload_asset_no_event(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    return create_uploaded_asset(db=db, file=file, event_id=None)


@app.get("/events/{event_id}/assets", response_model=list[AssetResponse])
def list_event_assets(event_id: int, db: Session = Depends(get_db)):
    assets = db.query(Asset).filter(Asset.event_id == event_id).all()
    return [build_asset_response(a) for a in assets]


@app.get("/assets", response_model=list[AssetResponse])
def list_assets(db: Session = Depends(get_db)):
    assets = db.query(Asset).order_by(Asset.id.desc()).all()
    return [build_asset_response(a) for a in assets]


@app.get("/assets/{asset_id}", response_model=AssetResponse)
def get_asset(asset_id: int, db: Session = Depends(get_db)):
    asset = get_asset_or_404(asset_id, db)
    return build_asset_response(asset)


@app.patch("/assets/{asset_id}")
def rename_asset(
    asset_id: int,
    payload: AssetRenameRequest,
    db: Session = Depends(get_db),
):
    return rename_asset_record(asset_id, payload.display_name, db)


@app.patch("/assets/{asset_id}/event", response_model=AssetResponse)
def update_asset_event(
    asset_id: int,
    payload: AssetEventUpdate,
    db: Session = Depends(get_db),
):
    return update_asset_event_record(asset_id, payload.event_id, db)


@app.post("/assets/{asset_id}/analyze", response_model=AssetAnalyzeResponse)
def analyze_asset(
    asset_id: int,
    payload: AssetAnalyzeRequest,
    db: Session = Depends(get_db),
):
    asset = get_asset_or_404(asset_id, db)
    analyzed = analyze_asset_record(
        asset,
        db,
        user_correction=payload.user_correction,
    )

    return AssetAnalyzeResponse(
        asset_id=analyzed.id,
        analysis_status=analyzed.analysis_status,
        vision_summary_generated=analyzed.vision_summary_generated,
        accessibility_text_generated=analyzed.accessibility_text_generated,
        analysis_error_message=analyzed.analysis_error_message,
    )


@app.post("/assets/{asset_id}/approve", response_model=AssetApproveResponse)
def approve_asset(
    asset_id: int,
    payload: AssetApproveRequest,
    db: Session = Depends(get_db),
):
    return approve_asset_record(asset_id=asset_id, payload=payload, db=db)


@app.post(
    "/assets/{asset_id}/propose-analysis",
    response_model=AssetAnalysisProposalResponse,
)
def propose_asset_analysis(
    asset_id: int,
    payload: AssetAnalyzeRequest,
    db: Session = Depends(get_db),
):
    return propose_asset_analysis_service(
        asset_id=asset_id,
        user_correction=payload.user_correction,
        db=db,
    )


@app.patch("/assets/{asset_id}/apply-analysis", response_model=AssetResponse)
def apply_asset_analysis_route(
    asset_id: int,
    payload: AssetApplyAnalysisRequest,
    db: Session = Depends(get_db),
):
    return apply_asset_analysis(asset_id=asset_id, payload=payload, db=db)


@app.delete("/assets/{asset_id}")
def delete_asset(asset_id: int, db: Session = Depends(get_db)):
    return delete_asset_record(asset_id, db)


# =========================
# Posts / Drafts
# =========================

@app.post("/posts", response_model=PostDraftCreateResponse)
def create_post_route(
    payload: PostDraftCreate,
    db: Session = Depends(get_db),
):
    return create_post_record(payload, db)


@app.get("/posts")
def list_posts(db: Session = Depends(get_db)):
    return list_post_records(db)


@app.get("/posts/{post_id}")
def get_post(post_id: int, db: Session = Depends(get_db)):
    return get_post_record(post_id, db)


@app.patch("/posts/{post_id}", response_model=PostDraftCreateResponse)
def update_post_route(
    post_id: int,
    payload: PostDraftUpdate,
    db: Session = Depends(get_db),
):
    return update_post_record(post_id, payload, db)


@app.patch("/posts/{post_id}/draft-content")
def update_post_draft_content(
    post_id: int,
    payload: PostDraftContentUpdate,
    db: Session = Depends(get_db),
):
    return update_post_draft_content_record(post_id, payload, db)


@app.post("/posts/{post_id}/generate", response_model=PostGenerationResponse)
def generate_post(
    post_id: int,
    payload: PostGenerateRequest | None = None,
    db: Session = Depends(get_db),
):
    return generate_post_record(post_id, payload, db)


@app.post("/posts/{post_id}/approve", response_model=ApprovedPostResponse)
def approve_post(
    post_id: int,
    payload: ApprovePostRequest,
    db: Session = Depends(get_db),
):
    return approve_post_record(post_id, payload, db)


@app.delete("/posts/{post_id}")
def delete_post(post_id: int, db: Session = Depends(get_db)):
    return delete_post_record(post_id, db)


@app.post(
    "/approved-posts/{approved_post_id}/fork-draft",
    response_model=PostDraftCreateResponse,
)
def fork_approved_post_to_draft(
    approved_post_id: int,
    db: Session = Depends(get_db),
):
    return fork_approved_post_to_draft_record(approved_post_id, db)


# =========================
# Approved Posts
# =========================

@app.get("/approved-posts")
def list_approved_posts(db: Session = Depends(get_db)):
    return list_approved_post_records(db)


# =========================
# Schedules
# =========================

@app.post(
    "/approved-posts/{approved_post_id}/schedule",
    response_model=ScheduleResponse,
)
def schedule_post(
    approved_post_id: int,
    payload: ScheduleCreate,
    db: Session = Depends(get_db),
):
    return create_schedule_record(approved_post_id, payload, db)


@app.post(
    "/approved-posts/{approved_post_id}/publish-now",
    response_model=ScheduleResponse,
)
def publish_now(
    approved_post_id: int,
    db: Session = Depends(get_db),
):
    return publish_now_record(approved_post_id, db)


@app.get("/schedules")
def list_schedules(db: Session = Depends(get_db)):
    return list_schedule_records(db)


@app.patch("/schedules/{schedule_id}/acknowledge")
def acknowledge_schedule_failure(
    schedule_id: int,
    db: Session = Depends(get_db),
):
    return toggle_schedule_acknowledged(schedule_id, db)


@app.post("/schedules/{schedule_id}/retry")
def retry_schedule(schedule_id: int, db: Session = Depends(get_db)):
    return retry_schedule_record(schedule_id, db)


@app.post("/schedules/archive-all-failed")
def archive_all_failed(db: Session = Depends(get_db)):
    return archive_all_failed_records(db)


@app.post("/schedules/restore-all-failed")
def restore_all_failed(db: Session = Depends(get_db)):
    return restore_all_failed_records(db)


@app.delete("/schedules/{schedule_id}")
def delete_schedule(schedule_id: int, db: Session = Depends(get_db)):
    return delete_schedule_record(schedule_id, db)


# =========================
# Time Utilities
# =========================

@app.get("/timezones")
def list_timezones():
    return list_available_timezones()


@app.post("/time/convert", response_model=TimeConvertResponse)
def convert_time(payload: TimeConvertRequest):
    return convert_local_time_to_utc(payload)


# =========================
# Debug
# =========================

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
