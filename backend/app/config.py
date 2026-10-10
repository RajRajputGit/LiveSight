"""Application configuration and settings for LiveSight Backend.

Conforms to Phase 4 guidelines in 02_SYSTEM_ARCHITECTURE.md and 07_LOCAL_SETUP_AND_RUNBOOK.md.
"""

from __future__ import annotations
import os
from pathlib import Path
from typing import List, Optional


class Settings:
    """Configurable settings loaded from environment variables with sensible defaults."""

    def __init__(self) -> None:
        self.app_env: str = os.getenv("APP_ENV", "development")
        self.api_host: str = os.getenv("API_HOST", "127.0.0.1")
        self.api_port: int = int(os.getenv("API_PORT", "8000"))

        # Database configuration
        # Prefer DATABASE_PATH if specified; else parse DATABASE_URL (e.g. sqlite:///./data/events.db)
        raw_db_path = os.getenv("DATABASE_PATH")
        if not raw_db_path:
            db_url = os.getenv("DATABASE_URL", "sqlite:///./data/events.db")
            if db_url.startswith("sqlite:///"):
                raw_db_path = db_url[len("sqlite:///") :]
            else:
                raw_db_path = "data/events.db"

        self.database_path: str = raw_db_path
        self.database_url: str = f"sqlite:///{self.database_path}"

        # Vision & Pipeline configuration
        self.video_source: Optional[str] = os.getenv("VIDEO_SOURCE", "0")
        self.model_name: str = os.getenv("MODEL_NAME", "yolo11n.pt")
        self.confidence_threshold: float = float(os.getenv("CONFIDENCE_THRESHOLD", "0.35"))
        self.tracking_enabled: bool = os.getenv("TRACKING_ENABLED", "true").lower() in (
            "true",
            "1",
            "yes",
        )
        self.tracker_config: str = os.getenv("TRACKER_CONFIG", "bytetrack.yaml")
        self.rules_config: str = os.getenv("RULES_CONFIG", "configs/rules.json")
        self.start_pipeline_on_startup: bool = os.getenv(
            "START_PIPELINE_ON_STARTUP", "false"
        ).lower() in ("true", "1", "yes")

        # CORS
        raw_cors = os.getenv(
            "CORS_ORIGINS",
            "http://localhost:3000,http://localhost:5173,http://127.0.0.1:3000,http://127.0.0.1:5173",
        )
        self.cors_origins: List[str] = [
            origin.strip() for origin in raw_cors.split(",") if origin.strip()
        ]

    def get_absolute_database_path(self, base_dir: Optional[Path] = None) -> Path:
        """Resolve database path relative to repository root if not absolute."""
        p = Path(self.database_path).expanduser()
        if p.is_absolute():
            return p
        root = base_dir or Path.cwd()
        return (root / p).resolve()


settings = Settings()
