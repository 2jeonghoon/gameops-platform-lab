from uuid import UUID, uuid4

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import create_app


@pytest.mark.anyio
async def test_session_create_read_delete_lifecycle() -> None:
    app = create_app()

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        created_response = await client.post(
            "/sessions", json={"region": "ap-northeast-2", "player_count": 24}
        )
        created = created_response.json()
        session_id = UUID(created["id"])

        read_response = await client.get(f"/sessions/{session_id}")
        delete_response = await client.delete(f"/sessions/{session_id}")
        missing_response = await client.get(f"/sessions/{session_id}")

    assert created_response.status_code == 201
    assert created["region"] == "ap-northeast-2"
    assert created["player_count"] == 24
    assert created["created_at"].endswith("Z")
    assert read_response.status_code == 200
    assert read_response.json() == created
    assert delete_response.status_code == 204
    assert delete_response.content == b""
    assert missing_response.status_code == 404


@pytest.mark.anyio
async def test_unknown_session_returns_not_found() -> None:
    app = create_app()

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get(f"/sessions/{uuid4()}")

    assert response.status_code == 404
    assert response.json() == {"detail": "Session not found"}


@pytest.mark.anyio
@pytest.mark.parametrize("invalid_count", [0, 101])
async def test_invalid_player_count_does_not_create_state(invalid_count: int) -> None:
    app = create_app()

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(
            "/sessions", json={"region": "ap-northeast-2", "player_count": invalid_count}
        )

    assert response.status_code == 422
    assert await app.state.session_store.count() == 0
