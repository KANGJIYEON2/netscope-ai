from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
    )

    # ===============================
    # Core
    # ===============================
    SECRET_KEY: str
    APP_ENV: str = "local"  # local | prod

    # ===============================
    # Token
    # ===============================
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 14

    # ===============================
    # Infra
    # ===============================
    DATABASE_URL: str | None = None
    OPENAI_API_KEY: str | None = None

    # ===============================
    # Frontend / CORS
    # ===============================
    # Comma-separated origins: "http://localhost:3000,https://app.example.com"
    FRONTEND_ORIGIN: str = "http://localhost:3000"

    @property
    def cors_origins(self) -> list[str]:
        return [o.strip() for o in self.FRONTEND_ORIGIN.split(",") if o.strip()]

    # ===============================
    # Cookie (Auth)
    # ===============================
    COOKIE_SECURE: bool = False
    COOKIE_SAMESITE: str = "lax"

    @property
    def is_prod(self) -> bool:
        return self.APP_ENV == "prod"


settings = Settings()
