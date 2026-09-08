from __future__ import annotations

from datetime import datetime
from sqlalchemy import or_, select
from sqlalchemy.orm import Session
from app.models.todo import Todo


class TodoRepository:
    def __init__(self, db: Session):
        self.db = db

    def list(self, status: str | None = None) -> list[Todo]:
        stmt = select(Todo).order_by(Todo.due_at.asc())
        if status:
            stmt = stmt.where(Todo.status == status)
        return list(self.db.scalars(stmt))

    def get(self, todo_id: int) -> Todo | None:
        return self.db.get(Todo, todo_id)

    def due_for_reminder(self, now: datetime) -> list[Todo]:
        stmt = select(Todo).where(Todo.status == "open", Todo.reminder_sent.is_(False), Todo.remind_at <= now)
        return list(self.db.scalars(stmt))

    def delete_expired(self, now: datetime) -> int:
        """删除已过截止时间且不再需要重试提醒的开放待办。"""
        stmt = select(Todo).where(
            Todo.status == "open",
            Todo.due_at.is_not(None),
            Todo.due_at <= now,
            or_(Todo.remind_at.is_(None), Todo.reminder_sent.is_(True)),
        )
        expired = list(self.db.scalars(stmt))
        for todo in expired:
            self.db.delete(todo)
        if expired:
            self.db.commit()
        return len(expired)

    def save(self, todo: Todo) -> Todo:
        self.db.add(todo)
        self.db.commit()
        self.db.refresh(todo)
        return todo
