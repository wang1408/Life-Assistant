from sqlalchemy.orm import Session
from app.services.todo_service import TodoService
from app.services.memory_service import MemoryService
from app.repositories.action_repository import ActionRepository


def get_dashboard(db: Session) -> dict:
    return {
        "todos": [t for t in TodoService(db).list("open")],
        "memories": MemoryService(db).list(),
        "pending_actions": ActionRepository(db).pending(),
    }

