from datetime import datetime, timedelta

from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from app.db.session import Base
from app.models.todo import Todo
from app.repositories.todo_repository import TodoRepository


def test_expired_todos_are_deleted_only_after_successful_reminder():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)()
    now = datetime(2026, 9, 8, 0, 10)
    sent = Todo(title="已发送", due_at=now - timedelta(minutes=1), remind_at=now - timedelta(minutes=2), reminder_sent=True)
    failed = Todo(title="待重试", due_at=now - timedelta(minutes=1), remind_at=now - timedelta(minutes=2), reminder_sent=False)
    future = Todo(title="未来任务", due_at=now + timedelta(hours=1), remind_at=now + timedelta(minutes=30), reminder_sent=False)
    session.add_all([sent, failed, future])
    session.commit()

    assert TodoRepository(session).delete_expired(now) == 1
    remaining = {todo.title for todo in session.scalars(select(Todo)).all()}
    assert remaining == {"待重试", "未来任务"}
    session.close()
