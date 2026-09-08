from datetime import datetime
from pydantic import BaseModel, ConfigDict


class ActionRead(BaseModel):
    id: int
    action_type: str
    payload: dict
    status: str
    expires_at: datetime | None
    model_config = ConfigDict(from_attributes=True)

