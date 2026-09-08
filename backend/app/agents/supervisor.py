import re


def classify(message: str, current_location: str | None = None, history: list[dict] | None = None) -> dict:
    text = message.lower()
    explicit_origin = _extract_origin(message)
    explicit_destination = _extract_destination(message)
    intents = []
    if any(k in text for k in ("提醒", "待办", "任务", "记得", "完成")):
        intents.append("todo")
    route_request = any(k in text for k in ("路线", "怎么去", "导航", "规划路线", "驾车", "打车", "公交"))
    route_request = route_request or (explicit_origin is not None and explicit_destination is not None)
    route_request = route_request or ("出行" in text and explicit_destination is not None)
    if route_request:
        intents.append("travel")
    advice_request = any(k in text for k in ("出行建议", "出门建议", "出门要带", "带什么", "穿什么", "适合出行", "能不能出门"))
    if advice_request:
        intents.append("advice")
    weather_request = any(k in text for k in ("天气", "下雨", "温度", "带伞"))
    weather_request = weather_request or ("出门" in text and not advice_request)
    if weather_request:
        intents.append("weather")
    if any(k in text for k in ("记住", "习惯", "偏好", "通常")):
        intents.append("memory")
    if not intents:
        intents = ["general"]
    origin = explicit_origin
    if not origin and any(k in message for k in ("我所在地", "当前位置", "当前地点")):
        origin = current_location or "我所在地"
    # If the user has granted browser location and only says “去机场/去某地”,
    # use the current coordinates as the implicit origin.
    if not origin and "travel" in intents and current_location:
        origin = current_location
    destination = explicit_destination
    # 天气查询没有明确城市时，优先使用用户已授权的当前位置。
    if not destination and ("weather" in intents or "advice" in intents) and "travel" not in intents and current_location:
        destination = current_location
    context_reference = any(k in text for k in ("那边", "那里", "刚才", "上面", "目的地", "该地", "这个地方"))
    if not destination and history and context_reference and any(k in intents for k in ("travel", "weather", "advice")):
        destination = _history_destination(history)
    return {"intents": intents, "origin": origin, "destination": destination}


def _history_destination(history: list[dict]) -> str | None:
    """从最近一次路线/天气结果或用户请求中补全省略的地点。"""
    for item in reversed(history):
        results = item.get("results") or {}
        weather = results.get("weather") if isinstance(results, dict) else None
        travel = results.get("travel") if isinstance(results, dict) else None
        if isinstance(weather, dict) and weather.get("location"):
            return str(weather["location"])
        if isinstance(travel, dict) and travel.get("destination"):
            return str(travel["destination"])
        if item.get("role") == "user":
            destination = _extract_destination(str(item.get("content") or ""))
            if destination:
                return destination
    return None


def _extract_after(text: str, marker: str) -> str | None:
    match = re.search(rf"{marker}([^，。；,; ]+)", text)
    return match.group(1) if match else None


def _extract_origin(text: str) -> str | None:
    match = re.search(r"从(.+?)到", text)
    return match.group(1).strip() if match else None


def _extract_destination(text: str) -> str | None:
    match = re.search(r"(?:到|去)(.+?)(?:(?:的)?(?:路线|天气|怎么走|导航|出行)|[，。；,;？?]|$)", text)
    if match:
        return match.group(1).strip()
    return _extract_after(text, "到")
