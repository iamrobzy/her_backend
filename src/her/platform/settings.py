from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache
from typing import Optional

class _Settings(BaseSettings):
    elevenlabs_api_key: str
    agent_id: str
    agent_phone_number_id: Optional[str] = None
    database_url: str = "sqlite:///./her.db"

    phone_enabled: bool = True
    browser_enabled: bool = False

    # Pydantic-v2 style configuration
    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",          # ignore keys we haven't declared
    )

    @property
    def can_make_calls(self) -> bool:
        return bool(self.agent_phone_number_id)

@lru_cache
def get_settings() -> _Settings:
    return _Settings()

settings = get_settings()
