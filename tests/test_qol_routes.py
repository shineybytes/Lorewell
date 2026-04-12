from tests.helpers import create_event, create_post, upload_asset, write_temp_file


def test_delete_post_removes_draft(client, create_event, create_asset, create_post):
    event_id = create_event()
    asset_id = create_asset(event_id)
    post_id = create_post(event_id=event_id, asset_id=asset_id)

    response = client.delete(f"/posts/{post_id}")
    assert response.status_code == 200
    assert response.json()["status"] == "deleted"

    get_response = client.get(f"/posts/{post_id}")
    assert get_response.status_code == 404


def test_delete_asset_blocks_when_in_use(client, create_event, create_asset, create_post):
    event_id = create_event()
    asset_id = create_asset(event_id)
    create_post(event_id=event_id, asset_id=asset_id)

    response = client.delete(f"/assets/{asset_id}")
    assert response.status_code == 400
    assert response.json()["detail"] == "Asset is in use"


def test_delete_asset_succeeds_when_unused(client):
    event_id = create_event(client)
    media_path = write_temp_file("tests_temp_delete_unused.jpg", b"fake jpeg bytes")

    try:
        asset = upload_asset(client, event_id, media_path, "image/jpeg")
        asset_id = asset["asset_id"]

        response = client.delete(f"/assets/{asset_id}")
        assert response.status_code == 200
        assert response.json()["status"] == "deleted"

        get_response = client.get(f"/assets/{asset_id}")
        assert get_response.status_code == 404
    finally:
        if media_path.exists():
            media_path.unlink()


def test_delete_event_detaches_assets_and_posts(client):
    event_id = create_event(client)
    media_path = write_temp_file("tests_temp_detach_event.jpg", b"fake jpeg bytes")

    try:
        asset = upload_asset(client, event_id, media_path, "image/jpeg")
        asset_id = asset["asset_id"]

        post_resp = client.post(
            "/posts",
            json={
                "event_id": event_id,
                "asset_id": asset_id,
                "brand_voice": "warm",
                "cta_goal": "book now",
                "generation_notes": "detach regression",
            },
        )
        assert post_resp.status_code == 200
        post_id = post_resp.json()["post_id"]

        delete_resp = client.delete(f"/events/{event_id}")
        assert delete_resp.status_code == 200
        assert delete_resp.json()["status"] == "deleted"

        get_event = client.get(f"/events/{event_id}")
        assert get_event.status_code == 404

        get_asset = client.get(f"/assets/{asset_id}")
        assert get_asset.status_code == 200
        assert get_asset.json()["event_id"] is None

        get_post = client.get(f"/posts/{post_id}")
        assert get_post.status_code == 200
        assert get_post.json()["event_id"] is None
    finally:
        if media_path.exists():
            media_path.unlink()


def test_retry_failed_schedule_creates_new_schedule(client, approved_post_factory, failed_schedule_factory):
    approved_post_id = approved_post_factory()
    failed_schedule = failed_schedule_factory(approved_post_id=approved_post_id)

    response = client.post(f"/schedules/{failed_schedule.id}/retry")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "scheduled"

    schedules = client.get("/schedules")
    assert schedules.status_code == 200
    data = schedules.json()
    matching = [s for s in data if s["approved_post_id"] == approved_post_id]
    assert len(matching) >= 2


def test_retry_non_failed_schedule_rejected(client, approved_post_factory, schedule_factory):
    approved_post_id = approved_post_factory()
    schedule = schedule_factory(approved_post_id=approved_post_id)

    response = client.post(f"/schedules/{schedule['schedule_id']}/retry")
    assert response.status_code == 400
    assert response.json()["detail"] == "Only failed schedules can be retried"


def test_archive_all_failed_marks_unacknowledged_failures(client, failed_schedule_factory, approved_post_factory):
    approved_post_id = approved_post_factory()
    failed_schedule_factory(approved_post_id=approved_post_id, acknowledged=False)
    failed_schedule_factory(approved_post_id=approved_post_id, acknowledged=False)

    response = client.post("/schedules/archive-all-failed")
    assert response.status_code == 200
    assert response.json()["count"] == 2

    schedules = client.get("/schedules").json()
    failed = [s for s in schedules if s["status"] == "failed"]
    assert all(s["failure_acknowledged"] is True for s in failed)


def test_restore_all_failed_marks_archived_failures_unacknowledged(client, failed_schedule_factory, approved_post_factory):
    approved_post_id = approved_post_factory()
    failed_schedule_factory(approved_post_id=approved_post_id, acknowledged=True)
    failed_schedule_factory(approved_post_id=approved_post_id, acknowledged=True)

    response = client.post("/schedules/restore-all-failed")
    assert response.status_code == 200
    assert response.json()["count"] == 2

    schedules = client.get("/schedules").json()
    failed = [s for s in schedules if s["status"] == "failed"]
    assert all(s["failure_acknowledged"] is False for s in failed)
