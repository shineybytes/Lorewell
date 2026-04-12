from tests.helpers import approve_post, create_event, create_post, upload_asset, write_temp_file


def test_create_post_without_event_succeeds(client):
    event_id = create_event(client)
    media_path = write_temp_file("tests_temp_asset_only_post.jpg", b"fake jpeg bytes")

    try:
        asset = upload_asset(client, event_id, media_path, "image/jpeg")
        asset_id = asset["asset_id"]

        clear_resp = client.patch(
            f"/assets/{asset_id}/event",
            json={"event_id": None},
        )
        assert clear_resp.status_code == 200

        post_resp = client.post(
            "/posts",
            json={
                "event_id": None,
                "asset_id": asset_id,
                "brand_voice": "warm",
                "cta_goal": "book now",
                "generation_notes": "asset-only draft",
            },
        )
        assert post_resp.status_code == 200

        post_id = post_resp.json()["post_id"]
        get_resp = client.get(f"/posts/{post_id}")
        assert get_resp.status_code == 200
        assert get_resp.json()["event_id"] is None
        assert get_resp.json()["asset_id"] == asset_id
    finally:
        if media_path.exists():
            media_path.unlink()


def test_save_draft_content_updates_post(client):
    event_id = create_event(client)
    media_path = write_temp_file("tests_temp_save_draft.jpg", b"fake jpeg bytes")

    try:
        asset = upload_asset(client, event_id, media_path, "image/jpeg")
        post_id = create_post(client, event_id=event_id, asset_id=asset["asset_id"])

        response = client.patch(
            f"/posts/{post_id}/draft-content",
            json={
                "draft_caption_current": "Draft caption current",
                "draft_hashtags_current": "#one #two",
                "draft_accessibility_current": "Draft accessibility current",
            },
        )
        assert response.status_code == 200
        body = response.json()

        assert body["draft_caption_current"] == "Draft caption current"
        assert body["draft_hashtags_current"] == "#one #two"
        assert body["draft_accessibility_current"] == "Draft accessibility current"

        get_resp = client.get(f"/posts/{post_id}")
        assert get_resp.status_code == 200
        post = get_resp.json()
        assert post["draft_caption_current"] == "Draft caption current"
        assert post["draft_hashtags_current"] == "#one #two"
        assert post["draft_accessibility_current"] == "Draft accessibility current"
    finally:
        if media_path.exists():
            media_path.unlink()


def test_fork_approved_post_creates_revision_draft(client):
    event_id = create_event(client, title="Revision Event")
    media_path = write_temp_file("tests_temp_fork.jpg", b"fake jpeg bytes")

    try:
        asset = upload_asset(client, event_id, media_path, "image/jpeg")
        post_id = create_post(
            client,
            event_id=event_id,
            asset_id=asset["asset_id"],
            brand_voice="elegant",
            cta_goal="drive inquiries",
            generation_notes="original notes",
        )

        approved_post_id = approve_post(
            client,
            post_id=post_id,
            caption_final="Approved caption",
            hashtags_final=["#one", "#two"],
            accessibility_text="Approved alt text",
        )

        fork_resp = client.post(f"/approved-posts/{approved_post_id}/fork-draft")
        assert fork_resp.status_code == 200
        forked_post_id = fork_resp.json()["post_id"]

        get_resp = client.get(f"/posts/{forked_post_id}")
        assert get_resp.status_code == 200
        body = get_resp.json()

        assert body["status"] == "draft"
        assert body["event_id"] == event_id
        assert body["asset_id"] == asset["asset_id"]
        assert body["brand_voice"] == "elegant"
        assert body["cta_goal"] == "drive inquiries"
        assert body["generation_notes"] == "original notes"
        assert body["draft_caption_current"] == "Approved caption"
        assert body["draft_hashtags_current"] == "#one #two"
        assert body["draft_accessibility_current"] == "Approved alt text"
    finally:
        if media_path.exists():
            media_path.unlink()
