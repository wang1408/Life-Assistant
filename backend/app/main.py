import asyncio
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1.router import api_router
from app.core.config import get_settings
from app.core.logging import configure_logging
from app.db.session import Base, engine, ensure_compat_schema
from app.db import base  # noqa: F401 - registers all models
from app.tasks.reminder_tasks import scan_and_send_reminders

logger = logging.getLogger(__name__)


async def _run_local_reminders(stop_event: asyncio.Event, interval: int) -> None:
    while not stop_event.is_set():
        try:
            await asyncio.to_thread(scan_and_send_reminders)
        except Exception:
            # SMTP/Redis 等外部服务短暂失败时，不应中断 API 进程。
            logger.exception("local reminder scan failed")
        try:
            await asyncio.wait_for(stop_event.wait(), timeout=max(5, interval))
        except asyncio.TimeoutError:
            continue


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging()
    Base.metadata.create_all(bind=engine)
    ensure_compat_schema()
    settings = get_settings()
    stop_event = asyncio.Event()
    reminder_task = None
    if settings.app_env.lower() in ("development", "dev") and settings.reminder_local_runner:
        reminder_task = asyncio.create_task(_run_local_reminders(stop_event, settings.reminder_poll_interval_seconds))
    try:
        yield
    finally:
        if reminder_task:
            stop_event.set()
            reminder_task.cancel()
            await asyncio.gather(reminder_task, return_exceptions=True)


app = FastAPI(title="Life Assistant API", version="0.1.0", lifespan=lifespan)
settings = get_settings()
app.add_middleware(CORSMiddleware, allow_origins=[settings.frontend_origin], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
app.include_router(api_router)


@app.get("/health")
def health():
    return {"status": "ok", "service": "life-assistant"}
