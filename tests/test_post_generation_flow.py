def test_generate_post_accepts_seed_caption(client, mocker, create_event, create_asset, create_post):
    event_id = create_event()
    asset_id = create_asset(event_id)
    post_id = create_post(event_id=event_id, asset_id=asset_id)

    mocker.patch(
        "app.services.posts.generate_caption_package",
        return_value={
            "caption_option_1": "Seeded option 1",
            "caption_option_2": "Seeded option 2",
            "caption_option_3": "Seeded option 3",
            "hashtags": ["#tag1", "#tag2"],
            "accessibility_text": "Generated alt",
            "seo_keywords": ["kw1"],
            "visual_summary": "summary",
        },
    )

    response = client.post(
        f"/posts/{post_id}/generate",
        json={"seed_caption": "Use this as the basis"},
    )
    assert response.status_code == 200
    body = response.json()

    assert body["caption_option_1"] == "Seeded option 1"
    assert body["caption_option_2"] == "Seeded option 2"
    assert body["caption_option_3"] == "Seeded option 3"

def test_get_post_includes_latest_approved_snapshot(
    client, create_event, create_asset, create_post, approve_post
):
    event_id = create_event()
    asset_id = create_asset(event_id)
    post_id = create_post(event_id=event_id, asset_id=asset_id)

    approve_post(
        post_id=post_id,
        caption_final="Final chosen caption",
        hashtags_final=["#one", "#two"],
        accessibility_text="Final alt text",
    )

    response = client.get(f"/posts/{post_id}")
    assert response.status_code == 200
    body = response.json()

    assert body["approved_caption_final"] == "Final chosen caption"
    assert body["approved_hashtags_final"] == "#one #two"
    assert body["approved_accessibility_text"] == "Final alt text"
