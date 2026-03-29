from app.instagram import get_container_status, wait_until_container_ready
from tests.instagram_helpers import make_response, patch_instagram_settings


def test_get_container_status_returns_json(mocker):
    patch_instagram_settings(mocker)

    mock_response = make_response(
        mocker,
        ok=True,
        json_data={
            "status": "Finished",
            "status_code": "FINISHED",
        },
    )

    get_mock = mocker.patch("app.instagram.requests.get", return_value=mock_response)

    result = get_container_status("container123")

    assert result["status_code"] == "FINISHED"

    _, kwargs = get_mock.call_args
    assert kwargs["params"]["fields"] == "status,status_code"
    assert kwargs["params"]["access_token"] == "page-token"


def test_wait_until_container_ready_returns_when_finished(mocker):
    status_sequence = [
        {"status": "In Progress", "status_code": "IN_PROGRESS"},
        {"status": "In Progress", "status_code": "IN_PROGRESS"},
        {"status": "Finished", "status_code": "FINISHED"},
    ]

    mocker.patch("app.instagram.get_container_status", side_effect=status_sequence)
    sleep_mock = mocker.patch("app.instagram.time.sleep")

    wait_until_container_ready("container123")

    assert sleep_mock.call_count == 2


def test_wait_until_container_ready_raises_on_error_status(mocker):
    mocker.patch(
        "app.instagram.get_container_status",
        return_value={"status": "Error", "status_code": "ERROR"},
    )

    try:
        wait_until_container_ready("container123")
        assert False, "Expected RuntimeError"
    except RuntimeError as e:
        assert "Meta container failed" in str(e)


def test_wait_until_container_ready_raises_on_expired_status(mocker):
    mocker.patch(
        "app.instagram.get_container_status",
        return_value={"status": "Expired", "status_code": "EXPIRED"},
    )

    try:
        wait_until_container_ready("container123")
        assert False, "Expected RuntimeError"
    except RuntimeError as e:
        assert "Meta container failed" in str(e)


def test_wait_until_container_ready_times_out(mocker):
    mocker.patch("app.instagram.PUBLISH_MAX_WAIT_SECONDS", 30)
    mocker.patch("app.instagram.PUBLISH_RETRY_INTERVAL_SECONDS", 10)

    mocker.patch(
        "app.instagram.get_container_status",
        return_value={"status": "In Progress", "status_code": "IN_PROGRESS"},
    )
    mocker.patch("app.instagram.time.sleep")

    try:
        wait_until_container_ready("container123")
        assert False, "Expected RuntimeError"
    except RuntimeError as e:
        assert "Meta container not ready after waiting" in str(e)
