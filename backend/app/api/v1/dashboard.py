from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.services.dashboard_service import get_dashboard

router = APIRouter()


@router.get("/today")
def today(db: Session = Depends(get_db)):
    data = get_dashboard(db)
    return {
        "todos": [{"id": x.id, "title": x.title, "due_at": x.due_at, "remind_at": x.remind_at, "status": x.status} for x in data["todos"]],
        "memories": [{"id": x.id, "category": x.category, "content": x.content, "enabled": x.enabled} for x in data["memories"]],
        "pending_actions": [{"id": x.id, "action_type": x.action_type, "payload": x.payload, "status": x.status} for x in data["pending_actions"]],
    }

