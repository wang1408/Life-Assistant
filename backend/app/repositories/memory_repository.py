from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models.memory import Memory


class MemoryRepository:
    def __init__(self, db: Session):
        self.db = db

    def enabled(self, limit: int = 20) -> list[Memory]:
        return list(self.db.scalars(select(Memory).where(Memory.enabled.is_(True)).limit(limit)))

    def list(self) -> list[Memory]:
        return list(self.db.scalars(select(Memory).order_by(Memory.created_at.desc())))

    def get(self, memory_id: int) -> Memory | None:
        return self.db.get(Memory, memory_id)
