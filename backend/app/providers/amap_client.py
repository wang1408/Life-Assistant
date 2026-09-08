from app.core.config import get_settings
from urllib.parse import urlencode


class AmapClient:
    async def geocode(self, address: str) -> dict | None:
        settings = get_settings()
        if not address or not settings.amap_api_key:
            return None
        try:
            import httpx
            async with httpx.AsyncClient(timeout=15) as client:
                response = await client.get("https://restapi.amap.com/v3/geocode/geo", params={"key": settings.amap_api_key, "address": address})
                response.raise_for_status()
                data = response.json()
                geocode = (data.get("geocodes") or [{}])[0]
                return {"location": geocode.get("location"), "formatted_address": geocode.get("formatted_address") or address}
        except Exception:
            return None

    async def route(self, origin: str, destination: str, mode: str = "driving") -> dict:
        settings = get_settings()
        if not settings.amap_api_key:
            return {"provider": "amap", "available": False, "message": "未配置高德 API Key", "origin": origin, "destination": destination, "mode": mode}
        try:
            import httpx
            origin_geo = {"location": origin} if _is_coordinate(origin) else await self.geocode(origin)
            destination_geo = {"location": destination} if _is_coordinate(destination) else await self.geocode(destination)
            if not origin_geo or not origin_geo.get("location") or not destination_geo or not destination_geo.get("location"):
                return {"provider": "amap", "available": False, "message": "无法将出发地或目的地解析为地图坐标，请输入城市或具体地址", "origin": origin, "destination": destination, "mode": mode}
            origin_coord = origin_geo["location"]
            destination_coord = destination_geo["location"]
            url = "https://restapi.amap.com/v3/direction/driving"
            params = {"key": settings.amap_api_key, "origin": origin_coord, "destination": destination_coord, "extensions": "all"}
            async with httpx.AsyncClient(timeout=15) as client:
                response = await client.get(url, params=params)
                data = response.json()
                if response.status_code >= 400 or data.get("status") != "1":
                    return {"provider": "amap", "available": False, "message": "高德路线请求失败，请检查 Web 服务 Key 是否有效，以及出发地/目的地是否明确", "origin": origin, "destination": destination, "mode": mode}
                path = (data.get("route", {}).get("paths") or [{}])[0]
                available = data.get("status") == "1" and bool(path.get("distance"))
                static_params = {"key": settings.amap_api_key, "location": destination_coord, "zoom": 11, "size": "750*360", "markers": f"mid,0x2563EB,A:{origin_coord}|mid,0xF97316,B:{destination_coord}"}
                if path.get("polyline"):
                    static_params["paths"] = f"6,0x2563EB,1,,::{path['polyline']}"
                return {"provider": "amap", "available": available, "distance": path.get("distance"), "duration": path.get("duration"), "origin": origin_geo.get("formatted_address", origin), "destination": destination_geo.get("formatted_address", destination), "origin_location": origin_coord, "destination_location": destination_coord, "mode": mode, "map_url": "https://restapi.amap.com/v3/staticmap?" + urlencode(static_params), "navigation_url": "https://uri.amap.com/navigation?from=" + origin_coord + "&to=" + destination_coord + "&mode=car&coordinate=gaode"}
        except Exception as exc:
            return {"provider": "amap", "available": False, "message": "高德地图服务暂时不可用，请稍后重试", "origin": origin, "destination": destination, "mode": mode}


def _is_coordinate(value: str | None) -> bool:
    if not value:
        return False
    parts = value.split(",")
    if len(parts) != 2:
        return False
    try:
        float(parts[0]); float(parts[1]); return True
    except ValueError:
        return False
