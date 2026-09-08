from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.schemas.action import ActionRead
from app.services.action_service import ActionService

router = APIRouter()


@router.post("/{action_id}/confirm", response_model=ActionRead)
def confirm_action(action_id: int, db: Session = Depends(get_db)):
    action = ActionService(db).execute(action_id)
    if not action:
        raise HTTPException(404, "动作不存在")
    return action


@router.post("/{action_id}/reject", response_model=ActionRead)
def reject_action(action_id: int, db: Session = Depends(get_db)):
    action = ActionService(db).reject(action_id)
    if not action:
        raise HTTPException(404, "动作不存在")
    return action

