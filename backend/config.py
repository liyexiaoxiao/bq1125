import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    SECRET_KEY: str = "fuzz_test_secret_key_change_in_production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24 hours
    
    DATABASE_URL: str = "sqlite:///./backend.db"
    
    # Paths - use /app as project root in Docker, or parent dir when running locally
    PROJECT_ROOT: str = os.environ.get("PROJECT_ROOT", "/app")
    CONFIG_FILE_PATH: str = os.path.join(PROJECT_ROOT, "app", "config.py")
    LOGS_DIR: str = os.path.join(PROJECT_ROOT, "logs")
    APP_DB_PATH: str = os.path.join(PROJECT_ROOT, "app", "db.db")
    START_PY_PATH: str = os.path.join(PROJECT_ROOT, "start.py")
    
    class Config:
        env_file = ".env"


settings = Settings()
