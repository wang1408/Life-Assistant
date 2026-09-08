from fastapi import APIRouter
from app.api.v1 import chat, todos, actions, memories, dashboard, conversations

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(chat.router, tags=["chat"])
api_router.include_router(todos.router, prefix="/todos", tags=["todos"])
api_router.include_router(actions.router, prefix="/actions", tags=["actions"])
api_router.include_router(memories.router, prefix="/memories", tags=["memories"])
api_router.include_router(dashboard.router, prefix="/dashboard", tags=["dashboard"])
api_router.include_router(conversations.router, prefix="/conversations", tags=["conversations"])
