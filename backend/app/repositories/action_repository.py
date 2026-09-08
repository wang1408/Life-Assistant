from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models.action import PendingAction


class ActionRepository:
    def __init__(self, db: Session):
        self.db = db

    def get(self, action_id: int) -> PendingAction | None:
        return self.db.get(PendingAction, action_id)

    def pending(self) -> list[PendingAction]:
        return list(self.db.scalars(select(PendingAction).where(PendingAction.status == "pending")))

