from tests.helpers import approve_post, create_event, create_post, upload_asset, write_temp_file


def test_create_post_converts_local_time_to_utc(client):
    event_id = create_event(
        client,
        title="TZ Test Event",
        event_date="2026-03-25T18:00:00",
        recap="timezone test",
    )
    media_path = write_temp_file("tests_temp_image.jpg", b"fake jpeg bytes")

    try:
        asset = upload_asset(client, event_id, media_path, "image/jpeg")
        post_id = create_post(client, event_id=event_id, asset_id=asset["asset_id"])
        approved_post_id = approve_post(
            client,
            post_id=post_id,
            caption_final="caption",
            hashtags_final=["one"],
            accessibility_text="alt",
        )

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
    event_id = create_event(
        client,
        title="TZ Invalid Event",
        event_date="2026-03-25T18:00:00",
        recap="timezone test",
    )
    media_path = write_temp_file("tests_temp_image.jpg", b"fake jpeg bytes")

    try:
        asset = upload_asset(client, event_id, media_path, "image/jpeg")
        post_id = create_post(client, event_id=event_id, asset_id=asset["asset_id"])
        approved_post_id = approve_post(
            client,
            post_id=post_id,
            caption_final="caption",
            hashtags_final=["one"],
            accessibility_text="alt",
        )

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
    event_id = create_event(
        client,
        title="TZ Invalid Publish Event",
        event_date="2026-03-25T18:00:00",
        recap="timezone test",
    )
    media_path = write_temp_file("tests_temp_image.jpg", b"fake jpeg bytes")

    try:
        asset = upload_asset(client, event_id, media_path, "image/jpeg")
        post_id = create_post(client, event_id=event_id, asset_id=asset["asset_id"])
        approved_post_id = approve_post(
            client,
            post_id=post_id,
            caption_final="caption",
            hashtags_final=["one"],
            accessibility_text="alt",
        )

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
