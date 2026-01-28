from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
    )

    SECRET_KEY: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # 너 env에 있는 것들 추가 (필요 없으면 optional로 두거나 지워도 됨)
    OPENAI_API_KEY: str | None = None
    APP_ENV: str = "local"
    DATABASE_URL: str | None = None

    # (refresh 토큰 도입할 거니까 미리)
    REFRESH_TOKEN_EXPIRE_DAYS: int = 14


settings = Settings()