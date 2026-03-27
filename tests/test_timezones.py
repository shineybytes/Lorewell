def test_create_post_converts_local_time_to_utc(client):
    event_resp = client.post(
        "/events",
        json={
            "title": "TZ Test Event",
            "event_type": "dj set",
            "location": "San Diego",
            "event_date": "2026-03-25T18:00:00",
            "notes": "timezone test",
            "keywords": "dj,test",
            "brand_voice": "energetic",
            "cta": "Follow for more",
        },
    )
    event_id = event_resp.json()["id"]

    from pathlib import Path
    media_path = Path("tests_temp_image.jpg")
    media_path.write_bytes(b"fake jpeg bytes")

    try:
        with media_path.open("rb") as f:
            upload_resp = client.post(
                f"/events/{event_id}/upload",
                files={"file": ("tests_temp_image.jpg", f, "image/jpeg")},
            )
        asset_id = upload_resp.json()["asset_id"]

        # create draft
        post_resp = client.post(
            "/posts",
            json={
                "event_id": event_id,
                "asset_id": asset_id,
            },
        )
        post_id = post_resp.json()["post_id"]

        # approve
        approve_resp = client.post(
            f"/posts/{post_id}/approve",
            json={
                "caption_final": "caption",
                "hashtags_final": "#one",
                "accessibility_text": "alt",
            },
        )
        approved_post_id = approve_resp.json()["approved_post_id"]

        # schedule
        schedule_resp = client.post(
            f"/approved-posts/{approved_post_id}/schedule",
            json={
                "publish_at": "2026-03-25T18:30:00",
                "publish_timezone": "America/Los_Angeles",
            },
        )
        assert schedule_resp.status_code == 200

        schedules = client.get("/schedules").json()
        created = schedules[-1]

        assert created["publish_timezone"] == "America/Los_Angeles"
        assert created["publish_at"] == "2026-03-26T01:30:00"

    finally:
        if media_path.exists():
            media_path.unlink()

def test_create_post_rejects_invalid_timezone(client):
    event_resp = client.post(
        "/events",
        json={
            "title": "TZ Invalid Event",
            "event_type": "dj set",
            "location": "San Diego",
            "event_date": "2026-03-25T18:00:00",
            "notes": "timezone test",
            "keywords": "dj,test",
            "brand_voice": "energetic",
            "cta": "Follow for more",
        },
    )
    event_id = event_resp.json()["id"]

    from pathlib import Path
    media_path = Path("tests_temp_image.jpg")
    media_path.write_bytes(b"fake jpeg bytes")

    try:
        with media_path.open("rb") as f:
            upload_resp = client.post(
                f"/events/{event_id}/upload",
                files={"file": ("tests_temp_image.jpg", f, "image/jpeg")},
            )
        asset_id = upload_resp.json()["asset_id"]

        post_id = client.post(
            "/posts",
            json={"event_id": event_id, "asset_id": asset_id},
        ).json()["post_id"]

        approved_post_id = client.post(
            f"/posts/{post_id}/approve",
            json={
                "caption_final": "caption",
                "hashtags_final": "#one",
                "accessibility_text": "alt",
            },
        ).json()["approved_post_id"]

        resp = client.post(
            f"/approved-posts/{approved_post_id}/schedule",
            json={
                "publish_at": "2026-03-25T18:30:00",
                "publish_timezone": "Mars/Olympus",
            },
        )

        assert resp.status_code == 400
        assert resp.json()["detail"] == "Invalid timezone"

    finally:
        if media_path.exists():
            media_path.unlink()

def test_convert_time_rejects_timezone_aware_input(client):
    resp = client.post(
        "/time/convert",
        json={
            "local_datetime": "2026-03-25T18:30:00Z",
            "timezone": "America/Los_Angeles",
        },
    )
    assert resp.status_code == 400
    assert "local_datetime must not include a timezone" in resp.json()["detail"]

def test_create_post_rejects_timezone_aware_publish_at(client):
    event_resp = client.post(
        "/events",
        json={
            "title": "TZ Invalid Publish Event",
            "event_type": "dj set",
            "location": "San Diego",
            "event_date": "2026-03-25T18:00:00",
            "notes": "timezone test",
            "keywords": "dj,test",
            "brand_voice": "energetic",
            "cta": "Follow for more",
        },
    )
    event_id = event_resp.json()["id"]

    from pathlib import Path
    media_path = Path("tests_temp_image.jpg")
    media_path.write_bytes(b"fake jpeg bytes")

    try:
        with media_path.open("rb") as f:
            upload_resp = client.post(
                f"/events/{event_id}/upload",
                files={"file": ("tests_temp_image.jpg", f, "image/jpeg")},
            )
        asset_id = upload_resp.json()["asset_id"]

        post_id = client.post(
            "/posts",
            json={"event_id": event_id, "asset_id": asset_id},
        ).json()["post_id"]

        approved_post_id = client.post(
            f"/posts/{post_id}/approve",
            json={
                "caption_final": "caption",
                "hashtags_final": "#one",
                "accessibility_text": "alt",
            },
        ).json()["approved_post_id"]

        resp = client.post(
            f"/approved-posts/{approved_post_id}/schedule",
            json={
                "publish_at": "2026-03-25T18:30:00Z",
                "publish_timezone": "America/Los_Angeles",
            },
        )

        assert resp.status_code == 400
        assert "publish_at must not include timezone" in resp.json()["detail"]

    finally:
        if media_path.exists():
            media_path.unlink()
