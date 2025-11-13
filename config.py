import os
from pydantic_settings import BaseSettings  # type: ignore
from pydantic import ConfigDict  # type: ignore
import dotenv




class Settings(BaseSettings):
    BOT_TOKEN: str
    POSTGRES_URL: str

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"



settings = Settings()


if not settings.BOT_TOKEN:
    raise ValueError("BOT_TOKEN не установлен в .env файле!")