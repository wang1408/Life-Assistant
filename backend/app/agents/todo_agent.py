from app.services.todo_service import parse_natural_datetime


def build_todo_action(message: str) -> dict | None:
    if not any(k in message for k in ("提醒", "待办", "任务", "记得")):
        return None
    title = message.strip()
    parsed_time = parse_natural_datetime(message)
    remind_at = None
    if parsed_time:
        remind_at = parsed_time.isoformat()
    return {"action_type": "create_todo", "payload": {"title": title, "remind_at": remind_at, "due_at": remind_at, "priority": 2}, "label": f"创建待办：{title}"}
