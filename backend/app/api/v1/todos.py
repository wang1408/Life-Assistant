from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.schemas.todo import TodoCreate, TodoRead, TodoUpdate
from app.services.todo_service import TodoService

router = APIRouter()


@router.get("", response_model=list[TodoRead])
def list_todos(status: str | None = None, db: Session = Depends(get_db)):
    return TodoService(db).list(status)


@router.post("", response_model=TodoRead)
def create_todo(data: TodoCreate, db: Session = Depends(get_db)):
    return TodoService(db).create(data)


@router.patch("/{todo_id}", response_model=TodoRead)
def update_todo(todo_id: int, data: TodoUpdate, db: Session = Depends(get_db)):
    todo = TodoService(db).update(todo_id, data)
    if not todo:
        raise HTTPException(404, "待办不存在")
    return todo


@router.post("/{todo_id}/complete", response_model=TodoRead)
def complete_todo(todo_id: int, db: Session = Depends(get_db)):
    todo = TodoService(db).complete(todo_id)
    if not todo:
        raise HTTPException(404, "待办不存在")
    return todo


@router.delete("/{todo_id}")
def delete_todo(todo_id: int, db: Session = Depends(get_db)):
    if not TodoService(db).delete(todo_id):
        raise HTTPException(404, "待办不存在")
    return {"deleted": True, "id": todo_id}
