from tests.helpers import create_event, create_post, upload_asset, write_temp_file


def test_create_event(client):
    response = client.post(
        "/events",
        json={
            "title": "Test Event",
            "event_type": "dj set",
            "location": "San Diego",
            "event_date": "2026-03-19T01:00:00",
            "event_timezone": "America/Los_Angeles",
            "recap": "Test recap",
            "keywords": "dj,test",
            "vendors": "Venue X",
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert "id" in body
    assert body["title"] == "Test Event"
    assert body["event_type"] == "dj set"


def test_create_post(client):
    event_id = create_event(client)
    media_path = write_temp_file("tests_temp_image.jpg", b"fake image bytes")

    try:
        asset = upload_asset(client, event_id, media_path, "image/jpeg")
        post_id = create_post(
            client,
            event_id=event_id,
            asset_id=asset["asset_id"],
            generation_notes="Keep it short and lively.",
        )

        assert post_id is not None
    finally:
        if media_path.exists():
            media_path.unlink()


def test_generate_post_stores_caption(client, mocker):
    mocker.patch(
        "app.main.generate_caption_package",
        return_value={
            "caption_short": "short",
            "caption_medium": "medium caption",
            "caption_long": "long",
            "hashtags": ["one", "two"],
            "accessibility_text": "alt text",
            "seo_keywords": ["dj"],
            "visual_summary": "summary",
        },
    )

    event_id = create_event(client)
    media_path = write_temp_file("tests_temp_image.jpg", b"fake image bytes")

    try:
        asset = upload_asset(client, event_id, media_path, "image/jpeg")
        post_id = create_post(client, event_id=event_id, asset_id=asset["asset_id"])

        generate_resp = client.post(f"/posts/{post_id}/generate")
        assert generate_resp.status_code == 200

        body = generate_resp.json()
        assert body["caption_medium"] == "medium caption"
        assert body["hashtags"] == ["one", "two"]
        assert body["accessibility_text"] == "alt text"

        posts_resp = client.get("/posts")
        posts = posts_resp.json()
        saved = next(p for p in posts if p["id"] == post_id)

        assert saved["status"] == "generated"
    finally:
        if media_path.exists():
            media_path.unlink()


def test_approve_post_changes_status(client):
    event_id = create_event(client)
    media_path = write_temp_file("tests_temp_image.jpg", b"fake image bytes")

    try:
        asset = upload_asset(client, event_id, media_path, "image/jpeg")
        post_id = create_post(client, event_id=event_id, asset_id=asset["asset_id"])

        approve_resp = client.post(
            f"/posts/{post_id}/approve",
            json={
                "caption_final": "approved caption",
                "hashtags_final": ["dj", "test"],
                "accessibility_text": "alt text",
            },
        )
        assert approve_resp.status_code == 200
        assert approve_resp.json()["status"] == "approved"
    finally:
        if media_path.exists():
            media_path.unlink()
