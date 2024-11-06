from pathlib import Path
from typing import Literal

from pydantic import BaseModel, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).parent.parent.parent


class AuthJWT(BaseModel):
    PRIVATE_KEY_PATH: Path = BASE_DIR / "app" / "certs" / "jwt-private.pem"
    PUBLIC_KEY_PATH: Path = BASE_DIR / "app" / "certs" / "jwt-public.pem"
    ALGORITHM: str = "RS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30


class Settings(BaseSettings):
    MODE: Literal["DEBUG", "TEST", "PROD"]
    LOG_LEVEL: Literal["INFO", "DEBUG"]

    DB_HOST: str
    DB_PORT: int
    DB_NAME: str
    DB_USER: str
    DB_PASS: str

    TEST_DB_HOST: str
    TEST_DB_PORT: int
    TEST_DB_NAME: str
    TEST_DB_USER: str
    TEST_DB_PASS: str

    AUTH_JWT: AuthJWT = AuthJWT()
    BASE_LIMIT_CHATS_FOR_USER: int
    BASE_LIMIT_MESSAGES_FOR_USER: int
    BASE_LIMIT_USERS_SEARCH: int
    BASE_LIMIT_MESSAGES_FOR_MODERATOR: int

    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env", env_file_encoding="utf-8"
    )

    @computed_field
    @property
    def DATABASE_URL(self) -> str:
        return f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASS}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

    @computed_field
    @property
    def TEST_DATABASE_URL(self) -> str:
        return f"postgresql+asyncpg://{self.TEST_DB_USER}:{self.TEST_DB_PASS}@{self.TEST_DB_HOST}:{self.TEST_DB_PORT}/{self.TEST_DB_NAME}"


settings = Settings()