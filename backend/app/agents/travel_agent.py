from app.providers.amap_client import AmapClient


async def run(origin: str | None, destination: str | None) -> dict:
    if not origin or not destination:
        return {"available": False, "message": "请提供出发地和目的地，例如：从公司到机场怎么走？"}
    return await AmapClient().route(origin, destination)

