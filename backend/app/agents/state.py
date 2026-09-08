from typing import Any, TypedDict


class AssistantState(TypedDict, total=False):
    message: str
    # 当前会话中最近的消息，包含 assistant 的路线/天气结构化结果。
    history: list[dict[str, Any]]
    current_location: str | None
    intent: dict[str, Any]
    memories: list[str]
    results: dict[str, Any]
    actions: list[dict[str, Any]]
    response: str
    specialist_results: dict[str, Any]
    candidates: list[dict[str, Any]]
