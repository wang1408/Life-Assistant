from app.core.celery_app import celery_app


@celery_app.task(name="app.tasks.cleanup_tasks.cleanup_expired_actions")
def cleanup_expired_actions() -> None:
    return None

