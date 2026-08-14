import aiohttp
from config import YANDEX_STATIC_MAPS_API_KEY

STATIC_MAP_URL = "https://static-maps.yandex.ru/v1"

class StaticMapError(Exception):
    pass

async def get_map(lat: float, lon: float, output_path: str) -> str:
    params = {
        "apikey": YANDEX_STATIC_MAPS_API_KEY,
        "ll": f"{lon:.6f},{lat:.6f}",
        "z": "15",
        "size": "650,450",
        "lang": "ru_RU",
        "theme": "dark",
        "type": "map",
    }

    timeout = aiohttp.ClientTimeout(total=20)

    try:
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(STATIC_MAP_URL, params=params) as response:
                if response.status in (401, 403):
                    raise StaticMapError("Yandex Static Maps API key is invalid, inactive or has no access.")
                if response.status == 429:
                    raise StaticMapError("Yandex Static Maps API rate limit reached.")
                response.raise_for_status()
                content = await response.read()
    except aiohttp.ClientError as exc:
        raise StaticMapError("Could not connect to Yandex Static Maps.") from exc

    if not content.startswith(b"\x89PNG") and not content.startswith(b"\xff\xd8"):
        raise StaticMapError("Yandex did not return an image.")

    with open(output_path, "wb") as f:
        f.write(content)

    return output_path
