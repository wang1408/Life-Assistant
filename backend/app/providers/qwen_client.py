from app.core.config import get_settings


class QwenClient:
    """OpenAI-compatible Qwen client with a deterministic local fallback."""

    def __init__(self):
        self.settings = get_settings()

    async def complete(self, prompt: str, smart: bool = False) -> str:
        if not self.settings.qwen_api_key:
            return "我已根据你的请求生成了一个可确认的操作草案。"
        try:
            import httpx
            payload = {"model": self.settings.qwen_smart_model if smart else self.settings.qwen_fast_model, "messages": [{"role": "user", "content": prompt}], "temperature": 0.2}
            headers = {"Authorization": f"Bearer {self.settings.qwen_api_key}"}
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.post(f"{self.settings.qwen_base_url}/chat/completions", json=payload, headers=headers)
                response.raise_for_status()
                return response.json()["choices"][0]["message"]["content"]
        except Exception:
            return "通义千问暂时不可用，已返回本地规则处理结果。"

