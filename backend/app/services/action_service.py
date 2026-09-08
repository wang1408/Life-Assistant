import json
import uuid
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.models.action import AuditLog, PendingAction
from app.services.todo_service import TodoService
from app.schemas.todo import TodoCreate


class ActionService:
    def __init__(self, db: Session):
        self.db = db

    def create(self, action_type: str, payload: dict) -> PendingAction:
        action = PendingAction(action_type=action_type, payload=payload, idempotency_key=str(uuid.uuid4()), expires_at=datetime.utcnow() + timedelta(hours=1))
        self.db.add(action)
        self.db.commit()
        self.db.refresh(action)
        return action

    def execute(self, action_id: int) -> PendingAction | None:
        action = self.db.get(PendingAction, action_id)
        if not action or action.status != "pending":
            return action
        if action.action_type == "create_todo":
            TodoService(self.db).create(TodoCreate(**action.payload))
        action.status = "confirmed"
        self.db.add(AuditLog(event_type="action_confirmed", detail=json.dumps({"id": action_id, "type": action.action_type}, ensure_ascii=False)))
        self.db.commit()
        self.db.refresh(action)
        return action

    def reject(self, action_id: int) -> PendingAction | None:
        action = self.db.get(PendingAction, action_id)
        if not action or action.status != "pending":
            return action
        action.status = "rejected"
        self.db.commit()
        return action

