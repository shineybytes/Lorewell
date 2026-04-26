from pathlib import Path

from fastapi import HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.ai import analyze_media
from app.asset_timestamp import extract_timestamp_from_filename
from app.config import settings
from app.domain.statuses import AssetStatus
from app.media_validation import validate_media_file
from app.models import Asset, Event, Post
from app.schemas import (
    AssetAnalysisProposalResponse,
    AssetApplyAnalysisRequest,
    AssetApproveRequest,
    AssetApproveResponse,
    AssetResponse,
)


def build_asset_response(asset: Asset) -> AssetResponse:
    return AssetResponse(
        id=asset.id,
        event_id=asset.event_id,
        file_path=asset.file_path,
        media_type=asset.media_type,
        analysis_status=asset.analysis_status,
        display_name=asset.display_name,
        created_at=asset.created_at,
        captured_at_guess=asset.captured_at_guess,
        captured_at_guess_source=asset.captured_at_guess_source,
        captured_at_guess_confidence=asset.captured_at_guess_confidence,
        captured_at_guess_matched_text=asset.captured_at_guess_matched_text,
        vision_summary_generated=asset.vision_summary_generated,
        accessibility_text_generated=asset.accessibility_text_generated,
        accessibility_text_final=asset.accessibility_text_final,
        analysis_error_message=asset.analysis_error_message,
        analysis_user_correction=asset.analysis_user_correction,
    )


def get_asset_or_404(asset_id: int, db: Session) -> Asset:
    asset = db.query(Asset).filter(Asset.id == asset_id).first()
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    return asset


def create_uploaded_asset(
    *,
    db: Session,
    file: UploadFile,
    event_id: int | None = None,
) -> dict:
    if event_id is not None:
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

    timestamp_guess = extract_timestamp_from_filename(safe_name)

    asset = Asset(
        event_id=event_id,
        file_path=str(save_path),
        display_name=safe_name,
        media_type=media_type,
        captured_at_guess=timestamp_guess.captured_at_guess,
        captured_at_guess_source=timestamp_guess.captured_at_guess_source,
        captured_at_guess_confidence=timestamp_guess.captured_at_guess_confidence,
        captured_at_guess_matched_text=timestamp_guess.captured_at_guess_matched_text,
        analysis_status=AssetStatus.PENDING,
    )

    db.add(asset)
    db.commit()
    db.refresh(asset)

    return {
        "asset_id": asset.id,
        "media_type": asset.media_type,
        "analysis_status": asset.analysis_status,
        "vision_summary_generated": asset.vision_summary_generated,
        "accessibility_text_generated": asset.accessibility_text_generated,
        "captured_at_guess": asset.captured_at_guess,
        "captured_at_guess_source": asset.captured_at_guess_source,
        "captured_at_guess_confidence": asset.captured_at_guess_confidence,
        "captured_at_guess_matched_text": asset.captured_at_guess_matched_text,
    }


def analyze_asset_record(
    asset: Asset,
    db: Session,
    user_correction: str | None = None,
) -> Asset:
    try:
        result = analyze_media(
            asset.file_path,
            asset.media_type,
            user_correction=user_correction,
        )

        asset.analysis_user_correction = user_correction
        asset.vision_summary_generated = result.get("visual_summary")
        asset.accessibility_text_generated = result.get("accessibility_text")
        asset.analysis_status = AssetStatus.ANALYZED
        asset.analysis_error_message = None

    except Exception as e:
        asset.analysis_status = AssetStatus.FAILED
        asset.analysis_error_message = str(e)

    db.add(asset)
    db.commit()
    db.refresh(asset)
    return asset


def build_event_context_correction(
    asset: Asset,
    db: Session,
    user_correction: str | None = None,
) -> str | None:
    event = None
    if asset.event_id is not None:
        event = db.query(Event).filter(Event.id == asset.event_id).first()

    event_bits: list[str] = []

    if event:
        if event.title:
            event_bits.append(f"Title: {event.title}")
        if event.event_type:
            event_bits.append(f"Type: {event.event_type}")
        if event.location:
            event_bits.append(f"Location: {event.location}")
        if event.recap:
            event_bits.append(f"Recap: {event.recap}")
        if event.event_guidance:
            event_bits.append(f"Guidance: {event.event_guidance}")
        if event.vendors:
            event_bits.append(f"Vendors: {event.vendors}")

    context_text = ""
    if event_bits:
        context_text = (
            "Event context may help interpret this asset. "
            "Use it as secondary context only. "
            "Do not invent details not supported by what is visible.\n\n"
            + "\n".join(event_bits)
        )

    correction_parts = [part for part in [user_correction, context_text] if part]
    return "\n\n".join(correction_parts) if correction_parts else None


def propose_asset_analysis(
    *,
    asset_id: int,
    user_correction: str | None,
    db: Session,
) -> AssetAnalysisProposalResponse:
    asset = get_asset_or_404(asset_id, db)

    try:
        contextual_correction = build_event_context_correction(
            asset,
            db,
            user_correction=user_correction,
        )

        proposed = analyze_media(
            asset.file_path,
            asset.media_type,
            user_correction=contextual_correction,
        )

        return AssetAnalysisProposalResponse(
            asset_id=asset.id,
            current_visual_summary=asset.vision_summary_generated,
            current_accessibility_text=asset.accessibility_text_generated,
            proposed_visual_summary=proposed.get("visual_summary"),
            proposed_accessibility_text=proposed.get("accessibility_text"),
            analysis_status=asset.analysis_status,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def apply_asset_analysis(
    *,
    asset_id: int,
    payload: AssetApplyAnalysisRequest,
    db: Session,
) -> AssetResponse:
    asset = get_asset_or_404(asset_id, db)

    asset.vision_summary_generated = payload.vision_summary_generated
    asset.accessibility_text_generated = payload.accessibility_text_generated
    asset.analysis_status = AssetStatus.ANALYZED
    asset.analysis_error_message = None

    db.add(asset)
    db.commit()
    db.refresh(asset)

    return build_asset_response(asset)


def approve_asset_record(
    *,
    asset_id: int,
    payload: AssetApproveRequest,
    db: Session,
) -> AssetApproveResponse:
    asset = get_asset_or_404(asset_id, db)

    asset.accessibility_text_final = payload.accessibility_text_final
    asset.analysis_status = AssetStatus.APPROVED
    asset.analysis_error_message = None

    db.add(asset)
    db.commit()
    db.refresh(asset)

    return AssetApproveResponse(
        asset_id=asset.id,
        analysis_status=asset.analysis_status,
        accessibility_text_final=asset.accessibility_text_final or "",
    )


def rename_asset_record(asset_id: int, display_name: str | None, db: Session) -> dict:
    asset = get_asset_or_404(asset_id, db)
    asset.display_name = display_name

    db.add(asset)
    db.commit()
    db.refresh(asset)

    return {"id": asset.id, "display_name": asset.display_name}


def update_asset_event_record(asset_id: int, event_id: int | None, db: Session) -> AssetResponse:
    asset = get_asset_or_404(asset_id, db)

    if event_id is not None:
        event = db.query(Event).filter(Event.id == event_id).first()
        if not event:
            raise HTTPException(status_code=404, detail="Event not found")

    asset.event_id = event_id

    db.add(asset)
    db.commit()
    db.refresh(asset)

    return build_asset_response(asset)


def delete_asset_record(asset_id: int, db: Session) -> dict:
    asset = get_asset_or_404(asset_id, db)

    post = db.query(Post).filter(Post.primary_asset_id == asset_id).first()
    if post:
        raise HTTPException(status_code=400, detail="Asset is in use")

    db.delete(asset)
    db.commit()
    return {"status": "deleted"}
