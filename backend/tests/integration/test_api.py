import os
os.environ.setdefault("DATABASE_URL", "sqlite:///./test_life_assistant.db")
os.environ["QWEN_API_KEY"] = ""
os.environ["AMAP_API_KEY"] = ""
os.environ["QWEATHER_API_KEY"] = ""
os.environ["REMINDER_LOCAL_RUNNER"] = "false"

from fastapi.testclient import TestClient
from app.main import app


def test_health():
    with TestClient(app) as client:
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"


def test_conversation_retains_messages_and_can_be_deleted():
    with TestClient(app) as client:
        conversation = client.post("/api/v1/conversations", json={}).json()
        conversation_id = conversation["id"]
        response = client.post("/api/v1/chat/stream", json={"conversation_id": conversation_id, "message": "你好"})
        assert response.status_code == 200
        messages = client.get(f"/api/v1/conversations/{conversation_id}/messages").json()
        assert [message["role"] for message in messages] == ["user", "assistant"]
        assert client.delete(f"/api/v1/conversations/{conversation_id}").json()["deleted"] is True
        assert client.get(f"/api/v1/conversations/{conversation_id}/messages").status_code == 404
