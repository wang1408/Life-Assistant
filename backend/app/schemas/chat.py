from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    message: str = Field(min_length=1)
    conversation_id: int | None = None
    current_location: str | None = None  # longitude,latitude from browser geolocation


class ChatEvent(BaseModel):
    type: str
    content: str | None = None
    data: dict | None = None
