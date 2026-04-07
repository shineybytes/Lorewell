from tests.helpers import create_event, create_post, upload_asset, write_temp_file


def test_get_post_returns_draft_fields(client):
    event_id = create_event(client)
    media_path = write_temp_file("tests_temp_image.jpg", b"fake image bytes")

    try:
        asset = upload_asset(client, event_id, media_path, "image/jpeg")
        post_id = create_post(
            client,
            event_id=event_id,
            asset_id=asset["asset_id"],
            brand_voice="warm",
            cta_goal="encourage bookings",
            generation_notes="Keep it classy.",
        )

        response = client.get(f"/posts/{post_id}")

        assert response.status_code == 200
        body = response.json()
        assert body["id"] == post_id
        assert body["event_id"] == event_id
        assert body["asset_id"] == asset["asset_id"]
        assert body["brand_voice"] == "warm"
        assert body["cta_goal"] == "encourage bookings"
        assert body["generation_notes"] == "Keep it classy."
        assert body["status"] == "draft"
    finally:
        if media_path.exists():
            media_path.unlink()


def test_get_post_returns_404_for_missing_post(client):
    response = client.get("/posts/999999")
    assert response.status_code == 404
    assert response.json()["detail"] == "Post not found"


def test_patch_post_updates_fields(client):
    event_id = create_event(client)
    media_path = write_temp_file("tests_temp_image.jpg", b"fake image bytes")

    try:
        asset = upload_asset(client, event_id, media_path, "image/jpeg")
        post_id = create_post(
            client,
            event_id=event_id,
            asset_id=asset["asset_id"],
            brand_voice="energetic",
            cta_goal="encourage follows",
            generation_notes="Initial notes",
        )

        response = client.patch(
            f"/posts/{post_id}",
            json={
                "brand_voice": "elegant",
                "cta_goal": "encourage inquiries",
                "generation_notes": "Updated notes",
            },
        )

        assert response.status_code == 200
        assert response.json()["post_id"] == post_id

        get_resp = client.get(f"/posts/{post_id}")
        body = get_resp.json()
        assert body["brand_voice"] == "elegant"
        assert body["cta_goal"] == "encourage inquiries"
        assert body["generation_notes"] == "Updated notes"
    finally:
        if media_path.exists():
            media_path.unlink()


def test_patch_post_returns_404_for_missing_post(client):
    response = client.patch(
        "/posts/999999",
        json={
            "brand_voice": "elegant",
            "cta_goal": "encourage inquiries",
            "generation_notes": "Updated notes",
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Post not found"
