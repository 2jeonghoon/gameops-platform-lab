from uuid import UUID

from fastapi import FastAPI, HTTPException, Response, status

from app.models import Session, SessionCreate
from app.settings import Settings
from app.store import SessionStore


def create_app(settings: Settings | None = None) -> FastAPI:
    app = FastAPI(title="GameOps Session API", version="0.1.0")
    app.state.settings = settings or Settings()
    app.state.session_store = SessionStore()

    @app.get("/healthz")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/readyz")
    async def readiness() -> dict[str, str]:
        return {"status": "ready"}

    @app.post("/sessions", response_model=Session, status_code=status.HTTP_201_CREATED)
    async def create_session(payload: SessionCreate) -> Session:
        return await app.state.session_store.create(payload)

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
        return Response(status_code=status.HTTP_204_NO_CONTENT)

    return app


app = create_app()
