import asyncio
from typing import Any
from app.agents.state import AssistantState
from app.agents.supervisor import classify
from app.agents.todo_agent import build_todo_action
from app.agents.travel_agent import run as run_travel
from app.agents.weather_agent import run as run_weather
from app.agents.memory_agent import extract_candidates
from app.providers.qwen_client import QwenClient
from app.core.config import get_settings
from app.agents.general_chat import respond as respond_general


def _local_outdoor_advice(weather: dict[str, Any]) -> str:
    now = weather.get("now") or {}
    text = str(now.get("text") or "")
    tips: list[str] = []
    try:
        temperature = float(now.get("temp"))
    except (TypeError, ValueError):
        temperature = None
    try:
        precipitation = float(now.get("precip") or 0)
    except (TypeError, ValueError):
        precipitation = 0
    try:
        wind_scale = float(now.get("windScale") or 0)
    except (TypeError, ValueError):
        wind_scale = 0
    if precipitation > 0 or any(word in text for word in ("雨", "雪", "雷")):
        tips.append("建议带伞并优先选择有遮挡的路线")
    if temperature is not None and temperature >= 30:
        tips.append("天气偏热，建议穿轻薄透气衣物并注意补水")
    elif temperature is not None and temperature <= 10:
        tips.append("天气偏冷，建议增加保暖衣物")
    if wind_scale >= 5:
        tips.append("风力较大，户外活动注意防风")
    if not tips:
        tips.append("当前天气总体适合正常出行")
    return "；".join(tips) + "。"


async def _generate_outdoor_advice(message: str, weather: dict[str, Any]) -> str:
    if not weather.get("available") or not weather.get("now"):
        return "暂时无法获取可靠的实时天气，因此无法给出准确的出行建议。请检查天气配置或稍后重试。"
    now = weather.get("now") or {}
    location = weather.get("location") or "当前位置"
    if not get_settings().qwen_api_key:
        return _local_outdoor_advice(weather)
    prompt = f"""你是生活助手的出行建议 Agent。用户请求：{message}
请根据下面的实时天气，为用户给出简洁、可执行的出行建议。不要只复述天气数据，也不要编造未来预报；重点回答是否适合出行、穿衣、雨具、补水和交通注意事项。用 2-4 条中文建议直接回答。
地点：{location}
实时天气：温度 {now.get('temp', '未知')}℃，体感 {now.get('feelsLike', '未知')}℃，{now.get('text', '未知')}，降水 {now.get('precip', '未知')} mm，风力 {now.get('windScale', '未知')} 级，湿度 {now.get('humidity', '未知')}%。"""
    return await QwenClient().complete(prompt, smart=True)


async def _specialist_step(message: str, intent: dict) -> tuple[dict[str, Any], list[dict[str, Any]], list[dict[str, Any]]]:
    results: dict[str, Any] = {}
    actions: list[dict[str, Any]] = []
    tasks = []
    if "travel" in intent["intents"]:
        tasks.append(("travel", run_travel(intent.get("origin"), intent.get("destination"))))
    if "weather" in intent["intents"] or "advice" in intent["intents"]:
        tasks.append(("weather", run_weather(intent.get("destination"))))
    if tasks:
        values = await asyncio.gather(*(task for _, task in tasks))
        results.update({name: value for (name, _), value in zip(tasks, values)})
    if "advice" in intent["intents"]:
        results["advice"] = {"text": await _generate_outdoor_advice(message, results.get("weather", {}))}
    action = build_todo_action(message)
    if action:
        actions.append(action)
    candidates = extract_candidates(message)
    if candidates:
        results["memory_candidates"] = candidates
    return results, actions, candidates


def _synthesize(message: str, intent: dict, results: dict[str, Any], actions: list[dict[str, Any]], candidates: list[dict[str, Any]]) -> str:
    if "advice" in intent["intents"]:
        advice = (results.get("advice") or {}).get("text") or "暂时无法生成出行建议。"
        pieces = [advice]
        if actions:
            pieces.append("待办已生成草案，请确认后创建。")
        if candidates:
            pieces.append("发现一个可保存的习惯偏好，可在记忆页管理。")
        return "\n".join(pieces)
    pieces = ["我理解你的需求了。"]
    if actions:
        pieces.append("待办已生成草案，请确认后创建。")
    if "travel" in results:
        pieces.append(f"路线结果：{results['travel'].get('message') or results['travel'].get('duration') or '已返回路线信息'}")
    if "weather" in results:
        pieces.append(f"天气结果：{results['weather'].get('message') or results['weather'].get('now') or '已返回天气信息'}")
    if candidates:
        pieces.append("发现一个可保存的习惯偏好，可在记忆页管理。")
    if intent["intents"] == ["general"]:
        pieces.append("你可以让我创建待办、查天气、规划路线，或记住你的偏好。")
    return "\n".join(pieces)


async def run_assistant(message: str, memories: list[str] | None = None, current_location: str | None = None, history: list[dict[str, Any]] | None = None) -> AssistantState:
    intent = classify(message, current_location, history)
    results, actions, candidates = await _specialist_step(message, intent)
    if intent["intents"] == ["general"]:
        response = await respond_general(message, memories, history)
    else:
        response = _synthesize(message, intent, results, actions, candidates)
    if intent["intents"] != ["general"] and "advice" not in intent["intents"] and get_settings().qwen_api_key:
        response = await QwenClient().complete(f"请润色以下生活助手答复，保持事实和待确认要求不变：\n{response}", smart=True)
    return {"message": message, "current_location": current_location, "intent": intent, "memories": memories or [], "results": results, "actions": actions, "candidates": candidates, "response": response}


def build_graph():
    """Return a LangGraph graph when installed, with a compatible local fallback."""
    try:
        from langgraph.graph import END, START, StateGraph
        graph = StateGraph(AssistantState)
        async def load_context(state: AssistantState):
            return {"memories": state.get("memories", []), "history": state.get("history", [])}
        async def supervisor_node(state: AssistantState):
            return {"intent": classify(state["message"], state.get("current_location"), state.get("history"))}
        async def specialist_node(state: AssistantState):
            results, actions, candidates = await _specialist_step(state["message"], state["intent"])
            return {"specialist_results": results, "actions": actions, "candidates": candidates, "results": results}
        async def synthesize_node(state: AssistantState):
            if state["intent"]["intents"] == ["general"]:
                response = await respond_general(state["message"], state.get("memories", []), state.get("history", []))
            else:
                response = _synthesize(state["message"], state["intent"], state.get("specialist_results", {}), state.get("actions", []), state.get("candidates", []))
            if state["intent"]["intents"] != ["general"] and "advice" not in state["intent"]["intents"] and get_settings().qwen_api_key:
                response = await QwenClient().complete(f"请润色以下生活助手答复，保持事实和待确认要求不变：\n{response}", smart=True)
            return {"response": response}
        graph.add_node("load_context", load_context)
        graph.add_node("supervisor", supervisor_node)
        graph.add_node("specialists", specialist_node)
        graph.add_node("synthesize", synthesize_node)
        graph.add_edge(START, "load_context")
        graph.add_edge("load_context", "supervisor")
        graph.add_edge("supervisor", "specialists")
        graph.add_edge("specialists", "synthesize")
        graph.add_edge("synthesize", END)
        return graph.compile()
    except ImportError:
        class LocalGraph:
            async def ainvoke(self, state):
                return await run_assistant(state["message"], state.get("memories"), state.get("current_location"), state.get("history"))
        return LocalGraph()
