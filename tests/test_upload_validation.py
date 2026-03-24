from pathlib import Path


def create_event(client):
    response = client.post(
        "/events",
        json={
            "title": "Test Event",
            "event_type": "dj set",
            "location": "San Diego",
            "event_date": "2026-03-19T01:00:00",
            "notes": "Test notes",
            "keywords": "dj,test",
            "brand_voice": "energetic",
            "cta": "Follow for more",
        },
    )
    return response.json()["id"]


def test_upload_rejects_png(client):
    event_id = create_event(client)

    media_path = Path("tests_temp_image.png")
    media_path.write_bytes(b"fake png bytes")

    try:
        with media_path.open("rb") as f:
            response = client.post(
                f"/events/{event_id}/upload",
                files={"file": ("tests_temp_image.png", f, "image/png")},
            )
        assert response.status_code == 400
        assert response.json()["detail"] == "Unsupported file type. Only JPEG, MP4, and MOV are currently supported."
    finally:
        if media_path.exists():
            media_path.unlink()


def test_upload_accepts_jpeg(client):
    event_id = create_event(client)

    media_path = Path("tests_temp_image.jpg")
    media_path.write_bytes(b"fake jpeg bytes")

    try:
        with media_path.open("rb") as f:
            response = client.post(
                f"/events/{event_id}/upload",
                files={"file": ("tests_temp_image.jpg", f, "image/jpeg")},
            )
        assert response.status_code == 200
        assert response.json()["media_type"] == "image"
    finally:
        if media_path.exists():
            media_path.unlink()


def test_upload_accepts_mp4(client):
    event_id = create_event(client)

    media_path = Path("tests_temp_video.mp4")
    media_path.write_bytes(b"fake mp4 bytes")

    try:
        with media_path.open("rb") as f:
            response = client.post(
                f"/events/{event_id}/upload",
                files={"file": ("tests_temp_video.mp4", f, "video/mp4")},
            )
        assert response.status_code == 200
        assert response.json()["media_type"] == "video"
    finally:
        if media_path.exists():
            media_path.unlink()

def test_upload_rejects_oversized_video(client, mocker):
    event_id = create_event(client)

    mocker.patch(
        "app.main.validate_media_file",
        return_value=("video", "Video exceeds 300 MB maximum size."),
    )

    media_path = Path("tests_temp_video.mp4")
    media_path.write_bytes(b"tiny bytes")

    try:
        with media_path.open("rb") as f:
            response = client.post(
                f"/events/{event_id}/upload",
                files={"file": ("tests_temp_video.mp4", f, "video/mp4")},
            )
        assert response.status_code == 400
        assert response.json()["detail"] == "Video exceeds 300 MB maximum size."
    finally:
        if media_path.exists():
            media_path.unlink()

def test_upload_writes_nonempty_file(client):
    event_resp = client.post(
        "/events",
        json={
            "title": "Upload Test",
            "event_type": "test",
            "location": "here",
            "event_date": "2026-03-25T18:00:00",
            "notes": "test",
            "keywords": "test",
            "brand_voice": "neutral",
            "cta": "none",
        },
    )
    event_id = event_resp.json()["id"]

    from pathlib import Path
    media_path = Path("tests_temp_image.jpg")
    media_path.write_bytes(b"nonempty image bytes")

    try:
        with media_path.open("rb") as f:
            upload_resp = client.post(
                f"/events/{event_id}/upload",
                files={"file": ("tests_temp_image.jpg", f, "image/jpeg")},
            )
        assert upload_resp.status_code == 200

        from app.db import SessionLocal
        from app.models import Asset
        db = SessionLocal()
        try:
            asset = db.query(Asset).filter(Asset.id == upload_resp.json()["asset_id"]).first()
            assert asset is not None
            assert Path(asset.file_path).stat().st_size > 0
        finally:
            db.close()
    finally:
        if media_path.exists():
            media_path.unlink()
