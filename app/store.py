import asyncio
from datetime import UTC, datetime
from uuid import UUID, uuid4

from app.models import Session, SessionCreate


class SessionStore:
    def __init__(self) -> None:
        self._sessions: dict[UUID, Session] = {}
        self._lock = asyncio.Lock()

    async def create(self, payload: SessionCreate) -> Session:
        session = Session(id=uuid4(), created_at=datetime.now(UTC), **payload.model_dump())
        async with self._lock:
            self._sessions[session.id] = session
        return session

    async def get(self, session_id: UUID) -> Session | None:
        async with self._lock:
            return self._sessions.get(session_id)

    async def delete(self, session_id: UUID) -> bool:
        async with self._lock:
            return self._sessions.pop(session_id, None) is not None

    async def count(self) -> int:
        async with self._lock:
            return len(self._sessions)
