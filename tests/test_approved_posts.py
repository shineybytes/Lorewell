from tests.helpers import approve_post, create_event, create_post, upload_asset, write_temp_file


def test_list_approved_posts_returns_approved_content(client):
    event_id = create_event(client)
    media_path = write_temp_file("tests_temp_image.jpg", b"fake image bytes")

    try:
        asset = upload_asset(client, event_id, media_path, "image/jpeg")
        post_id = create_post(client, event_id=event_id, asset_id=asset["asset_id"])

        approved_post_id = approve_post(
            client,
            post_id=post_id,
            caption_final="Approved caption",
            hashtags_final=["dj", "nightlife"],
            accessibility_text="Approved alt text",
        )

        response = client.get("/approved-posts")

        assert response.status_code == 200
        body = response.json()
        approved = next(a for a in body if a["id"] == approved_post_id)

        assert approved["post_id"] == post_id
        assert approved["selected_asset_id"] == asset["asset_id"]
        assert approved["caption_final"] == "Approved caption"
        assert approved["hashtags_final"] == ["dj", "nightlife"]
        assert approved["accessibility_text"] == "Approved alt text"
        assert approved["status"] == "approved"
    finally:
        if media_path.exists():
            media_path.unlink()


def test_approved_post_disappears_from_draft_status_flow(client):
    event_id = create_event(client)
    media_path = write_temp_file("tests_temp_image.jpg", b"fake image bytes")

    try:
        asset = upload_asset(client, event_id, media_path, "image/jpeg")
        post_id = create_post(client, event_id=event_id, asset_id=asset["asset_id"])

        approve_post(
            client,
            post_id=post_id,
            caption_final="Approved caption",
            hashtags_final=["dj"],
            accessibility_text="alt text",
        )

        posts_resp = client.get("/posts")
        posts = posts_resp.json()
        post = next(p for p in posts if p["id"] == post_id)

        assert post["status"] == "approved"
    finally:
        if media_path.exists():
            media_path.unlink()
