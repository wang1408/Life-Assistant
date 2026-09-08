from pydantic import BaseModel


class DashboardRead(BaseModel):
    todos: list[dict]
    memories: list[dict]
    pending_actions: list[dict]

