from functools import lru_cache
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parents[3]
BACKEND_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    app_env: str = "development"
    database_url: str = "sqlite:///./life_assistant.db"
    redis_url: str = "redis://localhost:6379/0"
    qwen_api_key: str = ""
    qwen_base_url: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    qwen_fast_model: str = "qwen-turbo"
    qwen_smart_model: str = "qwen-plus"
    amap_api_key: str = ""
    qweather_api_key: str = ""
    # 和风天气控制台为项目分配的专属 API Host，例如 xxx.xy.qweatherapi.com
    qweather_api_host: str = ""
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_username: str = ""
    smtp_password: str = ""
    smtp_from: str = ""
    reminder_email_to: str = ""
    reminder_timezone: str = "Asia/Shanghai"
    # 本机直接运行 Uvicorn 时启用；Docker 部署由 Celery Beat 负责扫描。
    reminder_local_runner: bool = True
    reminder_poll_interval_seconds: int = 30
    frontend_origin: str = "http://localhost:5173"
    # Support both `project/.env` and `project/backend/.env`, regardless of
    # whether Uvicorn is started from the repository root or backend folder.
    model_config = SettingsConfigDict(
        env_file=(str(PROJECT_ROOT / ".env"), str(BACKEND_ROOT / ".env")),
        extra="ignore",
        case_sensitive=False,
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
