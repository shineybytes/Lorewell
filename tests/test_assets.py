from tests.helpers import create_event, upload_asset, write_temp_file


def test_upload_asset_auto_analyzes(client, mocker):
    mocker.patch(
        "app.main.analyze_media",
        return_value={
            "visual_summary": "DJ behind booth",
            "accessibility_text": "A DJ standing behind a booth in a dim venue.",
        },
    )

    event_id = create_event(
        client,
        title="Asset Test Event",
        event_date="2026-03-25T18:00:00",
        notes="asset test",
    )
    media_path = write_temp_file("tests_temp_image.jpg", b"fake image bytes")

    try:
        body = upload_asset(client, event_id, media_path, "image/jpeg")
        assert body["analysis_status"] == "analyzed"
        assert body["vision_summary_generated"] == "DJ behind booth"
        assert body["accessibility_text_generated"] == "A DJ standing behind a booth in a dim venue."
    finally:
        if media_path.exists():
            media_path.unlink()


def test_approve_asset_stores_final_accessibility(client, mocker):
    mocker.patch(
        "app.main.analyze_media",
        return_value={
            "visual_summary": "DJ behind booth",
            "accessibility_text": "Generated alt text",
        },
    )

    event_id = create_event(
        client,
        title="Asset Approve Event",
        event_date="2026-03-25T18:00:00",
        notes="asset test",
    )
    media_path = write_temp_file("tests_temp_image.jpg", b"fake image bytes")

    try:
        upload_resp = upload_asset(client, event_id, media_path, "image/jpeg")
        asset_id = upload_resp["asset_id"]

        approve_resp = client.post(
            f"/assets/{asset_id}/approve",
            json={"accessibility_text_final": "Final approved alt text"},
        )

        assert approve_resp.status_code == 200
        body = approve_resp.json()
        assert body["analysis_status"] == "approved"
        assert body["accessibility_text_final"] == "Final approved alt text"
    finally:
        if media_path.exists():
            media_path.unlink()


def test_reapprove_asset_overwrites_final_accessibility(client, mocker):
    mocker.patch(
        "app.main.analyze_media",
        return_value={
            "visual_summary": "DJ behind booth",
            "accessibility_text": "Generated alt text",
        },
    )

    event_id = create_event(
        client,
        title="Asset Reapprove Event",
        event_date="2026-03-25T18:00:00",
        notes="asset test",
    )
    media_path = write_temp_file("tests_temp_image.jpg", b"fake image bytes")

    try:
        upload_resp = upload_asset(client, event_id, media_path, "image/jpeg")
        asset_id = upload_resp["asset_id"]

        client.post(
            f"/assets/{asset_id}/approve",
            json={"accessibility_text_final": "First final text"},
        )

        resp = client.post(
            f"/assets/{asset_id}/approve",
            json={"accessibility_text_final": "Second final text"},
        )

        assert resp.status_code == 200
        assert resp.json()["accessibility_text_final"] == "Second final text"
    finally:
        if media_path.exists():
            media_path.unlink()

def test_reanalyze_asset_without_correction(client, mocker):
    mocker.patch(
        "app.main.analyze_media",
        side_effect=[
            {
                "visual_summary": "Initial summary",
                "accessibility_text": "Initial accessibility text",
            },
            {
                "visual_summary": "Updated summary",
                "accessibility_text": "Updated accessibility text",
            },
        ],
    )

    event_id = create_event(
        client,
        title="Asset Reanalyze Event",
        event_date="2026-03-25T18:00:00",
        notes="asset reanalyze test",
    )
    media_path = write_temp_file("tests_temp_image.jpg", b"fake image bytes")

    try:
        upload_resp = upload_asset(client, event_id, media_path, "image/jpeg")
        asset_id = upload_resp["asset_id"]

        resp = client.post(
            f"/assets/{asset_id}/analyze",
            json={},
        )

        assert resp.status_code == 200
        body = resp.json()
        assert body["asset_id"] == asset_id
        assert body["analysis_status"] == "analyzed"
        assert body["vision_summary_generated"] == "Updated summary"
        assert body["accessibility_text_generated"] == "Updated accessibility text"
    finally:
        if media_path.exists():
            media_path.unlink()


def test_reanalyze_asset_with_user_correction(client, mocker):
    analyze_mock = mocker.patch(
        "app.main.analyze_media",
        side_effect=[
            {
                "visual_summary": "Wrong summary",
                "accessibility_text": "Wrong accessibility text",
            },
            {
                "visual_summary": "Video of people dancing",
                "accessibility_text": "A video of people dancing in front of a DJ booth.",
            },
        ],
    )

    event_id = create_event(
        client,
        title="Asset Correction Event",
        event_date="2026-03-25T18:00:00",
        notes="asset correction test",
    )
    media_path = write_temp_file("tests_temp_video.mp4", b"fake mp4 bytes")

    try:
        upload_resp = upload_asset(client, event_id, media_path, "video/mp4")
        asset_id = upload_resp["asset_id"]

        correction = "This is not a colorful DJ graphic. It is a video of people dancing."

        resp = client.post(
            f"/assets/{asset_id}/analyze",
            json={"user_correction": correction},
        )

        assert resp.status_code == 200
        body = resp.json()
        assert body["asset_id"] == asset_id
        assert body["analysis_status"] == "analyzed"
        assert body["vision_summary_generated"] == "Video of people dancing"
        assert body["accessibility_text_generated"] == (
            "A video of people dancing in front of a DJ booth."
        )

        last_call = analyze_mock.call_args_list[-1]
        assert last_call.args[0].endswith("tests_temp_video.mp4")
        assert last_call.args[1] == "video"
        assert last_call.kwargs["user_correction"] == correction
    finally:
        if media_path.exists():
            media_path.unlink()
