from pathlib import Path
import tempfile

from aiogram import Router, F
from aiogram.filters import CommandStart, Command
from aiogram.types import (
    Message,
    FSInputFile,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    ReplyKeyboardMarkup,
    KeyboardButton,
)
from aiogram.utils.keyboard import InlineKeyboardBuilder

from services.geocoder import geocode, GeocodingError
from services.maps import get_map, StaticMapError
from services.image_generator import make_card
from utils.aliases import ALIASES


router = Router()

# MAIN MENU
def main_menu_text() -> str:
    return (
        "🌐 <b>LOCAL MINSK SEARCH</b>\n\n"
        "Найди любое место в Минске — "
        "я превращу его в фирменную карту.\n\n"
        "Можно отправить:\n"
        "• название — <i>Немига</i>\n"
        "• адрес — <i>Независимости, 20</i>\n"
        "• координаты — <i>53.9027, 27.5619</i>\n"
        "• местный сленг — <i>Зыба и т.д.</i>\n"
        "• свою геолокацию\n\n"
        "Выбирай действие 👇"
    )

def main_menu() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    builder.row(
        InlineKeyboardButton(
            text="🔎 Найти место",
            callback_data="search",
        )
    )

    builder.row(
        InlineKeyboardButton(
            text="📍 Моя геолокация",
            callback_data="location",
        ),
        InlineKeyboardButton(
            text="Сленг Минска",
            callback_data="slang",
        ),
    )

    builder.row(
        InlineKeyboardButton(
            text="ℹ️ Как пользоваться",
            callback_data="help",
        )
    )

    return builder.as_markup()


def back_button() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="◀️ Назад",
                    callback_data="menu",
                )
            ]
        ]
    )

# LOCATION BUTTON
def location_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(
                    text="📍 Отправить геолокацию",
                    request_location=True,
                )
            ]
        ],
        resize_keyboard=True,
        one_time_keyboard=True,
        input_field_placeholder="Отправь свою геолокацию",
    )

# START
@router.message(CommandStart())
async def start(message: Message):

    await message.answer(
        main_menu_text(),
        parse_mode="HTML",
        reply_markup=main_menu(),
    )


# CALLBACKS
@router.callback_query(F.data == "menu")
async def menu_callback(callback):

    await callback.message.edit_text(
        main_menu_text(),
        parse_mode="HTML",
        reply_markup=main_menu(),
    )

    await callback.answer()


@router.callback_query(F.data == "search")
async def search_callback(callback):

    await callback.message.edit_text(
        "🔎 <b>ПОИСК МЕСТА</b>\n\n"
        "Отправь мне:\n\n"
        "📍 название\n"
        "🏠 адрес\n"
        "🧭 координаты\n"
        "🔥 сленговое название\n\n",
        parse_mode="HTML",
        reply_markup=back_button(),
    )

    await callback.answer()


@router.callback_query(F.data == "location")
async def location_callback(callback):

    await callback.message.answer(
        "📍 <b>ОТПРАВЬ СВОЮ ГЕОЛОКАЦИЮ</b>\n\n"
        "Telegram передаст координаты, "
        "и я сразу построю карту.",
        parse_mode="HTML",
        reply_markup=location_keyboard(),
    )

    await callback.answer()


@router.callback_query(F.data == "help")
async def help_callback(callback):

    await callback.message.edit_text(
        "ℹ️ <b>КАК ЭТО РАБОТАЕТ</b>\n\n"
        "1️⃣ Ты отправляешь место.\n"
        "2️⃣ Я определяю координаты.\n"
        "3️⃣ Нахожу точку на карте Минска.\n"
        "4️⃣ Собираю cyber-map.\n"
        "5️⃣ Отправляю её тебе.\n\n"
        "<b>Поддерживаются:</b>\n"
        "• адреса\n"
        "• названия\n"
        "• координаты\n"
        "• Telegram Location\n"
        "• сленговые названия Минска\n\n"
        "🔥 Попробуй написать!",
        parse_mode="HTML",
        reply_markup=back_button(),
    )

    await callback.answer()


@router.callback_query(F.data == "slang")
async def slang_callback(callback):

    text = (
        "<b>МИНСКИЙ СЛЕНГ</b>\n\n"
        "Я понимаю не только официальные адреса.\n"
        "Попробуй написать, например:\n\n"
        "• <b>Зыба</b> → Зыбицкая\n"
        "• <b>Каменка</b> → Каменная горка\n"
        "• <b>Курасы</b> → Курасовщина\n"
        "И это далеко не всё 👀"
    )

    await callback.message.edit_text(
        text,
        parse_mode="HTML",
        reply_markup=back_button(),
    )

    await callback.answer()

# HELP
@router.message(Command("help"))
async def help_command(message: Message):

    await message.answer(
        "ℹ️ <b>LOCAL MINSK SEARCH</b>\n\n"
        "Просто отправь название места, адрес, "
        "координаты или геолокацию.",
        parse_mode="HTML",
        reply_markup=main_menu(),
    )

# TELEGRAM LOCATION
@router.message(F.location)
async def location(message: Message):

    loc = message.location

    if not is_minsk(loc.latitude, loc.longitude):
        await message.answer(
            "📍 Эта точка находится за пределами Минска."
        )
        return

    await build_card(
        message,
        loc.latitude,
        loc.longitude,
        "Точка на карте",
    )

# TEXT SEARCH
@router.message(F.text)
async def text_query(message: Message):

    query = message.text.strip()

    if query == "📍 Отправить геолокацию":
        await message.answer(
            "Нажми кнопку ещё раз и разреши Telegram "
            "передать геолокацию."
        )
        return

    # COORDINATES
    coords = parse_coordinates(query)

    if coords:

        lat, lon = coords

        if not is_minsk(lat, lon):
            await message.answer(
                "📍 Эта точка находится за пределами Минска."
            )
            return

        await build_card(
            message,
            lat,
            lon,
            "Точка на карте",
        )

        return

    # GEOCODING
    await message.bot.send_chat_action(
        chat_id=message.chat.id,
        action="upload_photo",
    )

    try:

        result = await geocode(query)

    except GeocodingError as exc:

        await message.answer(
            "⚠️ <b>Не удалось найти место.</b>\n\n"
            f"{exc}\n\n"
            "Попробуй написать адрес подробнее.",
            parse_mode="HTML",
        )

        return

    # NOT FOUND
    if not result:

        await message.answer(
            "🔎 <b>Ничего не нашёл.</b>\n\n"
            "Попробуй:\n"
            "• написать полный адрес\n"
            "• использовать другое название\n"
            "• отправить координаты\n"
            "• отправить геолокацию",
            parse_mode="HTML",
        )

        return

    # BUILD MAP
    await build_card(
        message,
        result["lat"],
        result["lon"],
        result["name"],
    )


# COORDINATES PARSER
def parse_coordinates(text: str):

    try:

        cleaned = (
            text
            .replace(";", ",")
            .replace(" ", ",", 1)
            if text.count(",") == 0
            else text
        )

        parts = [
            part.strip()
            for part in cleaned.split(",")
        ]

        if len(parts) != 2:
            return None

        lat = float(parts[0])
        lon = float(parts[1])

        return lat, lon

    except (ValueError, TypeError):

        return None


# MINSK BOUNDS
def is_minsk(lat: float, lon: float) -> bool:

    return (
        53.7 <= lat <= 54.1
        and
        27.2 <= lon <= 27.8
    )


# CARD GENERATION
async def build_card(
    message: Message,
    lat: float,
    lon: float,
    name: str,
):

    with tempfile.TemporaryDirectory() as tmp:

        map_path = str(
            Path(tmp) / "map.png"
        )

        card_path = str(
            Path(tmp) / "local_minsk_search.jpg"
        )

        status_message = await message.answer(
            "📡 <b>Ищу точку…</b>",
            parse_mode="HTML",
        )

        try:

            await get_map(
                lat,
                lon,
                map_path,
            )

            await status_message.edit_text(
                "⚡ <b>Собираю карту…</b>",
                parse_mode="HTML",
            )

            make_card(
                map_path,
                name,
                lat,
                lon,
                card_path,
            )

        except StaticMapError as exc:

            await status_message.edit_text(
                "⚠️ <b>Не удалось получить карту.</b>\n\n"
                f"{exc}\n\n"
                "Проверь Static Maps API key.",
                parse_mode="HTML",
            )

            return

        except Exception as exc:

            await status_message.edit_text(
                "⚠️ <b>Ошибка генерации.</b>\n\n"
                f"<code>{type(exc).__name__}</code>",
                parse_mode="HTML",
            )

            return

        await status_message.delete()

        await message.answer_photo(
            photo=FSInputFile(card_path),
            caption=(
                f"📍 <b>{name}</b>\n"
                f"LOCAL MINSK SEARCH"
            ),
            parse_mode="HTML",
        )