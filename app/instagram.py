from pathlib import Path
import time
import requests
from app.config import settings

PUBLISH_RETRY_INTERVAL_SECONDS = 10
PUBLISH_MAX_WAIT_SECONDS = 600


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

def get_container_status(container_id: str) -> dict:
    url = f"https://graph.facebook.com/{settings.graph_api_version}/{container_id}"
    params = {
            "fields" : "status,status_code",
            "access_token": settings.page_access_token,
    }
    r = requests.get(url, params=params, timeout=60)
    if not r.ok:
        raise RuntimeError(f"Meta get_container_status failed: {r.status_code} {r.text}")
    return r.json()

def wait_until_container_ready(container_id: str) -> None:
    attempts = PUBLISH_MAX_WAIT_SECONDS // PUBLISH_RETRY_INTERVAL_SECONDS
    last_status = None
    for _ in range(attempts):
        status_data = get_container_status(container_id)
        last_status = status_data

        status_code = status_data.get("status_code")
        status = status_data.get("status")
        if status_code == "FINISHED":
            return
        if status_code in {"ERROR", "EXPIRED"}:
            raise RuntimeError(f"Meta container failed: {status_data}")
        time.sleep(PUBLISH_RETRY_INTERVAL_SECONDS)
    raise RuntimeError(f"Meta container not ready after waiting: {last_status}")


def publish_container(container_id: str) -> str:
    # raise Exception("Meta create_media_container failed: 400 test")
    url = f"https://graph.facebook.com/{settings.graph_api_version}/{settings.instagram_account_id}/media_publish"
    payload = {
        "creation_id": container_id,
        "access_token": settings.page_access_token,
    }
    last_error = None
    attempts = PUBLISH_MAX_WAIT_SECONDS // PUBLISH_RETRY_INTERVAL_SECONDS
    
    for attempt in range(attempts):
        r = requests.post(url, data=payload, timeout=60)
        if r.ok:
            return r.json()["id"]
        last_error = f"{r.status_code} {r.text}"
        if "Media ID is not available" in r.text or "not ready for publishing" in r.text:
            time.sleep(PUBLISH_RETRY_INTERVAL_SECONDS)
            continue
        raise RuntimeError(f"Meta publish_container failed: {last_error}")
    raise RuntimeError(f"Meta publish_container failed after retries: {last_error}")
    
