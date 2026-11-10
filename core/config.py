from urllib.parse import quote

from pydantic import computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables or a .env file.
    This class uses Pydantic's BaseSettings to automatically read and validate
    configuration values from the environment or a .env file. 
    
    """
    
    database_connection_string: str | None = None
    database_password: str | None = None

    telegram_bot_token: str | None = None
    telegram_chat_id: str | None = None

    gemini_api_key: str | None = None

    @computed_field
    @property
    def encoded_password(self) -> str:
        return quote(self.database_password, safe="") if self.database_password else ""

    @computed_field
    @property
    def database_url(self) -> str:
        return self.database_connection_string.replace(
            "[YOUR-PASSWORD]", self.encoded_password
        ) if self.database_connection_string else ""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


settings = Settings()
