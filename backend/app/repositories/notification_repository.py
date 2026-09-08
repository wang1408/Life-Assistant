from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models.notification import NotificationLog


class NotificationRepository:
    def __init__(self, db: Session):
        self.db = db

    def for_todo(self, todo_id: int) -> NotificationLog | None:
        return self.db.scalar(select(NotificationLog).where(NotificationLog.todo_id == todo_id))

