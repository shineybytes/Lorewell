from tests.helpers import approve_post, create_event, create_post, upload_asset, write_temp_file


def test_schedule_list_includes_error_and_instagram_fields(client):
    event_id = create_event(client)
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

        schedules_resp = client.get("/schedules")
        assert schedules_resp.status_code == 200

        body = schedules_resp.json()
        created = body[-1]
        assert created["approved_post_id"] == approved_post_id
        assert created["status"] == "scheduled"
        assert created["error_message"] is None
        assert created["published_instagram_id"] is None
    finally:
        if media_path.exists():
            media_path.unlink()


def test_schedule_rejects_missing_approved_post(client):
    resp = client.post(
        "/approved-posts/999999/schedule",
        json={
            "publish_at": "2026-03-25T18:30:00",
            "publish_timezone": "America/Los_Angeles",
        },
    )

    assert resp.status_code == 404
    assert resp.json()["detail"] == "ApprovedPost not found"
