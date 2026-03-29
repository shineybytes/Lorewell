from pathlib import Path

from tests.helpers import create_event, upload_asset, write_temp_file


def test_upload_rejects_png(client):
    event_id = create_event(client)
    media_path = write_temp_file("tests_temp_image.png", b"fake png bytes")

    try:
        with media_path.open("rb") as f:
            response = client.post(
                f"/events/{event_id}/assets",
                files={"file": ("tests_temp_image.png", f, "image/png")},
            )
        assert response.status_code == 400
        assert response.json()["detail"] == (
            "Unsupported file type. Only JPEG, MP4, and MOV are currently supported."
        )
    finally:
        if media_path.exists():
            media_path.unlink()


def test_upload_accepts_jpeg(client):
    event_id = create_event(client)
    media_path = write_temp_file("tests_temp_image.jpg", b"fake jpeg bytes")

    try:
        response = upload_asset(client, event_id, media_path, "image/jpeg")
        assert response["media_type"] == "image"
    finally:
        if media_path.exists():
            media_path.unlink()


def test_upload_accepts_mp4(client):
    event_id = create_event(client)
    media_path = write_temp_file("tests_temp_video.mp4", b"fake mp4 bytes")

    try:
        response = upload_asset(client, event_id, media_path, "video/mp4")
        assert response["media_type"] == "video"
    finally:
        if media_path.exists():
            media_path.unlink()


def test_upload_rejects_oversized_video(client, mocker):
    event_id = create_event(client)

    mocker.patch(
        "app.main.validate_media_file",
        return_value=("video", "Video exceeds 300 MB maximum size."),
    )

    media_path = write_temp_file("tests_temp_video.mp4", b"tiny bytes")

    try:
        with media_path.open("rb") as f:
            response = client.post(
                f"/events/{event_id}/assets",
                files={"file": ("tests_temp_video.mp4", f, "video/mp4")},
            )
        assert response.status_code == 400
        assert response.json()["detail"] == "Video exceeds 300 MB maximum size."
    finally:
        if media_path.exists():
            media_path.unlink()


def test_upload_writes_nonempty_file(client):
    event_id = create_event(
        client,
        title="Upload Test",
        event_type="test",
        location="here",
        event_date="2026-03-25T18:00:00",
        recap="test",
        keywords="test",
    )
    media_path = write_temp_file("tests_temp_image.jpg", b"nonempty image bytes")

    try:
        upload_resp = upload_asset(client, event_id, media_path, "image/jpeg")

        assets_resp = client.get(f"/events/{event_id}/assets")
        assert assets_resp.status_code == 200

        assets = assets_resp.json()
        asset = next(a for a in assets if a["id"] == upload_resp["asset_id"])

        assert Path(asset["file_path"]).stat().st_size > 0
    finally:
        if media_path.exists():
            media_path.unlink()
