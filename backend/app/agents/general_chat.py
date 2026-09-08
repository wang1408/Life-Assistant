import json
from app.core.config import get_settings
from app.providers.qwen_client import QwenClient


def _safe_result_context(result: dict) -> dict:
    """只保留回答后续问题所需的事实，避免把带 Key 的地图 URL 送进模型。"""
    safe: dict = {}
    travel = result.get("travel")
    if isinstance(travel, dict):
        safe["travel"] = {
            key: travel.get(key)
            for key in ("available", "message", "origin", "destination", "distance", "duration", "mode")
            if travel.get(key) is not None
        }
    weather = result.get("weather")
    if isinstance(weather, dict):
        safe["weather"] = {
            key: weather.get(key)
            for key in ("available", "message", "location", "location_id", "now", "update_time")
            if weather.get(key) is not None
        }
    advice = result.get("advice")
    if isinstance(advice, dict) and advice.get("text"):
        safe["advice"] = {"text": str(advice["text"])[:1200]}
    return safe


def _history_context(history: list[dict] | None) -> str:
    if not history:
        return "暂无此前对话"
    lines = []
    for item in history[-8:]:
        role = "用户" if item.get("role") == "user" else "助手"
        content = str(item.get("content") or "").strip()
        if not content:
            continue
        result = item.get("results")
        if result:
            # 结构化结果是路线/天气卡片的事实来源，也要提供给下一轮模型。
            content += f"\n结构化结果：{json.dumps(_safe_result_context(result), ensure_ascii=False, default=str)[:1800]}"
        lines.append(f"{role}：{content[:2000]}")
    return "\n".join(lines) or "暂无此前对话"


async def respond(message: str, memories: list[str] | None = None, history: list[dict] | None = None) -> str:
    settings = get_settings()
    if not settings.qwen_api_key:
        return "我可以陪你聊天，也可以在你需要时帮你安排待办、查询天气或规划路线。"
    memory_context = "；".join(memories or []) or "暂无已保存偏好"
    prompt = f"""你是一个自然、可靠的中文生活助手。当前用户没有触发待办、路线、天气或记忆工具，请像普通聊天模型一样直接回答，不要主动创建任务，不要声称调用了外部服务。
你必须结合下面的此前对话回答当前问题；如果此前对话中有路线或天气结果，应把它们当作已知事实，而不是要求用户重新提供。
此前对话：
{_history_context(history)}
用户已确认的偏好：{memory_context}
当前用户消息：{message}
请用简洁、友好的中文回答。"""
    return await QwenClient().complete(prompt, smart=True)
