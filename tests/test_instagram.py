from app.instagram import create_media_container, publish_container, public_media_url
from tests.instagram_helpers import make_response, patch_instagram_settings


def test_public_media_url_uses_filename(mocker):
    patch_instagram_settings(mocker)

    result = public_media_url("/tmp/uploads/dj_photo.jpg")

    assert result == "https://example.test/media/dj_photo.jpg"


def test_create_media_container_for_image(mocker):
    patch_instagram_settings(mocker)

    mock_response = make_response(
        mocker,
        ok=True,
        json_data={"id": "container123"},
    )
    post_mock = mocker.patch("app.instagram.requests.post", return_value=mock_response)

    result = create_media_container("media/test.jpg", "caption here", "image")

    assert result == "container123"
    _, kwargs = post_mock.call_args
    assert kwargs["data"]["image_url"] == "https://example.test/media/test.jpg"
    assert kwargs["data"]["caption"] == "caption here"
    assert kwargs["data"]["access_token"] == "page-token"


def test_create_media_container_for_video(mocker):
    patch_instagram_settings(mocker)

    mock_response = make_response(
        mocker,
        ok=True,
        json_data={"id": "container456"},
    )
    post_mock = mocker.patch("app.instagram.requests.post", return_value=mock_response)

    result = create_media_container("media/test.mp4", "caption here", "video")

    assert result == "container456"
    _, kwargs = post_mock.call_args
    assert kwargs["data"]["video_url"] == "https://example.test/media/test.mp4"
    assert kwargs["data"]["media_type"] == "REELS"


def test_publish_container_retries_when_media_not_ready(mocker):
    patch_instagram_settings(mocker)

    not_ready = make_response(
        mocker,
        ok=False,
        status_code=400,
        text='{"error":{"message":"Media ID is not available","error_user_msg":"The media is not ready for publishing, please wait for a moment"}}',
    )
    success = make_response(
        mocker,
        ok=True,
        json_data={"id": "published123"},
    )

    post_mock = mocker.patch(
        "app.instagram.requests.post",
        side_effect=[not_ready, not_ready, success],
    )
    mocker.patch("app.instagram.time.sleep")

    result = publish_container("container123")

    assert result == "published123"
    assert post_mock.call_count == 3


def test_publish_container_fails_fast_on_non_retryable_error(mocker):
    patch_instagram_settings(mocker)

    bad = make_response(
        mocker,
        ok=False,
        status_code=400,
        text='{"error":{"message":"Some other error"}}',
    )

    mocker.patch("app.instagram.requests.post", return_value=bad)

    try:
        publish_container("container123")
        assert False, "Expected RuntimeError"
    except RuntimeError as e:
        assert "Some other error" in str(e)
