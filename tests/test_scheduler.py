from datetime import datetime


class FakePost:
    def __init__(self):
        self.status = "approved"
        self.publish_at = datetime.utcnow()
        self.asset_id = 1
        self.caption_final = "caption"
        self.hashtags_final = "#one #two"
        self.published_instagram_id = None
        self.error_message = None


class FakeAsset:
    def __init__(self):
        self.id = 1
        self.file_path = "media/test.jpg"
        self.media_type = "image"


def test_scheduler_processes_approved_posts_in_window(mocker):
    fake_post = FakePost()
    fake_asset = FakeAsset()

    posts_query = mocker.Mock()
    posts_query.filter.return_value = posts_query
    posts_query.all.return_value = [fake_post]

    asset_query = mocker.Mock()
    asset_query.filter.return_value = asset_query
    asset_query.first.return_value = fake_asset

    db_mock = mocker.Mock()
    db_mock.query.side_effect = [posts_query, asset_query]

    mocker.patch("app.scheduler.SessionLocal", return_value=db_mock)
    mocker.patch("app.scheduler.create_media_container", return_value="container123")
    mocker.patch("app.scheduler.publish_container", return_value="published123")

    from app.scheduler import process_due_posts
    process_due_posts()

    assert fake_post.status == "published"
    assert fake_post.published_instagram_id == "published123"
    assert fake_post.error_message is None


def test_scheduler_marks_failed_on_publish_error(mocker):
    fake_post = FakePost()
    fake_asset = FakeAsset()

    posts_query = mocker.Mock()
    posts_query.filter.return_value = posts_query
    posts_query.all.return_value = [fake_post]

    asset_query = mocker.Mock()
    asset_query.filter.return_value = asset_query
    asset_query.first.return_value = fake_asset

    db_mock = mocker.Mock()
    db_mock.query.side_effect = [posts_query, asset_query]

    mocker.patch("app.scheduler.SessionLocal", return_value=db_mock)
    mocker.patch("app.scheduler.create_media_container", return_value="container123")
    mocker.patch("app.scheduler.publish_container", side_effect=RuntimeError("publish failed"))

    from app.scheduler import process_due_posts
    process_due_posts()

    assert fake_post.status == "failed"
    assert "publish failed" in fake_post.error_message
