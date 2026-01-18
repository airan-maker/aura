from pydantic_settings import BaseSettings
from typing import List
import json


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Database
    DATABASE_URL: str

    # Anthropic Claude
    ANTHROPIC_API_KEY: str

    # Security
    SECRET_KEY: str
    ALLOWED_ORIGINS: str = '["http://localhost:3000"]'

    # Crawler
    CRAWLER_TIMEOUT: int = 30000
    MAX_CONCURRENT_ANALYSES: int = 5

    # Environment
    ENVIRONMENT: str = "development"

    # Logging
    LOG_LEVEL: str = "INFO"

    @property
    def allowed_origins_list(self) -> List[str]:
        """Parse ALLOWED_ORIGINS JSON string to list."""
        try:
            return json.loads(self.ALLOWED_ORIGINS)
        except json.JSONDecodeError:
            return ["http://localhost:3000"]

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
