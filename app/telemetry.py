import asyncio
import random
from collections.abc import Awaitable, Callable

from prometheus_client import CollectorRegistry, Counter, Gauge, Histogram

from app.settings import Settings

Sleep = Callable[[float], Awaitable[None]]
RandomSource = Callable[[], float]


class InjectedFault(RuntimeError):
    """Raised when the configured experiment injects an application failure."""


class FaultController:
    def __init__(
        self,
        settings: Settings,
        *,
        sleep: Sleep = asyncio.sleep,
        random_source: RandomSource = random.random,
    ) -> None:
        self.settings = settings
        self._sleep = sleep
        self._random_source = random_source

    async def apply(self) -> None:
        if self.settings.fault_delay_ms:
            await self._sleep(self.settings.fault_delay_ms / 1000)
        if self._random_source() < self.settings.fault_error_rate:
            raise InjectedFault("Injected fault")


class Telemetry:
    def __init__(self) -> None:
        self.registry = CollectorRegistry()
        self.http_requests = Counter(
            "gameops_http_requests_total",
            "HTTP requests handled by the GameOps API.",
            ("method", "route", "status_class"),
            registry=self.registry,
        )
        self.http_request_duration = Histogram(
            "gameops_http_request_duration_seconds",
            "HTTP request duration for the GameOps API.",
            ("method", "route", "status_class"),
            registry=self.registry,
        )
        self.active_sessions = Gauge(
            "gameops_active_sessions",
            "Number of sessions currently held in memory.",
            registry=self.registry,
        )
        self.sessions_created = Counter(
            "gameops_sessions_created_total",
            "Sessions created since process start.",
            registry=self.registry,
        )
        self.sessions_deleted = Counter(
            "gameops_sessions_deleted_total",
            "Sessions deleted since process start.",
            registry=self.registry,
        )
