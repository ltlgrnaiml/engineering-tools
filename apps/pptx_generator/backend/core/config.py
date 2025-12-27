"""Application configuration settings."""

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings.

    Manages configuration from environment variables and defaults.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="allow",
    )

    APP_NAME: str = "PowerPoint Generator"
    DEBUG: bool = False
    API_V1_PREFIX: str = "/api/v1"

    CORS_ORIGINS: list[str] | str = [
        "http://localhost:3000",
        "http://localhost:3001",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001",
        "http://127.0.0.1:5173",
    ]

    @field_validator(
        "CORS_ORIGINS",
        "ALLOWED_TEMPLATE_EXTENSIONS",
        "ALLOWED_DATA_EXTENSIONS",
        "ALLOWED_DOMAIN_EXTENSIONS",
        mode="before",
    )
    @classmethod
    def parse_list_fields(cls, v: str | list[str]) -> list[str] | str:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        return v

    UPLOAD_DIR: str = "uploads"
    GENERATED_DIR: str = "generated"
    MAX_UPLOAD_SIZE: int = 50 * 1024 * 1024

    ALLOWED_TEMPLATE_EXTENSIONS: list[str] | str = [".pptx"]
    ALLOWED_DATA_EXTENSIONS: list[str] | str = [".csv", ".xlsx", ".xls"]
    ALLOWED_DOMAIN_EXTENSIONS: list[str] | str = [".yaml", ".yml", ".json"]


settings = Settings()
