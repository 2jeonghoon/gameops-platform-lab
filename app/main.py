from time import perf_counter
from uuid import UUID

from fastapi import FastAPI, HTTPException, Response, status
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
from starlette.requests import Request
from starlette.responses import JSONResponse

from app.models import Session, SessionCreate
from app.settings import Settings
from app.store import SessionStore
from app.telemetry import FaultController, InjectedFault, Telemetry


def _route_label(path: str) -> str:
    if path.startswith("/sessions/"):
        return "/sessions/{session_id}"
    if path in {"/sessions", "/healthz", "/readyz", "/metrics"}:
        return path
    return "unmatched"


def create_app(settings: Settings | None = None) -> FastAPI:
    app = FastAPI(title="GameOps Session API", version="0.1.0")
    app.state.settings = settings or Settings()
    app.state.session_store = SessionStore()
    app.state.fault_controller = FaultController(app.state.settings)
    app.state.telemetry = Telemetry()

    @app.middleware("http")
    async def observe_and_inject(request: Request, call_next):  # type: ignore[no-untyped-def]
        started = perf_counter()
        route = _route_label(request.url.path)
        try:
            if route.startswith("/sessions"):
                await app.state.fault_controller.apply()
            response = await call_next(request)
        except InjectedFault:
            response = JSONResponse(status_code=500, content={"detail": "Injected fault"})

        status_class = f"{response.status_code // 100}xx"
        labels = (request.method, route, status_class)
        app.state.telemetry.http_requests.labels(*labels).inc()
        app.state.telemetry.http_request_duration.labels(*labels).observe(perf_counter() - started)
        return response

    @app.get("/healthz")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/readyz")
    async def readiness() -> JSONResponse:
        if app.state.settings.readiness_fail:
            return JSONResponse(status_code=503, content={"status": "not_ready"})
        return JSONResponse(status_code=200, content={"status": "ready"})

    @app.get("/metrics")
    async def metrics() -> Response:
        return Response(
            content=generate_latest(app.state.telemetry.registry),
            headers={"Content-Type": CONTENT_TYPE_LATEST},
        )

    @app.post("/sessions", response_model=Session, status_code=status.HTTP_201_CREATED)
    async def create_session(payload: SessionCreate) -> Session:
        session = await app.state.session_store.create(payload)
        app.state.telemetry.sessions_created.inc()
        app.state.telemetry.active_sessions.set(await app.state.session_store.count())
        return session

    @app.get("/sessions/{session_id}", response_model=Session)
    async def get_session(session_id: UUID) -> Session:
        session = await app.state.session_store.get(session_id)
        if session is None:
            raise HTTPException(status_code=404, detail="Session not found")
        return session

    @app.delete("/sessions/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
    async def delete_session(session_id: UUID) -> Response:
        deleted = await app.state.session_store.delete(session_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="Session not found")
        app.state.telemetry.sessions_deleted.inc()
        app.state.telemetry.active_sessions.set(await app.state.session_store.count())
        return Response(status_code=status.HTTP_204_NO_CONTENT)

    return app


app = create_app()
