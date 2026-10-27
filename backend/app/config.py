import os
from pathlib import Path
from typing import Dict, Any, List
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent
ROOT_DIR = BASE_DIR.parent
LOGS_DIR = BASE_DIR / "logs"
LOGS_DIR.mkdir(parents=True, exist_ok=True)

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(str(BASE_DIR / ".env"), str(ROOT_DIR / ".env")),
        env_file_encoding="utf-8",
        extra="ignore"
    )

    PORT: int = 8000
    HOST: str = "127.0.0.1"
    DEBUG: bool = True
    DATABASE_URL: str = f"sqlite:///{BASE_DIR / 'music_recommender.db'}"

    # External APIs
    LASTFM_API_KEY: str = ""
    MUSICBRAINZ_USER_AGENT: str = "TWSMAMusicRecommender/1.0.0 (contact@example.com)"
    YOUTUBE_API_KEY: str = ""

    # RSS Text Feeds for TWSMA
    MUSIC_RSS_FEEDS: str = "https://pitchfork.com/feed/feed-news/rss,https://feeds.feedburner.com/stereogum/cBYa"

    # Default Hybrid Weights
    WEIGHT_CONTENT: float = 0.40
    WEIGHT_COLLABORATIVE: float = 0.30
    WEIGHT_TREND: float = 0.20
    WEIGHT_TEXT: float = 0.10

    # Logging
    LOG_FILE: str = str(LOGS_DIR / "app.log")
    LOG_RETENTION_LINES: int = 5000

settings = Settings()

def redact_secrets(data: Any) -> Any:
    """Recursively redacts API keys, secrets, and auth tokens from dicts/lists/strings."""
    SENSITIVE_KEYS = {"key", "token", "secret", "password", "authorization", "api_key", "lastfm_api_key", "youtube_api_key"}
    if isinstance(data, dict):
        cleaned = {}
        for k, v in data.items():
            if any(s in k.lower() for s in SENSITIVE_KEYS):
                cleaned[k] = "[REDACTED]" if v else "[EMPTY]"
            else:
                cleaned[k] = redact_secrets(v)
        return cleaned
    elif isinstance(data, list):
        return [redact_secrets(item) for item in data]
    return data
