import os
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

os.environ["PYTEST_RUNNING"] = "1"

from app.db import Base, get_db
from app.main import app
from app.models import Schedule

@pytest.fixture
def engine_and_session(tmp_path):
    test_db_url = f"sqlite:///{tmp_path / 'test.db'}"
    engine = create_engine(
        test_db_url,
        connect_args={"check_same_thread": False},
    )
    TestingSessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=engine,
    )

    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    return engine, TestingSessionLocal


@pytest.fixture
def client(engine_and_session, mocker):
    engine, TestingSessionLocal = engine_and_session

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    mocker.patch("app.main.start_scheduler", return_value=None)

    with TestClient(app) as c:
        yield c

    app.dependency_overrides.clear()


@pytest.fixture
def db_session(engine_and_session):
    _, TestingSessionLocal = engine_and_session
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def create_event(client):
    def _create():
        response = client.post(
            "/events",
            json={
                "title": "Test Event",
                "event_type": "dj set",
                "location": "San Diego",
                "event_date": "2026-03-19T01:00:00",
                "event_timezone": "America/Los_Angeles",
                "recap": "Test recap",
                "keywords": "dj,test",
                "vendors": "Venue X",
                "event_guidance": None,
            },
        )
        assert response.status_code == 200
        return response.json()["id"]

    return _create


@pytest.fixture
def create_asset(client, tmp_path):
    def _create(event_id: int):
        file_path = tmp_path / "test.jpg"
        file_path.write_bytes(b"fake-image-data")

        with file_path.open("rb") as f:
            response = client.post(
                f"/events/{event_id}/assets",
                files={"file": ("test.jpg", f, "image/jpeg")},
            )

        assert response.status_code == 200
        return response.json()["asset_id"]

    return _create


@pytest.fixture
def create_post(client):
    def _create(event_id: int, asset_id: int):
        response = client.post(
            "/posts",
            json={
                "event_id": event_id,
                "asset_id": asset_id,
                "brand_voice": "test",
                "cta_goal": "test",
                "generation_notes": "test",
            },
        )
        assert response.status_code == 200
        return response.json()["post_id"]

    return _create


@pytest.fixture
def approve_post(client):
    def _approve(
        post_id: int,
        caption_final="approved caption",
        hashtags_final=None,
        accessibility_text="alt text",
    ):
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

    return _approve


@pytest.fixture
def approved_post_factory(create_event, create_asset, create_post, approve_post):
    def _create():
        event_id = create_event()
        asset_id = create_asset(event_id)
        post_id = create_post(event_id, asset_id)
        return approve_post(
            post_id=post_id,
            caption_final="Approved caption",
            hashtags_final=["#test"],
            accessibility_text="Alt text",
        )

    return _create


@pytest.fixture
def schedule_factory(client):
    def _create(approved_post_id: int):
        response = client.post(
            f"/approved-posts/{approved_post_id}/schedule",
            json={
                "publish_at": "2026-01-01T00:00:00",
                "publish_timezone": "UTC",
            },
        )
        assert response.status_code == 200
        return response.json()

    return _create


@pytest.fixture
def failed_schedule_factory(db_session, schedule_factory):
    def _create(approved_post_id: int, acknowledged=False):
        schedule_data = schedule_factory(approved_post_id)
        schedule_id = schedule_data["schedule_id"]

        schedule = db_session.query(Schedule).filter(Schedule.id == schedule_id).first()
        assert schedule is not None

        schedule.status = "failed"
        schedule.error_message = "Simulated failure"
        schedule.failure_acknowledged = acknowledged
        db_session.add(schedule)
        db_session.commit()
        db_session.refresh(schedule)

        return schedule

    return _create
