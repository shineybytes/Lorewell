import os
import sys
from pathlib import Path

# Make sure app/ imports work during pytest collection.
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# Tell config to load .env.test before app modules import settings.
os.environ["PYTEST_RUNNING"] = "1"

import pytest
from fastapi.testclient import TestClient


@pytest.fixture(autouse=True)
def set_test_paths(monkeypatch, tmp_path):
    # Keep tests isolated from each other.
    monkeypatch.setenv("MEDIA_DIR", str(tmp_path / "media"))
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path / 'test.db'}")


@pytest.fixture
def client():
    from app.main import app
    return TestClient(app)
