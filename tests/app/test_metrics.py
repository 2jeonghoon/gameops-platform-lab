from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import create_app
from app.settings import Settings


@pytest.mark.anyio
async def test_metrics_cover_success_validation_not_found_and_injected_error() -> None:
    app = create_app(Settings(fault_error_rate=0.0))

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        created_response = await client.post(
            "/sessions", json={"region": "ap-northeast-2", "player_count": 8}
        )
        session_id = created_response.json()["id"]
        await client.get(f"/sessions/{session_id}")
        await client.post("/sessions", json={"region": "ap-northeast-2", "player_count": 0})
        unknown_id = uuid4()
        await client.get(f"/sessions/{unknown_id}")
        await client.delete(f"/sessions/{session_id}")

        app.state.fault_controller.settings.fault_error_rate = 1.0
        await client.post("/sessions", json={"region": "ap-northeast-2", "player_count": 8})
        metrics = (await client.get("/metrics")).text

    for metric_name in (
        "gameops_http_requests_total",
        "gameops_http_request_duration_seconds",
        "gameops_active_sessions",
        "gameops_sessions_created_total",
        "gameops_sessions_deleted_total",
    ):
        assert metric_name in metrics

    assert 'status_class="2xx"' in metrics
    assert 'status_class="4xx"' in metrics
    assert 'status_class="5xx"' in metrics
    assert session_id not in metrics
    assert str(unknown_id) not in metrics
    assert 'route="/sessions/{session_id}"' in metrics
    assert "gameops_active_sessions 0.0" in metrics
