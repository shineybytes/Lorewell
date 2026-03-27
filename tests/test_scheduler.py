from datetime import datetime

class FakeAsset:
    def __init__(self):
        self.id = 1
        self.file_path = "media/test.jpg"
        self.media_type = "image"

class FakeSchedule:
    def __init__(self):
        self.status = "scheduled"
        self.publish_at = datetime.utcnow()
        self.approved_post_id = 1
        self.published_instagram_id = None
        self.error_message = None

class FakeApprovedPost:
    def __init__(self):
        self.id = 1
        self.selected_asset_id = 1
        self.caption_final = "caption"
        self.hashtags_final = "#one #two"


def test_scheduler_processes_approved_posts_in_window(mocker):
    fake_schedule = FakeSchedule()
    fake_approved = FakeApprovedPost()
    fake_asset = FakeAsset()

    schedules_query = mocker.Mock()
    schedules_query.filter.return_value = schedules_query
    schedules_query.all.return_value = [fake_schedule]

    approved_query = mocker.Mock()
    approved_query.filter.return_value = approved_query
    approved_query.first.return_value = fake_approved

    asset_query = mocker.Mock()
    asset_query.filter.return_value = asset_query
    asset_query.first.return_value = fake_asset

    db_mock = mocker.Mock()
    db_mock.query.side_effect = [schedules_query, approved_query, asset_query]

    mocker.patch("app.scheduler.SessionLocal", return_value=db_mock)
    create_mock = mocker.patch("app.scheduler.create_media_container", return_value="container123")
    wait_mock = mocker.patch("app.scheduler.wait_until_container_ready")
    publish_mock = mocker.patch("app.scheduler.publish_container", return_value="published123")

    from app.scheduler import process_due_posts
    process_due_posts()

    create_mock.assert_called_once()
    wait_mock.assert_called_once_with("container123")
    publish_mock.assert_called_once_with("container123")
    assert fake_schedule.status == "published"
    assert fake_schedule.published_instagram_id == "published123"

def test_scheduler_marks_failed_on_publish_error(mocker):
    fake_schedule = FakeSchedule()
    fake_approved = FakeApprovedPost()
    fake_asset = FakeAsset()

    schedules_query = mocker.Mock()
    schedules_query.filter.return_value = schedules_query
    schedules_query.all.return_value = [fake_schedule]

    approved_query = mocker.Mock()
    approved_query.filter.return_value = approved_query
    approved_query.first.return_value = fake_approved

    asset_query = mocker.Mock()
    asset_query.filter.return_value = asset_query
    asset_query.first.return_value = fake_asset

    db_mock = mocker.Mock()
    db_mock.query.side_effect = [schedules_query, approved_query, asset_query]

    mocker.patch("app.scheduler.SessionLocal", return_value=db_mock)
    mocker.patch("app.scheduler.create_media_container", return_value="container123")
    mocker.patch("app.scheduler.wait_until_container_ready")
    mocker.patch("app.scheduler.publish_container", side_effect=RuntimeError("publish failed"))

    from app.scheduler import process_due_posts
    process_due_posts()

    assert fake_schedule.status == "failed"
    assert "publish failed" in fake_schedule.error_message
