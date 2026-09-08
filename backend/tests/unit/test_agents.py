import asyncio
from types import SimpleNamespace

from app.agents.supervisor import classify
from app.agents.todo_agent import build_todo_action
from app.agents.graph import run_assistant
from app.services.todo_service import parse_natural_datetime


def test_classify_compound_request():
    result = classify("明天从公司到机场怎么走，提醒我带伞")
    assert "travel" in result["intents"]
    assert "todo" in result["intents"]


def test_todo_action_requires_confirmation():
    action = build_todo_action("明天 08:00 提醒我带伞")
    assert action["action_type"] == "create_todo"
    assert action["payload"]["remind_at"]


def test_todo_action_parses_relative_minutes():
    action = build_todo_action("十分钟后提醒我去取快递")
    assert action["payload"]["remind_at"]
    assert parse_natural_datetime("十分钟后提醒我去取快递")


def test_todo_action_parses_chinese_morning_time():
    action = build_todo_action("明天早上9点提醒我开会")
    assert action["payload"]["remind_at"]


def test_graph_returns_action_and_results_without_keys():
    result = asyncio.run(run_assistant("查询从公司到机场的路线和天气，并提醒我带伞"))
    assert result["actions"]
    assert "travel" in result["results"]
    assert "weather" in result["results"]


def test_general_chat_has_normal_fallback_without_task():
    result = asyncio.run(run_assistant("你觉得周末适合做什么？"))
    assert result["intent"]["intents"] == ["general"]
    assert result["actions"] == []
    assert result["response"]


def test_followup_reuses_previous_destination():
    history = [{"role": "user", "content": "明天去重庆，规划路线并查询天气", "results": None}]
    result = classify("那边天气怎么样？", history=history)
    assert result["intents"] == ["weather"]
    assert result["destination"] == "重庆"


def test_weather_without_city_uses_current_location():
    result = classify("当前地的天气状况", current_location="116.397128,39.916527")
    assert result["intents"] == ["weather"]
    assert result["destination"] == "116.397128,39.916527"


def test_outdoor_advice_does_not_invent_route_destination():
    result = classify("如果我现在要出门的话有什么出行建议吗", current_location="116.397128,39.916527")
    assert result["intents"] == ["advice"]
    assert result["destination"] == "116.397128,39.916527"


def test_general_chat_prompt_contains_previous_structured_results(monkeypatch):
    import app.agents.general_chat as general_chat

    captured = []
    monkeypatch.setattr(general_chat, "get_settings", lambda: SimpleNamespace(qwen_api_key="configured"))

    async def fake_complete(self, prompt, smart=False):
        captured.append(prompt)
        return "ok"

    monkeypatch.setattr(general_chat.QwenClient, "complete", fake_complete)
    response = asyncio.run(general_chat.respond(
        "你觉得明天带什么？",
        history=[{
            "role": "assistant",
            "content": "路线和天气已查好",
            "results": {
                "travel": {"destination": "重庆", "map_url": "https://example.test/staticmap?key=secret"},
                "weather": {"location": "重庆", "now": {"text": "多云", "temp": "34"}},
            },
        }],
    ))
    assert response == "ok"
    assert "重庆" in captured[0]
    assert "多云" in captured[0]
    assert "secret" not in captured[0]
