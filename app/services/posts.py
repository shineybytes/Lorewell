from pathlib import Path

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.ai import generate_caption_package
from app.domain.statuses import PostStatus
from app.models import ApprovedPost, Asset, Event, Post
from app.schemas import (
    ApprovePostRequest,
    ApprovedPostResponse,
    PostDraftContentUpdate,
    PostDraftCreate,
    PostDraftCreateResponse,
    PostDraftUpdate,
    PostGenerateRequest,
    PostGenerationResponse,
)


def build_default_draft_title(event: Event | None, prefix: str = "Draft") -> str:
    if event and event.title:
        return f"{prefix} — {event.title}"
    return prefix


def get_post_or_404(post_id: int, db: Session) -> Post:
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    return post


def create_post_record(payload: PostDraftCreate, db: Session) -> PostDraftCreateResponse:
    asset = db.query(Asset).filter(Asset.id == payload.asset_id).first()
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")

    event = None
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
        working_title=build_default_draft_title(event, "Draft"),
        status=PostStatus.DRAFT,
    )

    db.add(post)
    db.commit()
    db.refresh(post)

    return PostDraftCreateResponse(post_id=post.id, status=post.status)


def generate_post_record(
    post_id: int,
    payload: PostGenerateRequest | None,
    db: Session,
) -> PostGenerationResponse:
    post = get_post_or_404(post_id, db)

    asset = db.query(Asset).filter(Asset.id == post.primary_asset_id).first()
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")

    event = None
    if post.event_id is not None:
        event = db.query(Event).filter(Event.id == post.event_id).first()

    seed_caption = payload.seed_caption if payload else None

    result = generate_caption_package(
        event,
        asset,
        post,
        seed_caption=seed_caption,
    )

    post.generated_caption_options = result.get("caption_option_1")
    post.generated_hashtag_options = " ".join(result.get("hashtags", []))
    post.generated_accessibility_options = (
        asset.accessibility_text_final or result.get("accessibility_text")
    )
    post.status = PostStatus.GENERATED
    post.error_message = None

    db.add(post)
    db.commit()
    db.refresh(post)

    return PostGenerationResponse(
        post_id=post.id,
        status=post.status,
        caption_option_1=result.get("caption_option_1"),
        caption_option_2=result.get("caption_option_2"),
        caption_option_3=result.get("caption_option_3"),
        hashtags=result.get("hashtags", []),
        accessibility_text=post.generated_accessibility_options,
        seo_keywords=result.get("seo_keywords", []),
        visual_summary=result.get("visual_summary"),
        credits=result.get("credits"),
    )


def approve_post_record(
    post_id: int,
    payload: ApprovePostRequest,
    db: Session,
) -> ApprovedPostResponse:
    post = get_post_or_404(post_id, db)

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

    post.status = PostStatus.APPROVED

    db.add(approved)
    db.add(post)
    db.commit()
    db.refresh(approved)

    return ApprovedPostResponse(
        approved_post_id=approved.id,
        status=PostStatus.APPROVED,
    )


def list_post_records(db: Session) -> list[dict]:
    posts = db.query(Post).order_by(Post.created_at.desc()).all()

    results = []
    for p in posts:
        event = (
            db.query(Event).filter(Event.id == p.event_id).first()
            if p.event_id
            else None
        )
        asset = (
            db.query(Asset).filter(Asset.id == p.primary_asset_id).first()
            if p.primary_asset_id
            else None
        )

        asset_filename = None
        if asset and asset.file_path:
            asset_filename = Path(asset.file_path).name

        results.append(
            {
                "id": p.id,
                "event_id": p.event_id,
                "asset_id": p.primary_asset_id,
                "status": p.status,
                "created_at": p.created_at.isoformat(),
                "event_title": event.title if event else None,
                "event_date": (
                    event.event_date.isoformat()
                    if event and event.event_date
                    else None
                ),
                "asset_filename": asset_filename,
                "draft_caption_current": p.draft_caption_current,
                "working_title": p.working_title,
            }
        )

    return results


def get_post_record(post_id: int, db: Session) -> dict:
    post = get_post_or_404(post_id, db)

    approved = (
        db.query(ApprovedPost)
        .filter(ApprovedPost.post_id == post.id)
        .order_by(ApprovedPost.id.desc())
        .first()
    )

    return {
        "id": post.id,
        "event_id": post.event_id,
        "asset_id": post.primary_asset_id,
        "brand_voice": post.brand_voice,
        "cta_goal": post.cta_goal,
        "generation_notes": post.generation_notes,
        "working_title": post.working_title,
        "generated_caption_options": post.generated_caption_options,
        "generated_hashtag_options": post.generated_hashtag_options,
        "generated_accessibility_options": post.generated_accessibility_options,
        "approved_caption_final": approved.caption_final if approved else None,
        "approved_hashtags_final": approved.hashtags_final if approved else None,
        "approved_accessibility_text": approved.accessibility_text if approved else None,
        "draft_caption_current": post.draft_caption_current,
        "draft_hashtags_current": post.draft_hashtags_current,
        "draft_accessibility_current": post.draft_accessibility_current,
        "status": post.status,
        "error_message": post.error_message,
        "created_at": post.created_at.isoformat(),
    }


def update_post_record(
    post_id: int,
    payload: PostDraftUpdate,
    db: Session,
) -> PostDraftCreateResponse:
    post = get_post_or_404(post_id, db)

    post.brand_voice = payload.brand_voice
    post.cta_goal = payload.cta_goal
    post.generation_notes = payload.generation_notes
    post.working_title = payload.working_title

    db.add(post)
    db.commit()
    db.refresh(post)

    return PostDraftCreateResponse(post_id=post.id, status=post.status)


def update_post_draft_content_record(
    post_id: int,
    payload: PostDraftContentUpdate,
    db: Session,
) -> dict:
    post = get_post_or_404(post_id, db)

    post.draft_caption_current = payload.draft_caption_current
    post.draft_hashtags_current = payload.draft_hashtags_current
    post.draft_accessibility_current = payload.draft_accessibility_current

    db.add(post)
    db.commit()
    db.refresh(post)

    return {
        "post_id": post.id,
        "status": post.status,
        "draft_caption_current": post.draft_caption_current,
        "draft_hashtags_current": post.draft_hashtags_current,
        "draft_accessibility_current": post.draft_accessibility_current,
    }


def fork_approved_post_to_draft_record(
    approved_post_id: int,
    db: Session,
) -> PostDraftCreateResponse:
    approved = (
        db.query(ApprovedPost)
        .filter(ApprovedPost.id == approved_post_id)
        .first()
    )
    if not approved:
        raise HTTPException(status_code=404, detail="ApprovedPost not found")

    source_post = db.query(Post).filter(Post.id == approved.post_id).first()
    if not source_post:
        raise HTTPException(status_code=404, detail="Source Post not found")

    event = None
    if source_post.event_id:
        event = db.query(Event).filter(Event.id == source_post.event_id).first()

    draft = Post(
        event_id=source_post.event_id,
        primary_asset_id=approved.selected_asset_id,
        brand_voice=source_post.brand_voice,
        cta_goal=source_post.cta_goal,
        generation_notes=source_post.generation_notes,
        working_title=build_default_draft_title(event, "Revision Draft"),
        draft_caption_current=approved.caption_final,
        draft_hashtags_current=approved.hashtags_final,
        draft_accessibility_current=approved.accessibility_text,
        status=PostStatus.DRAFT,
    )

    db.add(draft)
    db.commit()
    db.refresh(draft)

    return PostDraftCreateResponse(post_id=draft.id, status=draft.status)


def delete_post_record(post_id: int, db: Session) -> dict:
    post = get_post_or_404(post_id, db)
    db.delete(post)
    db.commit()
    return {"status": "deleted"}
