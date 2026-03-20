from pathlib import Path
import time
import requests
from app.config import settings


def public_media_url(file_path: str) -> str:
    filename = Path(file_path).name
    return f"{settings.app_base_url}/media/{filename}"


def create_media_container(file_path: str, caption: str, media_type: str) -> str:
    url = f"https://graph.facebook.com/{settings.graph_api_version}/{settings.instagram_account_id}/media"
    payload = {
        "access_token": settings.page_access_token,
        "caption": caption,
    }

    media_url = public_media_url(file_path)

    if media_type == "image":
        payload["image_url"] = media_url
    else:
        payload["media_type"] = "REELS"
        payload["video_url"] = media_url

    r = requests.post(url, data=payload, timeout=60)
    if not r.ok:
        raise RuntimeError(f"Meta create_media_container failed: {r.status_code} {r.text}")
    return r.json()["id"]


def publish_container(container_id: str) -> str:
    url = f"https://graph.facebook.com/{settings.graph_api_version}/{settings.instagram_account_id}/media_publish"
    payload = {
        "creation_id": container_id,
        "access_token": settings.page_access_token,
    }
    last_error = None
    for attempt in range(10):
        r = requests.post(url, data=payload, timeout=60)
        if r.ok:
            return r.json()["id"]
        last_error = f"{r.status_code} {r.text}"
        if "Media ID is not available" in r.text or "not ready for publishing" in r.text:
            time.sleep(5)
            continue
        raise RuntimeError(f"Meta publish_container failed: {last_error}")
    raise RuntimeError(f"Meta publish_container failed after retries: {last_error}")
    
