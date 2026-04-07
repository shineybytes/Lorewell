# tests/conftest.py
import os
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

os.environ["PYTEST_RUNNING"] = "1"

from app.db import Base
from app.main import app, get_db

@pytest.fixture
def client(tmp_path, mocker):
    test_db_url = f"sqlite:///{tmp_path / 'test.db'}"
    engine = create_engine(
        test_db_url,
        connect_args={"check_same_thread": False},
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

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
