from __future__ import annotations

from sqlalchemy.orm import Session
from app.models.memory import Memory
from app.repositories.memory_repository import MemoryRepository


class MemoryService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = MemoryRepository(db)

    def list(self):
        return self.repo.list()

    def context(self) -> list[str]:
        return [m.content for m in self.repo.enabled()]

    def add_candidate(self, candidate: dict) -> Memory:
        existing = next((m for m in self.repo.list() if m.content == candidate["content"]), None)
        if existing:
            existing.confidence = max(existing.confidence, candidate.get("confidence", 0.5))
            existing.enabled = True
            self.db.commit()
            self.db.refresh(existing)
            return existing
        memory = Memory(**candidate)
        self.db.add(memory)
        self.db.commit()
        self.db.refresh(memory)
        return memory

    def update(self, memory_id: int, content: str | None = None, enabled: bool | None = None):
        memory = self.repo.get(memory_id)
        if not memory:
            return None
        if content is not None:
            memory.content = content
        if enabled is not None:
            memory.enabled = enabled
        self.db.commit()
        self.db.refresh(memory)
        return memory

    def delete(self, memory_id: int) -> bool:
        memory = self.repo.get(memory_id)
        if not memory:
            return False
        self.db.delete(memory)
        self.db.commit()
        return True
