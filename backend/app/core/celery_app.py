from app.core.config import get_settings

try:
    from celery import Celery
except ImportError:  # pragma: no cover - allows the API to run without worker extras
    Celery = None

settings = get_settings()
if Celery:
    celery_app = Celery("life_assistant", broker=settings.redis_url, backend=settings.redis_url)
    celery_app.conf.beat_schedule = {
        "scan-reminders-every-minute": {
            "task": "app.tasks.reminder_tasks.scan_and_send_reminders",
            "schedule": 60.0,
        }
    }
    celery_app.conf.imports = (
        "app.tasks.reminder_tasks",
        "app.tasks.memory_tasks",
        "app.tasks.cleanup_tasks",
    )
else:
    class _UnavailableCelery:
        def task(self, *args, **kwargs):
            return lambda fn: fn
    celery_app = _UnavailableCelery()
