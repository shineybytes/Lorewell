from sqlalchemy.orm import Session

from app.domain.statuses import PostStatus
from app.models import ApprovedPost, Asset


def list_approved_post_records(db: Session) -> list[dict]:
    approved_posts = db.query(ApprovedPost).all()

    results = []
    for a in approved_posts:
        asset = db.query(Asset).filter(Asset.id == a.selected_asset_id).first()

        results.append(
            {
                "id": a.id,
                "post_id": a.post_id,
                "selected_asset_id": a.selected_asset_id,
                "caption_final": a.caption_final,
                "hashtags_final": a.hashtags_final.split()
                if a.hashtags_final
                else [],
                "accessibility_text": a.accessibility_text,
                "status": PostStatus.APPROVED,
                "asset_file_path": asset.file_path if asset else None,
                "asset_media_type": asset.media_type if asset else None,
            }
        )

    return results
