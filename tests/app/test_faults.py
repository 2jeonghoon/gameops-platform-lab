from collections.abc import Awaitable, Callable

import pytest
from httpx import ASGITransport, AsyncClient
from pydantic import ValidationError

from app.main import create_app
from app.settings import Settings
from app.telemetry import FaultController


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("fault_delay_ms", -1),
        ("fault_error_rate", -0.01),
        ("fault_error_rate", 1.01),
    ],
)
def test_invalid_fault_configuration_is_rejected(field: str, value: float) -> None:
    with pytest.raises(ValidationError):
        Settings(**{field: value})


@pytest.mark.anyio
async def test_readiness_failure_returns_service_unavailable() -> None:
    app = create_app(Settings(readiness_fail=True))

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/readyz")

    assert response.status_code == 503
    assert response.json() == {"status": "not_ready"}


@pytest.mark.anyio
async def test_full_error_rate_fails_session_route_but_not_health() -> None:
    app = create_app(Settings(fault_error_rate=1.0))

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        session_response = await client.post(
            "/sessions", json={"region": "ap-northeast-2", "player_count": 10}
        )
        health_response = await client.get("/healthz")

    assert session_response.status_code == 500
    assert session_response.json() == {"detail": "Injected fault"}
    assert health_response.status_code == 200


@pytest.mark.anyio
async def test_fault_delay_uses_injected_sleep() -> None:
    observed: list[float] = []

    async def fake_sleep(seconds: float) -> None:
        observed.append(seconds)

    sleeper: Callable[[float], Awaitable[None]] = fake_sleep
    controller = FaultController(Settings(fault_delay_ms=125), sleep=sleeper)

    await controller.apply()

    assert observed == [0.125]
