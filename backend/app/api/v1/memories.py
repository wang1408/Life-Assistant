from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.schemas.memory import MemoryRead, MemoryUpdate
from app.services.memory_service import MemoryService

router = APIRouter()


@router.get("", response_model=list[MemoryRead])
def list_memories(db: Session = Depends(get_db)):
    return MemoryService(db).list()


@router.patch("/{memory_id}", response_model=MemoryRead)
def update_memory(memory_id: int, data: MemoryUpdate, db: Session = Depends(get_db)):
    memory = MemoryService(db).update(memory_id, data.content, data.enabled)
    if not memory:
        raise HTTPException(404, "记忆不存在")
    return memory


@router.delete("/{memory_id}")
def delete_memory(memory_id: int, db: Session = Depends(get_db)):
    if not MemoryService(db).delete(memory_id):
        raise HTTPException(404, "记忆不存在")
    return {"deleted": True}

