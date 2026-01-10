import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    BACKBOARD_API_KEY: str | None = os.getenv("BACKBOARD_API_KEY")
    BACKBOARD_BASE_URL: str = os.getenv(
        "BACKBOARD_BASE_URL", "https://app.backboard.io/api")
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./data.db")
    TZ_DEFAULT: str = os.getenv("TZ_DEFAULT", "UTC")


settings = Settings()
