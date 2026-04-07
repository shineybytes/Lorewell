def test_create_event_allows_missing_date_and_timezone(client):
    response = client.post(
        "/events",
        json={
            "title": "No Time Event",
            "event_type": "club set",
            "location": "San Diego",
            "recap": "We do not know the exact date.",
            "keywords": "dj,test",
            "vendors": "Venue X",
            "event_guidance": "Keep it general.",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["title"] == "No Time Event"
    assert body["event_date"] is None
    assert body["event_timezone"] is None


def test_create_event_accepts_date_with_timezone(client):
    response = client.post(
        "/events",
        json={
            "title": "Timed Event",
            "event_type": "club set",
            "location": "San Diego",
            "event_date": "2026-03-29T20:00:00",
            "event_timezone": "America/Los_Angeles",
            "recap": "Packed dance floor.",
            "keywords": "dj,test",
            "vendors": "Venue X",
            "event_guidance": "Emphasize energy.",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["event_date"] == "2026-03-29T20:00:00"
    assert body["event_timezone"] == "America/Los_Angeles"


def test_create_event_rejects_date_without_timezone(client):
    response = client.post(
        "/events",
        json={
            "title": "Missing Timezone Event",
            "event_type": "club set",
            "location": "San Diego",
            "event_date": "2026-03-29T20:00:00",
            "recap": "Packed dance floor.",
            "keywords": "dj,test",
            "vendors": "Venue X",
            "event_guidance": "Emphasize energy.",
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "event_timezone required when event_date is provided"


def test_create_event_rejects_timezone_without_date(client):
    response = client.post(
        "/events",
        json={
            "title": "Missing Date Event",
            "event_type": "club set",
            "location": "San Diego",
            "event_timezone": "America/Los_Angeles",
            "recap": "Packed dance floor.",
            "keywords": "dj,test",
            "vendors": "Venue X",
            "event_guidance": "Emphasize energy.",
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "event_date required when event_timezone is provided"


def test_create_event_rejects_invalid_timezone(client):
    response = client.post(
        "/events",
        json={
            "title": "Bad Timezone Event",
            "event_type": "club set",
            "location": "San Diego",
            "event_date": "2026-03-29T20:00:00",
            "event_timezone": "Mars/Olympus",
            "recap": "Packed dance floor.",
            "keywords": "dj,test",
            "vendors": "Venue X",
            "event_guidance": "Emphasize energy.",
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid timezone"


def test_create_event_rejects_timezone_aware_event_date(client):
    response = client.post(
        "/events",
        json={
            "title": "Aware Datetime Event",
            "event_type": "club set",
            "location": "San Diego",
            "event_date": "2026-03-29T20:00:00Z",
            "event_timezone": "America/Los_Angeles",
            "recap": "Packed dance floor.",
            "keywords": "dj,test",
            "vendors": "Venue X",
            "event_guidance": "Emphasize energy.",
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "event_date must not include timezone or Z suffix"


def test_get_event_returns_event_timezone(client):
    create_resp = client.post(
        "/events",
        json={
            "title": "Returned Timezone Event",
            "event_type": "club set",
            "location": "San Diego",
            "event_date": "2026-03-29T20:00:00",
            "event_timezone": "America/Los_Angeles",
            "recap": "Packed dance floor.",
            "keywords": "dj,test",
            "vendors": "Venue X",
            "event_guidance": "Emphasize energy.",
        },
    )
    assert create_resp.status_code == 200
    event_id = create_resp.json()["id"]

    get_resp = client.get(f"/events/{event_id}")
    assert get_resp.status_code == 200
    body = get_resp.json()
    assert body["event_timezone"] == "America/Los_Angeles"
    assert body["event_date"] == "2026-03-29T20:00:00"
