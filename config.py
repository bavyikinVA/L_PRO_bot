from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # bot part
    BOT_TOKEN: str
    ADMIN_IDS: List[int]

    # log part
    FORMAT_LOG: str = "{time:YYYY-MM-DD at HH:mm:ss} | {level} | {message}"
    LOG_ROTATION: str = "10 MB"

    # db part
    POSTGRES_HOST: str
    POSTGRES_PORT: int
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str

    # redis part
    REDIS_HOST: str
    REDIS_PORT: int
    REDIS_DB: int = 0
    REDIS_PASSWORD: str | None = None

    # web part
    BASE_SITE: str
    TG_API_SITE: str
    FRONT_SITE: str
    UPLOAD_FOLDER: str = '/static/images/'

    WEBHOOK_SECRET: str

    ENVIRONMENT: str = "dev"
    ALLOWED_ORIGINS: str = "http://localhost:3000,http://127.0.0.1:3000"

    def get_allowed_origins(self) -> list[str]:
        return [
            origin.strip()
            for origin in self.ALLOWED_ORIGINS.split(",")
            if origin.strip()
        ]

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8"
    )

    def get_webhook_url(self) -> str:
        """Возвращает URL вебхука с кодированием специальных символов."""
        return f"{self.BASE_SITE}/webhook/{self.WEBHOOK_SECRET}"

    def get_tg_api_url(self) -> str:
        """Возвращает URL TG с Bot Token."""
        return f"{self.TG_API_SITE}/bot{self.BOT_TOKEN}"

    def get_db_url(self) -> str:
        return f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

    def get_redis_url(self) -> str:
        password_part = f":{self.REDIS_PASSWORD}@" if self.REDIS_PASSWORD else ""
        return f"redis://{password_part}{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"


settings = Settings()
database_url = settings.get_db_url()
