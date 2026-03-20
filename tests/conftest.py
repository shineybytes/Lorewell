import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import os
import pytest
from fastapi.testclient import TestClient


@pytest.fixture(autouse=True)
def set_test_env(monkeypatch, tmp_path):
    monkeypatch.setenv("OPENAI_API_KEY", "test-openai-key")
    monkeypatch.setenv("OPENAI_MODEL", "gpt-5.4-mini")
    monkeypatch.setenv("PAGE_ACCESS_TOKEN", "test-page-token")
    monkeypatch.setenv("INSTAGRAM_ACCOUNT_ID", "17841473771500345")
    monkeypatch.setenv("GRAPH_API_VERSION", "v25.0")
    monkeypatch.setenv("APP_BASE_URL", "https://example.test")
    monkeypatch.setenv("MEDIA_DIR", str(tmp_path / "media"))
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path / 'test.db'}")
    monkeypatch.setenv(
        "DEFAULT_BRAND_VOICE",
        "elegant, warm, story-driven, clear call to action",
    )


@pytest.fixture
def client():
    # Import after env vars are set
    from app.main import app
    return TestClient(app)
