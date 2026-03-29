from pathlib import Path


def create_event(
    client,
    *,
    title="Test Event",
    event_type="dj set",
    location="San Diego",
    event_date="2026-03-19T01:00:00",
    notes="Test notes",
    keywords="dj,test",
    vendors="Venue X",
) -> int:
    response = client.post(
        "/events",
        json={
            "title": title,
            "event_type": event_type,
            "location": location,
            "event_date": event_date,
            "notes": notes,
            "keywords": keywords,
            "vendors": vendors,
        },
    )
    assert response.status_code == 200
    return response.json()["id"]


def write_temp_file(filename: str, content: bytes) -> Path:
    path = Path(filename)
    path.write_bytes(content)
    return path


def upload_asset(client, event_id: int, media_path: Path, content_type: str) -> dict:
    with media_path.open("rb") as f:
        response = client.post(
            f"/events/{event_id}/assets",
            files={"file": (media_path.name, f, content_type)},
        )
    assert response.status_code == 200
    return response.json()


def create_post(
    client,
    *,
    event_id: int,
    asset_id: int,
    brand_voice="energetic",
    cta_goal="encourage follows",
    generation_notes=None,
) -> int:
    payload = {
        "event_id": event_id,
        "asset_id": asset_id,
        "brand_voice": brand_voice,
        "cta_goal": cta_goal,
    }
    if generation_notes is not None:
        payload["generation_notes"] = generation_notes

    response = client.post("/posts", json=payload)
    assert response.status_code == 200
    return response.json()["post_id"]


def approve_post(
    client,
    *,
    post_id: int,
    caption_final="approved caption",
    hashtags_final=None,
    accessibility_text="alt text",
) -> int:
    if hashtags_final is None:
        hashtags_final = ["dj", "test"]

    response = client.post(
        f"/posts/{post_id}/approve",
        json={
            "caption_final": caption_final,
            "hashtags_final": hashtags_final,
            "accessibility_text": accessibility_text,
        },
    )
    assert response.status_code == 200
    return response.json()["approved_post_id"]
