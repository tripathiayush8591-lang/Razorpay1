from pathlib import Path
from typing import List, Union
from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Base directory for backend
BASE_DIR = Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR.parent / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    PORT: int = 8000
    HOST: str = "0.0.0.0"
    ENVIRONMENT: str = "development"
    AUTO_CREATE_TABLES: bool = True
    DATABASE_URL: str = f"sqlite:///{(BASE_DIR / 'data' / 'store.db').as_posix()}"
    CORS_ORIGINS: Union[List[str], str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]
    FRONTEND_PUBLIC_URL: str = "http://localhost:5173"
    MCP_STREAMABLE_HTTP_URL: str = "http://localhost:8000/mcp/"
    RENDER_EXTERNAL_URL: str = ""

    ADMIN_EMAIL: str = "admin@runcraft.internal"
    ADMIN_PASSWORD: str = "demosecret123"
    AUTH_SECRET_KEY: str = "demo_commerce_auth_secret_key_runcraft_2026"
    STATIC_UPLOADS_DIR: Path = BASE_DIR / "data" / "uploads"

    RAZORPAY_KEY_ID: str = "rzp_test_placeholder"
    RAZORPAY_KEY_SECRET: str = "placeholder_secret"
    RAZORPAY_WEBHOOK_SECRET: str = "placeholder_webhook_secret"

    OPENAI_API_KEY: str = ""
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-2.5-flash"

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str):
            return [i.strip() for i in v.split(",") if i.strip()]
        return v

    @field_validator("STATIC_UPLOADS_DIR", mode="before")
    @classmethod
    def parse_uploads_dir(cls, v: Union[str, Path]) -> Path:
        return Path(v).expanduser() if isinstance(v, str) else v

    @field_validator("FRONTEND_PUBLIC_URL", "MCP_STREAMABLE_HTTP_URL", mode="after")
    @classmethod
    def strip_trailing_whitespace(cls, v: str) -> str:
        return v.strip()

    @model_validator(mode="after")
    def validate_production_settings(self) -> "Settings":
        if (
            self.ENVIRONMENT.lower() == "production"
            and self.MCP_STREAMABLE_HTTP_URL == "http://localhost:8000/mcp/"
            and self.RENDER_EXTERNAL_URL
        ):
            self.MCP_STREAMABLE_HTTP_URL = f"{self.RENDER_EXTERNAL_URL.rstrip('/')}/mcp/"

        if self.ENVIRONMENT.lower() != "production":
            return self

        insecure_values = {
            "ADMIN_PASSWORD": self.ADMIN_PASSWORD == "demosecret123",
            "AUTH_SECRET_KEY": self.AUTH_SECRET_KEY == "demo_commerce_auth_secret_key_runcraft_2026",
            "RAZORPAY_KEY_SECRET": self.RAZORPAY_KEY_SECRET == "placeholder_secret",
            "RAZORPAY_WEBHOOK_SECRET": self.RAZORPAY_WEBHOOK_SECRET == "placeholder_webhook_secret",
            "GEMINI_API_KEY": not self.GEMINI_API_KEY,
        }
        invalid = [name for name, is_invalid in insecure_values.items() if is_invalid]
        if invalid:
            joined = ", ".join(invalid)
            raise ValueError(f"Production environment requires secure values for: {joined}")

        cors_origins = self.CORS_ORIGINS if isinstance(self.CORS_ORIGINS, list) else [self.CORS_ORIGINS]
        if any(origin in {"*", "http://localhost:5173", "http://127.0.0.1:5173"} for origin in cors_origins):
            raise ValueError("Production CORS_ORIGINS must contain only public HTTPS frontend origins.")
        if not all(origin.startswith("https://") for origin in cors_origins):
            raise ValueError("Production CORS_ORIGINS must use HTTPS origins.")
        if not self.FRONTEND_PUBLIC_URL.startswith("https://"):
            raise ValueError("Production FRONTEND_PUBLIC_URL must be a public HTTPS URL.")
        if not self.MCP_STREAMABLE_HTTP_URL.startswith("https://"):
            raise ValueError("Production MCP_STREAMABLE_HTTP_URL must be a public HTTPS URL.")
        if not self.MCP_STREAMABLE_HTTP_URL.endswith("/"):
            raise ValueError("Production MCP_STREAMABLE_HTTP_URL must end with a trailing slash.")

        return self


settings = Settings()
