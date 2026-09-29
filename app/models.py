from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class SessionCreate(BaseModel):
    region: str = Field(min_length=1, max_length=32)
    player_count: int = Field(ge=1, le=100)


class Session(SessionCreate):
    model_config = ConfigDict(frozen=True)

    id: UUID
    created_at: datetime
