from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field


class MemoryUpdate(BaseModel):
    content: str | None = Field(default=None, min_length=1)
    enabled: bool | None = None


class MemoryRead(BaseModel):
    id: int
    category: str
    content: str
    confidence: float
    source: str
    enabled: bool
    last_used_at: datetime | None
    model_config = ConfigDict(from_attributes=True)

