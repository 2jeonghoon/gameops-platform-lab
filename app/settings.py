from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(case_sensitive=False, extra="forbid")

    fault_delay_ms: int = Field(default=0, ge=0)
    fault_error_rate: float = Field(default=0.0, ge=0.0, le=1.0)
    readiness_fail: bool = False
