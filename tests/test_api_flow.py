def test_create_event(client):
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
    assert response.status_code == 200
    body = response.json()
    assert "id" in body


def test_create_post(client):
    event_resp = client.post(
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
    event_id = event_resp.json()["id"]

    from pathlib import Path
    media_path = Path("tests_temp_image.jpg")
    media_path.write_bytes(b"fake image bytes")

    try:
        with media_path.open("rb") as f:
            upload_resp = client.post(
                f"/events/{event_id}/upload",
                files={"file": ("tests_temp_image.jpg", f, "image/jpeg")},
            )
        assert upload_resp.status_code == 200
        asset_id = upload_resp.json()["asset_id"]

        post_resp = client.post(
            "/posts",
            json={
                "event_id": event_id,
                "asset_id": asset_id,
                "publish_at": "2026-03-19T01:42:00",
            },
        )
        assert post_resp.status_code == 200
        assert post_resp.json()["status"] == "draft"
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
            "hashtags": ["#one", "#two"],
            "accessibility_text": "alt text",
            "seo_keywords": ["dj"],
            "visual_summary": "summary",
        },
    )

    event_resp = client.post(
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
    event_id = event_resp.json()["id"]

    from pathlib import Path
    media_path = Path("tests_temp_image.jpg")
    media_path.write_bytes(b"fake image bytes")

    try:
        with media_path.open("rb") as f:
            upload_resp = client.post(
                f"/events/{event_id}/upload",
                files={"file": ("tests_temp_image.jpg", f, "image/jpeg")},
            )
        asset_id = upload_resp.json()["asset_id"]

        post_resp = client.post(
            "/posts",
            json={
                "event_id": event_id,
                "asset_id": asset_id,
                "publish_at": "2026-03-19T01:42:00",
            },
        )
        post_id = post_resp.json()["post_id"]

        generate_resp = client.post("/posts/generate", json={"post_id": post_id})
        assert generate_resp.status_code == 200
        assert generate_resp.json()["caption_medium"] == "medium caption"

        posts_resp = client.get("/posts")
        posts = posts_resp.json()
        saved = next(p for p in posts if p["id"] == post_id)
        assert saved["caption_final"] == "medium caption"
        assert saved["hashtags_final"] == "#one #two"
    finally:
        if media_path.exists():
            media_path.unlink()


def test_approve_post_changes_status(client):
    event_resp = client.post(
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
    event_id = event_resp.json()["id"]

    from pathlib import Path
    media_path = Path("tests_temp_image.jpg")
    media_path.write_bytes(b"fake image bytes")

    try:
        with media_path.open("rb") as f:
            upload_resp = client.post(
                f"/events/{event_id}/upload",
                files={"file": ("tests_temp_image.jpg", f, "image/jpeg")},
            )
        asset_id = upload_resp.json()["asset_id"]

        post_resp = client.post(
            "/posts",
            json={
                "event_id": event_id,
                "asset_id": asset_id,
                "publish_at": "2026-03-19T01:42:00",
            },
        )
        post_id = post_resp.json()["post_id"]

        approve_resp = client.post(
            f"/posts/{post_id}/approve",
            json={
                "caption_final": "approved caption",
                "hashtags_final": "#dj #test",
                "accessibility_text": "alt text",
            },
        )
        assert approve_resp.status_code == 200
        assert approve_resp.json()["status"] == "approved"
    finally:
        if media_path.exists():
            media_path.unlink()
