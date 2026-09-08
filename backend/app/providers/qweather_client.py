from urllib.parse import urlparse

from app.core.config import get_settings


def _normalize_api_host(value: str) -> str:
    """将控制台中的 API Host 统一为 HTTPS 根地址。"""
    candidate = (value or "").strip()
    if not candidate:
        return ""
    parsed = urlparse(candidate if "://" in candidate else f"https://{candidate}")
    if parsed.scheme != "https" or not parsed.netloc:
        return ""
    return f"https://{parsed.netloc}"


def _response_error(response) -> str:
    """提取和风错误码，但不把响应中的敏感请求信息透传给前端。"""
    status = f"HTTP {response.status_code}"
    try:
        payload = response.json()
    except Exception:
        return status
    error = payload.get("error") if isinstance(payload, dict) else None
    if isinstance(error, dict):
        code = error.get("status") or error.get("code")
        detail = error.get("title") or error.get("detail")
    else:
        code = payload.get("code") if isinstance(payload, dict) else None
        detail = payload.get("message") if isinstance(payload, dict) else None
    parts = [status]
    if code:
        parts.append(str(code))
    if detail:
        parts.append(str(detail))
    return "，".join(parts)


def _normalize_location(value: str | None) -> str | None:
    """和风天气坐标最多支持两位小数，浏览器坐标需要先规整。"""
    if not value:
        return value
    parts = value.split(",")
    if len(parts) != 2:
        return value
    try:
        return f"{float(parts[0]):.2f},{float(parts[1]):.2f}"
    except ValueError:
        return value


def _is_coordinate(value: str | None) -> bool:
    if not value:
        return False
    parts = value.split(",")
    if len(parts) != 2:
        return False
    try:
        float(parts[0])
        float(parts[1])
        return True
    except ValueError:
        return False


class QWeatherClient:
    async def now(self, location: str) -> dict:
        settings = get_settings()
        if not settings.qweather_api_key:
            return {"provider": "qweather", "available": False, "message": "未配置和风天气 API Key", "location": location}
        api_host = _normalize_api_host(settings.qweather_api_host)
        if not api_host:
            return {
                "provider": "qweather",
                "available": False,
                "message": "未配置和风天气项目 API Host，请在 .env 设置 QWEATHER_API_HOST",
                "location": location,
            }
        try:
            import httpx
            headers = {"X-QW-Api-Key": settings.qweather_api_key}
            async with httpx.AsyncClient(timeout=15) as client:
                display_location = "当前位置" if _is_coordinate(location) else location
                location_id = _normalize_location(location)
                if location and any("\u4e00" <= char <= "\u9fff" for char in location) and "," not in location:
                    lookup = await client.get(f"{api_host}/geo/v2/city/lookup", params={"location": location, "number": 1}, headers=headers)
                    if lookup.status_code >= 400:
                        return {"provider": "qweather", "available": False, "message": f"和风天气地点查询失败（{_response_error(lookup)}），请检查 API Key、项目 API Host 和权限", "location": display_location}
                    locations = lookup.json().get("location") or []
                    if not locations:
                        return {"provider": "qweather", "available": False, "message": f"未找到天气地点：{location}", "location": display_location}
                    location_id = locations[0].get("id") or location
                response = await client.get(f"{api_host}/v7/weather/now", params={"location": location_id}, headers=headers)
                if response.status_code >= 400:
                    return {"provider": "qweather", "available": False, "message": f"和风天气查询失败（{_response_error(response)}），请检查 API Key、项目 API Host 和权限", "location": display_location}
                data = response.json()
                return {"provider": "qweather", "available": data.get("code") == "200", "location": display_location, "location_id": location_id, "now": data.get("now"), "update_time": data.get("updateTime")}
        except Exception as exc:
            return {"provider": "qweather", "available": False, "message": "和风天气服务暂时不可用，请稍后重试", "location": location}
