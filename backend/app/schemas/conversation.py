from datetime import datetime
from pydantic import BaseModel, ConfigDict


class ConversationCreate(BaseModel):
    title: str | None = None


class ConversationRead(BaseModel):
    id: int
    title: str
    created_at: datetime
    updated_at: datetime | None = None


class MessageRead(BaseModel):
    id: int
    conversation_id: int
    role: str
    content: str
    result_json: dict | None = None
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)
