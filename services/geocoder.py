import aiohttp
from utils.aliases import expand_alias
from config import YANDEX_GEOCODER_API_KEY

GEOCODER_URL = "https://geocode-maps.yandex.ru/v1/"

class GeocodingError(Exception):
    pass

async def geocode(query: str) -> dict | None:
    query = expand_alias(query)

    if "минск" not in query.lower():
        query = f"{query}, Минск"

    params = {
        "apikey": YANDEX_GEOCODER_API_KEY,
        "geocode": query,
        "lang": "ru_RU",
        "format": "json",
        "results": 1,
    }

    timeout = aiohttp.ClientTimeout(total=15)

    try:
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(GEOCODER_URL, params=params) as response:
                if response.status in (401, 403):
                    raise GeocodingError("Yandex Geocoder API key is invalid or not activated.")
                if response.status == 429:
                    raise GeocodingError("Yandex Geocoder API rate limit reached.")
                response.raise_for_status()
                data = await response.json()
    except aiohttp.ClientError as exc:
        raise GeocodingError("Could not connect to Yandex Geocoder.") from exc

    members = (
        data.get("response", {})
            .get("GeoObjectCollection", {})
            .get("featureMember", [])
    )

    if not members:
        return None

    geo = members[0].get("GeoObject", {})
    pos = geo.get("Point", {}).get("pos", "").split()

    if len(pos) != 2:
        raise GeocodingError("Yandex returned an invalid coordinate format.")

    lon, lat = map(float, pos)

    if not (53.7 <= lat <= 54.1 and 27.2 <= lon <= 27.8):
        return None

    return {
        "lat": lat,
        "lon": lon,
        "name": geo.get("name") or query,
        "description": geo.get("description") or "Минск, Беларусь",
    }
