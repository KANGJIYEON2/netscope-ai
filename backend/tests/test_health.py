"""GET /health smoke test."""
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient


def _make_client():
    from src.main import app
    from src.db.session import get_db

    mock_db = MagicMock()
    mock_db.execute.return_value = None  # SELECT 1 succeeds

    app.dependency_overrides[get_db] = lambda: mock_db
    client = TestClient(app)
    return client, app


def test_health_returns_ok():
    client, app = _make_client()
    try:
        resp = client.get("/health")
        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "ok"
        assert body["db"] == "ok"
    finally:
        app.dependency_overrides.clear()
