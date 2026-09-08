import re
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.models.todo import Todo
from app.schemas.todo import TodoCreate, TodoUpdate
from app.repositories.todo_repository import TodoRepository


def parse_natural_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        pass
    now = datetime.now()
    relative = re.search(r"(半|[零一二两三四五六七八九十百千万\d]+)\s*(个小时|小时|分钟|分|天|日)后", value)
    if relative:
        amount = _parse_natural_number(relative.group(1))
        if amount is None:
            return None
        unit = relative.group(2)
        if unit in ("分钟", "分"):
            return now + timedelta(minutes=amount)
        if unit in ("小时", "个小时"):
            return now + timedelta(hours=amount)
        return now + timedelta(days=amount)
    match = re.search(r"(今天|明天|后天)?\s*(早上|上午|中午|下午|晚上)?\s*(\d{1,2})(?:点|时|:\s*)(\d{1,2})?", value)
    if not match:
        return None
    day = {"明天": 1, "后天": 2}.get(match.group(1), 0)
    hour = int(match.group(3))
    period = match.group(2)
    if period in ("下午", "晚上") and hour < 12:
        hour += 12
    elif period == "中午" and hour < 11:
        hour += 12
    return (now + timedelta(days=day)).replace(hour=hour, minute=int(match.group(4) or 0), second=0, microsecond=0)


def _parse_natural_number(value: str) -> float | None:
    if value == "半":
        return 0.5
    if value.isdigit():
        return float(value)
    digits = {"零": 0, "一": 1, "二": 2, "两": 2, "三": 3, "四": 4, "五": 5, "六": 6, "七": 7, "八": 8, "九": 9}
    if value == "十":
        return 10
    if "十" in value:
        left, right = value.split("十", 1)
        tens = digits.get(left, 1) if left else 1
        ones = digits.get(right, 0) if right else 0
        return float(tens * 10 + ones)
    if len(value) == 1 and value in digits:
        return float(digits[value])
    return None


class TodoService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = TodoRepository(db)

    def list(self, status: str | None = None):
        return self.repo.list(status)

    def create(self, data: TodoCreate) -> Todo:
        todo = Todo(**data.model_dump())
        return self.repo.save(todo)

    def update(self, todo_id: int, data: TodoUpdate) -> Todo | None:
        todo = self.repo.get(todo_id)
        if not todo:
            return None
        changes = data.model_dump(exclude_unset=True)
        # 调整提醒时间意味着用户希望重新安排一次投递。
        if "remind_at" in changes and changes["remind_at"] != todo.remind_at:
            todo.reminder_sent = False
        for key, value in changes.items():
            setattr(todo, key, value)
        return self.repo.save(todo)

    def complete(self, todo_id: int) -> Todo | None:
        return self.update(todo_id, TodoUpdate(status="completed"))

    def delete(self, todo_id: int) -> bool:
        todo = self.repo.get(todo_id)
        if not todo:
            return False
        self.db.delete(todo)
        self.db.commit()
        return True
