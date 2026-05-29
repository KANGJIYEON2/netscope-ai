"""GET /projects/overview smoke test."""
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient


def _make_client():
    from src.main import app
    from src.db.session import get_db
    from src.api.v1.dep import get_current_context

    mock_db = MagicMock()
    # count queries return 0
    mock_db.query.return_value.filter.return_value.scalar.return_value = 0
    # chained filter for AnalysisResult query
    mock_db.query.return_value.filter.return_value.order_by.return_value.first.return_value = None

    app.dependency_overrides[get_db] = lambda: mock_db
    app.dependency_overrides[get_current_context] = lambda: {
        "user_id": "test-user",
        "tenant_id": "test-tenant",
    }

    client = TestClient(app)
    return client, app


def test_overview_returns_200():
    client, app = _make_client()
    try:
        resp = client.get("/projects/overview")
        assert resp.status_code == 200
        body = resp.json()
        assert "log_count_24h" in body
        assert "error_rate" in body
        assert "last_analysis" in body
    finally:
        app.dependency_overrides.clear()
