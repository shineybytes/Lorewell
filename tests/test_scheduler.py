from datetime import UTC, datetime, timedelta

from app.scheduler import process_due_posts


class FakeAsset:
    def __init__(self):
        self.id = 1
        self.file_path = "media/test.jpg"
        self.media_type = "image"


class FakeSchedule:
    def __init__(self):
        self.id = 1
        self.status = "scheduled"
        self.publish_at = datetime.now(UTC).replace(tzinfo=None)
        self.approved_post_id = 1
        self.published_instagram_id = None
        self.error_message = None

        self.publish_attempts = 0
        self.last_attempt_error = None
        self.publishing_started_at = None
        self.failure_acknowledged = False


class FakeApprovedPost:
    def __init__(self):
        self.id = 1
        self.selected_asset_id = 1
        self.caption_final = "caption"
        self.hashtags_final = "#one #two"


def make_query_mock(mocker, *, all_result=None, first_result=None):
    query = mocker.Mock()
    query.filter.return_value = query

    if all_result is not None:
        query.all.return_value = all_result

    if first_result is not None:
        query.first.return_value = first_result

    return query


def make_db_mock(
    mocker,
    *,
    stale_publishing=None,
    scheduled=None,
    approved_post=None,
    asset=None,
):
    queries = [
        make_query_mock(mocker, all_result=stale_publishing if stale_publishing is not None else []),
        make_query_mock(mocker, all_result=scheduled if scheduled is not None else []),
    ]

    if approved_post is not None:
        queries.append(make_query_mock(mocker, first_result=approved_post))

    if asset is not None:
        queries.append(make_query_mock(mocker, first_result=asset))

    db_mock = mocker.Mock()
    db_mock.query.side_effect = queries
    return db_mock


def test_scheduler_processes_approved_posts_in_window(mocker):
    fake_schedule = FakeSchedule()
    fake_approved = FakeApprovedPost()
    fake_asset = FakeAsset()

    db_mock = make_db_mock(
        mocker,
        stale_publishing=[],
        scheduled=[fake_schedule],
        approved_post=fake_approved,
        asset=fake_asset,
    )

    mocker.patch("app.scheduler.SessionLocal", return_value=db_mock)
    create_mock = mocker.patch("app.scheduler.create_media_container", return_value="container123")
    wait_mock = mocker.patch("app.scheduler.wait_until_container_ready")
    publish_mock = mocker.patch("app.scheduler.publish_container", return_value="published123")

    process_due_posts()

    create_mock.assert_called_once()
    wait_mock.assert_called_once_with("container123")
    publish_mock.assert_called_once_with("container123")

    assert fake_schedule.status == "published"
    assert fake_schedule.published_instagram_id == "published123"
    assert fake_schedule.error_message is None
    assert fake_schedule.last_attempt_error is None
    assert fake_schedule.publishing_started_at is None
    assert fake_schedule.publish_attempts == 1


def test_scheduler_marks_failed_on_publish_error(mocker):
    fake_schedule = FakeSchedule()
    fake_approved = FakeApprovedPost()
    fake_asset = FakeAsset()

    db_mock = make_db_mock(
        mocker,
        stale_publishing=[],
        scheduled=[fake_schedule],
        approved_post=fake_approved,
        asset=fake_asset,
    )

    mocker.patch("app.scheduler.SessionLocal", return_value=db_mock)
    mocker.patch("app.scheduler.create_media_container", return_value="container123")
    mocker.patch("app.scheduler.wait_until_container_ready")
    mocker.patch("app.scheduler.publish_container", side_effect=RuntimeError("publish failed"))

    process_due_posts()

    assert fake_schedule.status == "failed"
    assert "publish failed" in fake_schedule.error_message
    assert "publish failed" in fake_schedule.last_attempt_error
    assert fake_schedule.publishing_started_at is None
    assert fake_schedule.publish_attempts == 1


def test_scheduler_marks_stale_publishing_as_failed(mocker):
    fake_schedule = FakeSchedule()
    fake_schedule.status = "publishing"
    fake_schedule.publishing_started_at = (
        datetime.now(UTC).replace(tzinfo=None) - timedelta(minutes=20)
    )

    db_mock = make_db_mock(
        mocker,
        stale_publishing=[fake_schedule],
        scheduled=[],
    )

    mocker.patch("app.scheduler.SessionLocal", return_value=db_mock)

    process_due_posts()

    assert fake_schedule.status == "failed"
    assert fake_schedule.publishing_started_at is None
    assert fake_schedule.error_message == "Publishing attempt became stale and was marked failed"
    assert fake_schedule.last_attempt_error == "Publishing attempt became stale and was marked failed"


def test_scheduler_does_not_reclaim_fresh_publishing(mocker):
    fake_schedule = FakeSchedule()
    fake_schedule.status = "publishing"
    fake_schedule.publishing_started_at = datetime.now(UTC).replace(tzinfo=None)

    db_mock = make_db_mock(
        mocker,
        stale_publishing=[],
        scheduled=[],
    )

    mocker.patch("app.scheduler.SessionLocal", return_value=db_mock)

    process_due_posts()

    assert fake_schedule.status == "publishing"
    assert fake_schedule.publishing_started_at is not None
    assert fake_schedule.error_message is None
    assert fake_schedule.last_attempt_error is None
    assert fake_schedule.publish_attempts == 0

def test_scheduler_builds_full_caption_from_caption_and_hashtags(mocker):
    fake_schedule = FakeSchedule()
    fake_approved = FakeApprovedPost()
    fake_asset = FakeAsset()

    db_mock = make_db_mock(
        mocker,
        stale_publishing=[],
        scheduled=[fake_schedule],
        approved_post=fake_approved,
        asset=fake_asset,
    )

    mocker.patch("app.scheduler.SessionLocal", return_value=db_mock)
    create_mock = mocker.patch("app.scheduler.create_media_container", return_value="container123")
    mocker.patch("app.scheduler.wait_until_container_ready")
    mocker.patch("app.scheduler.publish_container", return_value="published123")

    process_due_posts()

    _, kwargs = create_mock.call_args
    assert kwargs["file_path"] == "media/test.jpg"
    assert kwargs["media_type"] == "image"
    assert kwargs["caption"] == "caption\n\n#one #two"

def test_failed_schedule_keeps_failure_acknowledged_default_false(mocker):
    fake_schedule = FakeSchedule()
    fake_schedule.failure_acknowledged = False
    fake_approved = FakeApprovedPost()
    fake_asset = FakeAsset()

    db_mock = make_db_mock(
        mocker,
        stale_publishing=[],
        scheduled=[fake_schedule],
        approved_post=fake_approved,
        asset=fake_asset,
    )

    mocker.patch("app.scheduler.SessionLocal", return_value=db_mock)
    mocker.patch("app.scheduler.create_media_container", return_value="container123")
    mocker.patch("app.scheduler.wait_until_container_ready")
    mocker.patch("app.scheduler.publish_container", side_effect=RuntimeError("publish failed"))

    process_due_posts()

    assert fake_schedule.status == "failed"
    assert fake_schedule.failure_acknowledged is False
