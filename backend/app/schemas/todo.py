from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field


class TodoCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    description: str | None = None
    due_at: datetime | None = None
    remind_at: datetime | None = None
    repeat_rule: str | None = None
    priority: int = Field(default=2, ge=1, le=3)


class TodoUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    due_at: datetime | None = None
    remind_at: datetime | None = None
    repeat_rule: str | None = None
    priority: int | None = Field(default=None, ge=1, le=3)
    status: str | None = None


class TodoRead(TodoCreate):
    id: int
    status: str
    reminder_sent: bool
    model_config = ConfigDict(from_attributes=True)

