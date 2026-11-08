from urllib.parse import quote

from pydantic import computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_connection_string: str
    database_password: str

    telegram_bot_token: str | None = None
    telegram_chat_id: str | None = None

    gemini_api_key: str | None = None

    @computed_field
    @property
    def encoded_password(self) -> str:
        return quote(self.database_password, safe="")

    @computed_field
    @property
    def database_url(self) -> str:
        return self.database_connection_string.replace(
            "[YOUR-PASSWORD]", self.encoded_password
        )

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


settings = Settings()
