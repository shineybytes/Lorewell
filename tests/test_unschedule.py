from app.models import Schedule
from tests.helpers import approve_post, create_event, create_post, upload_asset, write_temp_file


def test_unschedule_deletes_schedule(client):
    event_id = create_event(client)
    media_path = write_temp_file("tests_temp_unschedule.jpg", b"fake jpeg bytes")

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
        schedule_id = schedule_resp.json()["schedule_id"]

        delete_resp = client.delete(f"/schedules/{schedule_id}")
        assert delete_resp.status_code == 200
        assert delete_resp.json()["status"] == "deleted"

        schedules = client.get("/schedules").json()
        assert all(s["id"] != schedule_id for s in schedules)
    finally:
        if media_path.exists():
            media_path.unlink()


def test_unschedule_missing_schedule_returns_404(client):
    response = client.delete("/schedules/999999")
    assert response.status_code == 404
    assert response.json()["detail"] == "Schedule not found"


def test_unschedule_published_schedule_rejected(client, db_session):
    event_id = create_event(client)
    media_path = write_temp_file("tests_temp_published_unschedule.jpg", b"fake jpeg bytes")

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
        schedule_id = schedule_resp.json()["schedule_id"]

        schedule = db_session.query(Schedule).filter(Schedule.id == schedule_id).first()
        assert schedule is not None
        schedule.status = "published"
        db_session.add(schedule)
        db_session.commit()

        response = client.delete(f"/schedules/{schedule_id}")
        assert response.status_code == 400
        assert response.json()["detail"] == "Published schedules cannot be unscheduled"
    finally:
        if media_path.exists():
            media_path.unlink()
