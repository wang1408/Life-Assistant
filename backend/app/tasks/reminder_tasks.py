import logging
from datetime import datetime
from zoneinfo import ZoneInfo
from app.core.celery_app import celery_app
from app.db.session import SessionLocal
from app.repositories.todo_repository import TodoRepository
from app.providers.smtp_client import SMTPClient
from app.models.notification import NotificationLog
from app.core.config import get_settings

logger = logging.getLogger(__name__)


def _reminder_now(settings) -> datetime:
    """以配置的本地时区生成无时区时间，兼容当前 SQLite/MySQL 的存储方式。"""
    try:
        timezone = ZoneInfo(settings.reminder_timezone)
    except Exception:
        timezone = ZoneInfo("Asia/Shanghai")
    return datetime.now(timezone).replace(tzinfo=None)


@celery_app.task(name="app.tasks.reminder_tasks.scan_and_send_reminders")
def scan_and_send_reminders() -> int:
    db = SessionLocal()
    sent = 0
    try:
        settings = get_settings()
        repository = TodoRepository(db)
        now = _reminder_now(settings)
        for todo in repository.due_for_reminder(now):
            log = NotificationLog(todo_id=todo.id, status="pending")
            try:
                if not getattr(settings, "reminder_email_to", ""):
                    raise RuntimeError("未配置 REMINDER_EMAIL_TO")
                SMTPClient().send(settings.reminder_email_to, f"待办提醒：{todo.title}", todo.description or todo.title)
                todo.reminder_sent = True
                log.status = "sent"
                log.sent_at = datetime.utcnow()
                sent += 1
            except Exception as exc:
                log.status = "failed"
                log.error = str(exc)
                log.retries = 1
            db.add(log)
            db.commit()
        repository.delete_expired(now)
        return sent
    finally:
        db.close()
