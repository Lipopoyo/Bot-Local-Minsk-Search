import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()
YANDEX_GEOCODER_API_KEY = os.getenv("YANDEX_GEOCODER_API_KEY", "").strip()
YANDEX_STATIC_MAPS_API_KEY = os.getenv("YANDEX_STATIC_MAPS_API_KEY", "").strip()

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN is not set in .env")
if not YANDEX_GEOCODER_API_KEY:
    raise RuntimeError("YANDEX_GEOCODER_API_KEY is not set in .env")
if not YANDEX_STATIC_MAPS_API_KEY:
    raise RuntimeError("YANDEX_STATIC_MAPS_API_KEY is not set in .env")
