from app.instagram import public_media_url, create_media_container, publish_container


def test_public_media_url_uses_filename(mocker):
    mock_settings = mocker.patch("app.instagram.settings")
    mock_settings.app_base_url = "https://example.test"

    result = public_media_url("/tmp/uploads/dj_photo.jpg")

    assert result == "https://example.test/media/dj_photo.jpg"


def test_create_media_container_for_image(mocker):
    mock_settings = mocker.patch("app.instagram.settings")
    mock_settings.graph_api_version = "v25.0"
    mock_settings.instagram_account_id = "17841473771500345"
    mock_settings.page_access_token = "page-token"
    mock_settings.app_base_url = "https://example.test"

    mock_response = mocker.Mock()
    mock_response.ok = True
    mock_response.json.return_value = {"id": "container123"}
    post_mock = mocker.patch("app.instagram.requests.post", return_value=mock_response)

    result = create_media_container("media/test.jpg", "caption here", "image")

    assert result == "container123"
    _, kwargs = post_mock.call_args
    assert kwargs["data"]["image_url"] == "https://example.test/media/test.jpg"
    assert kwargs["data"]["caption"] == "caption here"
    assert kwargs["data"]["access_token"] == "page-token"


def test_create_media_container_for_video(mocker):
    mock_settings = mocker.patch("app.instagram.settings")
    mock_settings.graph_api_version = "v25.0"
    mock_settings.instagram_account_id = "17841473771500345"
    mock_settings.page_access_token = "page-token"
    mock_settings.app_base_url = "https://example.test"

    mock_response = mocker.Mock()
    mock_response.ok = True
    mock_response.json.return_value = {"id": "container456"}
    post_mock = mocker.patch("app.instagram.requests.post", return_value=mock_response)

    result = create_media_container("media/test.mp4", "caption here", "video")

    assert result == "container456"
    _, kwargs = post_mock.call_args
    assert kwargs["data"]["video_url"] == "https://example.test/media/test.mp4"
    assert kwargs["data"]["media_type"] == "REELS"


def test_publish_container_retries_when_media_not_ready(mocker):
    mock_settings = mocker.patch("app.instagram.settings")
    mock_settings.graph_api_version = "v25.0"
    mock_settings.instagram_account_id = "17841473771500345"
    mock_settings.page_access_token = "page-token"

    not_ready = mocker.Mock()
    not_ready.ok = False
    not_ready.status_code = 400
    not_ready.text = (
        '{"error":{"message":"Media ID is not available",'
        '"error_user_msg":"The media is not ready for publishing, please wait for a moment"}}'
    )

    success = mocker.Mock()
    success.ok = True
    success.json.return_value = {"id": "published123"}

    post_mock = mocker.patch(
        "app.instagram.requests.post",
        side_effect=[not_ready, not_ready, success],
    )
    mocker.patch("app.instagram.time.sleep")

    result = publish_container("container123")

    assert result == "published123"
    assert post_mock.call_count == 3


def test_publish_container_fails_fast_on_non_retryable_error(mocker):
    mock_settings = mocker.patch("app.instagram.settings")
    mock_settings.graph_api_version = "v25.0"
    mock_settings.instagram_account_id = "17841473771500345"
    mock_settings.page_access_token = "page-token"

    bad = mocker.Mock()
    bad.ok = False
    bad.status_code = 400
    bad.text = '{"error":{"message":"Some other error"}}'

    mocker.patch("app.instagram.requests.post", return_value=bad)

    try:
        publish_container("container123")
        assert False, "Expected RuntimeError"
    except RuntimeError as e:
        assert "Some other error" in str(e)
