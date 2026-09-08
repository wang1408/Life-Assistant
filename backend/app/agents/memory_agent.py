def extract_candidates(message: str) -> list[dict]:
    if not any(k in message for k in ("记住", "我喜欢", "我通常", "我的习惯")):
        return []
    content = message.replace("请记住", "").replace("记住", "").strip(" ：:，,。")
    return [{"category": "preference", "content": content, "confidence": 0.75, "source": "conversation"}] if content else []

