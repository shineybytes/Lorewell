from tests.helpers import create_event, upload_asset, write_temp_file


def test_upload_asset_without_event(client, mocker):
    media_path = write_temp_file("tests_temp_no_event.jpg", b"fake jpeg bytes")

    try:
        with media_path.open("rb") as f:
            response = client.post(
                "/assets/upload",
                files={"file": ("tests_temp_no_event.jpg", f, "image/jpeg")},
            )

        assert response.status_code == 200
        body = response.json()
        assert body["media_type"] == "image"
        assert body["analysis_status"] == "pending"
        assert body["vision_summary_generated"] is None
        assert body["accessibility_text_generated"] is None

        asset_id = body["asset_id"]
        get_resp = client.get(f"/assets/{asset_id}")
        assert get_resp.status_code == 200
        asset = get_resp.json()
        assert asset["event_id"] is None
        assert asset["display_name"] == "tests_temp_no_event.jpg"
    finally:
        if media_path.exists():
            media_path.unlink()


def test_list_assets_includes_uploaded_asset(client):
    media_path = write_temp_file("tests_temp_list_assets.jpg", b"fake jpeg bytes")

    try:
        with media_path.open("rb") as f:
            upload_resp = client.post(
                "/assets/upload",
                files={"file": ("tests_temp_list_assets.jpg", f, "image/jpeg")},
            )
        assert upload_resp.status_code == 200
        asset_id = upload_resp.json()["asset_id"]

        response = client.get("/assets")
        assert response.status_code == 200
        body = response.json()

        found = next(a for a in body if a["id"] == asset_id)
        assert found["display_name"] == "tests_temp_list_assets.jpg"
        assert found["event_id"] is None
    finally:
        if media_path.exists():
            media_path.unlink()


def test_get_asset_returns_single_asset(client):
    event_id = create_event(client)
    media_path = write_temp_file("tests_temp_get_asset.jpg", b"fake jpeg bytes")

    try:
        asset = upload_asset(client, event_id, media_path, "image/jpeg")
        asset_id = asset["asset_id"]

        response = client.get(f"/assets/{asset_id}")
        assert response.status_code == 200
        body = response.json()
        assert body["id"] == asset_id
        assert body["event_id"] == event_id
        assert body["media_type"] == "image"
    finally:
        if media_path.exists():
            media_path.unlink()


def test_rename_asset_updates_display_name(client):
    event_id = create_event(client)
    media_path = write_temp_file("tests_temp_rename_asset.jpg", b"fake jpeg bytes")

    try:
        asset = upload_asset(client, event_id, media_path, "image/jpeg")
        asset_id = asset["asset_id"]

        response = client.patch(
            f"/assets/{asset_id}",
            json={"display_name": "Hero Image"},
        )
        assert response.status_code == 200
        assert response.json()["display_name"] == "Hero Image"

        get_resp = client.get(f"/assets/{asset_id}")
        assert get_resp.status_code == 200
        assert get_resp.json()["display_name"] == "Hero Image"
    finally:
        if media_path.exists():
            media_path.unlink()


def test_update_asset_event_reassigns_and_unassigns(client):
    event_a = create_event(client, title="Event A")
    event_b = create_event(client, title="Event B")
    media_path = write_temp_file("tests_temp_reassign.jpg", b"fake jpeg bytes")

    try:
        asset = upload_asset(client, event_a, media_path, "image/jpeg")
        asset_id = asset["asset_id"]

        move_resp = client.patch(
            f"/assets/{asset_id}/event",
            json={"event_id": event_b},
        )
        assert move_resp.status_code == 200
        assert move_resp.json()["event_id"] == event_b

        clear_resp = client.patch(
            f"/assets/{asset_id}/event",
            json={"event_id": None},
        )
        assert clear_resp.status_code == 200
        assert clear_resp.json()["event_id"] is None
    finally:
        if media_path.exists():
            media_path.unlink()


def test_update_asset_event_rejects_missing_event(client):
    event_id = create_event(client)
    media_path = write_temp_file("tests_temp_bad_reassign.jpg", b"fake jpeg bytes")

    try:
        asset = upload_asset(client, event_id, media_path, "image/jpeg")
        asset_id = asset["asset_id"]

        response = client.patch(
            f"/assets/{asset_id}/event",
            json={"event_id": 999999},
        )
        assert response.status_code == 404
        assert response.json()["detail"] == "Event not found"
    finally:
        if media_path.exists():
            media_path.unlink()


def test_propose_asset_analysis_uses_event_context(client, mocker):
    analyze_mock = mocker.patch(
        "app.services.assets.analyze_media",
        return_value={
            "visual_summary": "Context-aware summary",
            "accessibility_text": "Context-aware accessibility",
        },
    )

    event_id = create_event(
        client,
        title="Proposal Event",
        recap="This was a wedding reception with uplighting.",
        event_guidance="Focus on dance floor energy.",
    )
    media_path = write_temp_file("tests_temp_proposal.jpg", b"fake jpeg bytes")

    try:
        asset = upload_asset(client, event_id, media_path, "image/jpeg")
        asset_id = asset["asset_id"]

        response = client.post(
            f"/assets/{asset_id}/propose-analysis",
            json={"user_correction": "The image shows guests dancing."},
        )
        assert response.status_code == 200
        body = response.json()

        assert body["asset_id"] == asset_id
        assert body["proposed_visual_summary"] == "Context-aware summary"
        assert body["proposed_accessibility_text"] == "Context-aware accessibility"

        last_call = analyze_mock.call_args_list[-1]
        correction_text = last_call.kwargs["user_correction"]
        assert "The image shows guests dancing." in correction_text
        assert "Proposal Event" in correction_text
        assert "This was a wedding reception with uplighting." in correction_text
        assert "Focus on dance floor energy." in correction_text
    finally:
        if media_path.exists():
            media_path.unlink()


def test_apply_asset_analysis_updates_generated_fields(client):
    event_id = create_event(client)
    media_path = write_temp_file("tests_temp_apply_analysis.jpg", b"fake jpeg bytes")

    try:
        asset = upload_asset(client, event_id, media_path, "image/jpeg")
        asset_id = asset["asset_id"]

        response = client.patch(
            f"/assets/{asset_id}/apply-analysis",
            json={
                "vision_summary_generated": "Applied summary",
                "accessibility_text_generated": "Applied accessibility text",
            },
        )
        assert response.status_code == 200
        body = response.json()

        assert body["vision_summary_generated"] == "Applied summary"
        assert body["accessibility_text_generated"] == "Applied accessibility text"
        assert body["analysis_status"] == "analyzed"
    finally:
        if media_path.exists():
            media_path.unlink()
