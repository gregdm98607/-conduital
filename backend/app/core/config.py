"""
Application configuration

Supports commercial module configurations:
- basic: Core + Projects (default)
- gtd: Core + Projects + Inbox
- proactive_assistant: Core + Projects + Memory Layer + AI Context
- full: All modules enabled
"""

import secrets
from pathlib import Path
from typing import Optional, Literal

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


def _get_or_generate_secret_key() -> str:
    """
    Get JWT secret from environment, or auto-generate and persist one.

    On first run, generates a cryptographically secure secret and writes it
    to the .env file so it persists across restarts. This prevents shipping
    a weak default secret in the codebase.
    """
    import os

    # If already set in environment, use it
    env_key = os.environ.get("SECRET_KEY")
    if env_key and env_key != "change-me-in-production-use-openssl-rand-hex-32":
        return env_key

    # Check if it's in the .env file already
    env_file = Path(__file__).parent.parent.parent / ".env"
    if env_file.exists():
        for line in env_file.read_text(encoding="utf-8").splitlines():
            stripped = line.strip()
            if stripped.startswith("SECRET_KEY=") and not stripped.startswith("#"):
                value = stripped.split("=", 1)[1].strip().strip('"').strip("'")
                if value and value != "change-me-in-production-use-openssl-rand-hex-32":
                    return value

    # Generate a new secret
    new_secret = secrets.token_urlsafe(64)

    # Persist to .env file
    try:
        if env_file.exists():
            content = env_file.read_text(encoding="utf-8")
            # Replace existing placeholder or append
            if "SECRET_KEY=" in content:
                lines = content.splitlines()
                for i, line in enumerate(lines):
                    stripped = line.strip()
                    if stripped.startswith("SECRET_KEY=") or stripped.startswith("# SECRET_KEY="):
                        lines[i] = f"SECRET_KEY={new_secret}"
                        break
                env_file.write_text("\n".join(lines) + "\n", encoding="utf-8")
            else:
                with open(env_file, "a", encoding="utf-8") as f:
                    f.write(f"\n# Auto-generated JWT signing key\nSECRET_KEY={new_secret}\n")
        else:
            env_file.write_text(
                f"# Auto-generated JWT signing key\nSECRET_KEY={new_secret}\n",
                encoding="utf-8",
            )
    except OSError:
        pass  # If we can't persist, still use the generated secret for this session

    return new_secret


# Commercial configuration presets
COMMERCIAL_PRESETS = {
    "basic": ["core", "projects"],
    "gtd": ["core", "projects", "gtd_inbox"],
    "proactive_assistant": ["core", "projects", "memory_layer", "ai_context"],
    "full": ["core", "projects", "gtd_inbox", "memory_layer", "ai_context"],
}


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    APP_NAME: str = "Conduital"
    VERSION: str = "1.0.0-alpha"
    DEBUG: bool = False

    # ==========================================================================
    # Module System Configuration
    # ==========================================================================

    # Commercial mode: basic, gtd, proactive_assistant, full
    # Or set ENABLED_MODULES directly for custom configurations
    COMMERCIAL_MODE: str = "basic"

    # Explicit list of enabled modules (overrides COMMERCIAL_MODE if set)
    # Example: ENABLED_MODULES=["core", "projects", "memory_layer"]
    ENABLED_MODULES: Optional[list[str]] = None

    # Database
    DATABASE_PATH: str = str(Path.home() / ".conduital" / "tracker.db")
    DATABASE_ECHO: bool = False  # Log SQL queries

    # Markdown File Sync Integration
    # NOTE: Set SECOND_BRAIN_ROOT in .env - this default may not exist on your system
    SECOND_BRAIN_ROOT: Optional[str] = None  # Required for sync features
    WATCH_DIRECTORIES: list[str] = ["10_Projects", "20_Areas"]
    SYNC_INTERVAL: int = 30  # seconds
    CONFLICT_STRATEGY: str = "prompt"  # prompt, file_wins, db_wins, merge

    # Project Discovery
    # Map project folder prefixes (xx.xx) to area names
    # Example: "01" -> "Literary Projects", "10" -> "Tech Projects"
    AREA_PREFIX_MAP: dict[str, str] = {
        "01": "Literary Projects",
        "10": "Personal Development",
        "20": "Research"
    }
    # Pattern for project folders: xx.xx Project_Name
    PROJECT_FOLDER_PATTERN: str = r"^(\d{2})\.(\d{2})\s+(.+)$"

    # Auto-Discovery (Phase 2)
    AUTO_DISCOVERY_ENABLED: bool = False  # Enable automatic discovery on folder changes
    AUTO_DISCOVERY_DEBOUNCE: float = 2.0  # Seconds to wait before processing folder events

    # AI Integration
    AI_PROVIDER: str = "anthropic"  # anthropic, openai, google
    ANTHROPIC_API_KEY: Optional[str] = None
    OPENAI_API_KEY: Optional[str] = None
    GOOGLE_API_KEY: Optional[str] = None
    AI_MODEL: str = "claude-sonnet-4-5-20250929"
    AI_MAX_TOKENS: int = 2000
    AI_FEATURES_ENABLED: bool = False

    # Momentum Calculation
    MOMENTUM_ACTIVITY_DECAY_DAYS: int = 30
    MOMENTUM_STALLED_THRESHOLD_DAYS: int = 14
    MOMENTUM_AT_RISK_THRESHOLD_DAYS: int = 7
    MOMENTUM_RECALCULATE_INTERVAL: int = 3600  # seconds

    # API
    API_V1_PREFIX: str = "/api/v1"
    # CORS allowed origins — include common dev ports so Vite fallback ports work.
    # Frontend uses Vite proxy (/api/v1 -> backend), so CORS is only needed
    # for non-proxy dev setups. Override via CORS_ORIGINS in .env for production.
    CORS_ORIGINS: list[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://localhost:5174",
        "http://localhost:5175",
    ]

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v: str | list[str]) -> list[str]:
        """Parse CORS_ORIGINS from comma-separated string or JSON array.

        Accepts:
        - Comma-separated: "http://localhost:3000,http://localhost:5173"
        - JSON array: '["http://localhost:3000","http://localhost:5173"]'
        - Already-parsed list (from default or pydantic-settings)
        """
        if isinstance(v, list):
            return v
        if isinstance(v, str):
            # Try JSON parse first (pydantic-settings may pass stringified JSON)
            v = v.strip()
            if v.startswith("["):
                import json
                try:
                    return json.loads(v)
                except json.JSONDecodeError:
                    pass
            # Fall back to comma-separated
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v

    # Server
    SERVER_HOST: str = "0.0.0.0"
    SERVER_PORT: int = 8000

    # Logging
    LOG_LEVEL: str = "INFO"  # DEBUG, INFO, WARNING, ERROR, CRITICAL
    LOG_TO_FILE: bool = True  # Write logs to file
    LOG_TO_CONSOLE: bool = True  # Output logs to console
    LOG_DIR: Optional[str] = None  # Custom log directory (default: ~/.conduital/logs)
    LOG_MAX_BYTES: int = 10 * 1024 * 1024  # 10 MB max per log file
    LOG_BACKUP_COUNT: int = 5  # Number of backup log files to keep

    # Authentication (ROADMAP-009)
    AUTH_ENABLED: bool = False  # Set True to enable auth (False for backwards compat during migration)
    SECRET_KEY: str = _get_or_generate_secret_key()  # Auto-generated on first run
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 30

    # Google OAuth
    GOOGLE_CLIENT_ID: Optional[str] = None
    GOOGLE_CLIENT_SECRET: Optional[str] = None
    GOOGLE_REDIRECT_URI: str = "http://localhost:8000/api/v1/auth/google/callback"

    # Frontend URL for OAuth redirects
    FRONTEND_URL: str = "http://localhost:5173"

    @property
    def DATABASE_URL(self) -> str:
        """Construct SQLite database URL"""
        return f"sqlite:///{self.DATABASE_PATH}"

    @property
    def SECOND_BRAIN_PATH(self) -> Optional[Path]:
        """Get synced notes root as Path object"""
        if self.SECOND_BRAIN_ROOT:
            return Path(self.SECOND_BRAIN_ROOT)
        return None

    def get_enabled_modules(self) -> list[str]:
        """
        Get list of enabled module names.

        Priority:
        1. ENABLED_MODULES if explicitly set
        2. Modules from COMMERCIAL_MODE preset
        """
        if self.ENABLED_MODULES:
            return self.ENABLED_MODULES

        if self.COMMERCIAL_MODE not in COMMERCIAL_PRESETS:
            # Fall back to basic if invalid mode
            return COMMERCIAL_PRESETS["basic"]

        return COMMERCIAL_PRESETS[self.COMMERCIAL_MODE]

    def is_module_enabled(self, module_name: str) -> bool:
        """Check if a specific module is enabled"""
        return module_name in self.get_enabled_modules()


# Global settings instance
settings = Settings()
