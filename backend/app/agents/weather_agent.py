from app.providers.qweather_client import QWeatherClient


async def run(location: str | None) -> dict:
    if not location:
        return {
            "provider": "qweather",
            "available": False,
            "message": "请提供城市，或先点击“定位”查询当前位置天气",
        }
    return await QWeatherClient().now(location)
