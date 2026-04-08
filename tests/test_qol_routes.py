from pathlib import Path


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


def test_delete_event_blocks_when_assets_exist(client, create_event, create_asset):
    event_id = create_event()
    create_asset(event_id)

    response = client.delete(f"/events/{event_id}")
    assert response.status_code == 400
    assert response.json()["detail"] == "Event has assets"


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
