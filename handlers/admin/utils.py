"""
handlers/admin/utils.py
=======================
Admin panel uchun umumiy yordamchi funksiyalar:
  - is_admin() tekshiruvi
  - ReplyKeyboard yaratish
  - InlineKeyboard yaratish
  - FSM States
"""
import logging
from os import getenv

from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (
    ReplyKeyboardMarkup, KeyboardButton,
    InlineKeyboardMarkup, InlineKeyboardButton
)

logger = logging.getLogger(__name__)

# ── Admin IDlarni .env dan olish ─────────────────────────────────────────────
_raw = getenv("ADMIN_IDS", "")
ADMIN_IDS: set[int] = set()
for _a in _raw.split(","):
    _a = _a.strip()
    if _a.isdigit():
        ADMIN_IDS.add(int(_a))
_old = getenv("ADMIN_CHAT_ID", "")
if _old.lstrip("-").isdigit() and int(_old) > 0:
    ADMIN_IDS.add(int(_old))


def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS


# ============================================================================
# FSM STATES
# ============================================================================

class AdminAddKochmas(StatesGroup):
    choosing_region        = State()
    choosing_district      = State()
    choosing_property_type = State()
    entering_full_name     = State()
    entering_phone         = State()
    entering_area          = State()
    entering_rooms         = State()
    entering_floor         = State()
    entering_total_floors  = State()
    entering_price         = State()
    entering_address       = State()
    entering_description   = State()
    uploading_photo        = State()
    uploading_video        = State()
    confirmation           = State()


class AdminAddIjara(StatesGroup):
    choosing_region        = State()
    choosing_district      = State()
    choosing_property_type = State()
    entering_full_name     = State()
    entering_phone         = State()
    entering_area          = State()
    entering_rooms         = State()
    entering_floor         = State()
    entering_total_floors  = State()
    entering_monthly_price = State()
    entering_rental_period = State()
    entering_address       = State()
    entering_description   = State()
    uploading_photo        = State()
    uploading_video        = State()
    confirmation           = State()


class AdminEditKochmas(StatesGroup):
    entering_value = State()


class AdminEditIjara(StatesGroup):
    entering_value = State()


class AdminSearchState(StatesGroup):
    entering_id = State()


class AdminBrowseKochmas(StatesGroup):
    choosing_region        = State()
    choosing_district      = State()
    choosing_property_type = State()


class AdminBrowseIjara(StatesGroup):
    choosing_region        = State()
    choosing_district      = State()
    choosing_property_type = State()


# ============================================================================
# KLAVIATURALAR — Reply
# ============================================================================

def _kb(*rows) -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=t) for t in row] for row in rows],
        resize_keyboard=True
    )


def get_admin_main_menu() -> ReplyKeyboardMarkup:
    return _kb(
        ["🏠 Ko'chmas mulk (Admin)", "📋 Ijara (Admin)"],
        ["🔍 ID orqali qidirish", "📊 Statistika"],
        ["🔙 Asosiy menyuga qaytish"]
    )


def get_admin_kochmas_menu() -> ReplyKeyboardMarkup:
    return _kb(
        ["➕ Ko'chmas mulk qo'shish"],
        ["📋 Barcha Ko'chmas mulk e'lonlar"],
        ["🔍 Filter orqali topish (Ko'chmas)"],
        ["🔙 Admin menyu"]
    )


def get_admin_ijara_menu() -> ReplyKeyboardMarkup:
    return _kb(
        ["➕ Ijara e'loni qo'shish"],
        ["📋 Barcha Ijara e'lonlar"],
        ["🔍 Filter orqali topish (Ijara)"],
        ["🔙 Admin menyu"]
    )


def get_cancel_admin() -> ReplyKeyboardMarkup:
    return _kb(["❌ Bekor qilish"])


def get_skip_cancel_admin() -> ReplyKeyboardMarkup:
    return _kb(["⏭️ O'tkazib yuborish"], ["❌ Bekor qilish"])


def get_confirm_admin() -> ReplyKeyboardMarkup:
    return _kb(["✅ Saqlash"], ["❌ Bekor qilish"])


# ============================================================================
# KLAVIATURALAR — Inline
# ============================================================================

def kochmas_detail_kb(obj_id: int, from_search: bool = False) -> InlineKeyboardMarkup:
    back_cb = "adm_search_back" if from_search else "akl_kochmas"
    back_txt = "🔙 Qidiruvga qaytish" if from_search else "🔙 Ro'yxatga qaytish"
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✏️ Narx",   callback_data=f"ake_kochmas_price_{obj_id}"),
            InlineKeyboardButton(text="✏️ Manzil", callback_data=f"ake_kochmas_address_{obj_id}"),
        ],
        [
            InlineKeyboardButton(text="✏️ Tavsif", callback_data=f"ake_kochmas_description_{obj_id}"),
            InlineKeyboardButton(text="📸 Rasm",   callback_data=f"ake_kochmas_photo_{obj_id}"),
            InlineKeyboardButton(text="🎥 Video",  callback_data=f"ake_kochmas_video_{obj_id}"),
        ],
        [InlineKeyboardButton(text="🗑️ O'chirish", callback_data=f"akd_kochmas_{obj_id}")],
        [InlineKeyboardButton(text=back_txt,        callback_data=back_cb)],
    ])


def ijara_detail_kb(obj_id: int, from_search: bool = False) -> InlineKeyboardMarkup:
    back_cb = "adm_search_back" if from_search else "akl_ijara"
    back_txt = "🔙 Qidiruvga qaytish" if from_search else "🔙 Ro'yxatga qaytish"
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✏️ Oylik narx", callback_data=f"ake_ijara_monthly_price_{obj_id}"),
            InlineKeyboardButton(text="✏️ Manzil",     callback_data=f"ake_ijara_address_{obj_id}"),
        ],
        [
            InlineKeyboardButton(text="✏️ Tavsif",     callback_data=f"ake_ijara_description_{obj_id}"),
            InlineKeyboardButton(text="📸 Rasm",       callback_data=f"ake_ijara_photo_{obj_id}"),
            InlineKeyboardButton(text="🎥 Video",      callback_data=f"ake_ijara_video_{obj_id}"),
        ],
        [InlineKeyboardButton(text="🗑️ O'chirish",     callback_data=f"akd_ijara_{obj_id}")],
        [InlineKeyboardButton(text=back_txt,            callback_data=back_cb)],
    ])


def confirm_delete_kb(obj_type: str, obj_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="✅ Ha, o'chir!", callback_data=f"akdc_{obj_type}_{obj_id}"),
        InlineKeyboardButton(text="❌ Bekor",       callback_data=f"akv_{obj_type}_{obj_id}"),
    ]])


# ============================================================================
# DB YORDAMCHI
# ============================================================================

def db_get_all_kochmas(db, limit: int = 200) -> list:
    try:
        return db.get_all_kochmas(limit=limit)
    except Exception:
        return []


def db_get_all_ijara(db, limit: int = 200) -> list:
    try:
        return db.get_all_ijara(limit=limit)
    except Exception:
        return []


def format_kochmas_text(obj: dict) -> str:
    from utils.constants import format_price, format_area, get_region_name_by_code, get_property_type_name_by_code
    status = "✅ Faol" if obj.get('is_active', 1) else "❌ O'chirilgan"
    text = (
        f"🏠 <b>#{obj['id']} — {get_property_type_name_by_code(obj.get('property_type', ''))}</b>\n"
        f"📌 Holat: {status}\n\n"
        f"🗺️ <b>Viloyat:</b> {get_region_name_by_code(obj.get('region', ''))}\n"
        f"🏘️ <b>Tuman:</b> {obj.get('district') or '—'}\n"
        f"📐 <b>Maydon:</b> {format_area(obj.get('area', 0))}\n"
    )
    if obj.get('rooms'):
        text += f"🚪 <b>Xonalar:</b> {obj['rooms']} ta\n"
    if obj.get('floor'):
        text += f"🏢 <b>Qavat:</b> {obj['floor']}/{obj.get('total_floors', '?')}\n"
    text += f"💰 <b>Narx:</b> {format_price(obj.get('price', 0))}\n"
    text += f"📍 <b>Manzil:</b> {obj.get('address', '—')}\n"
    text += f"👤 <b>Egasi:</b> {obj.get('full_name', '—')} | {obj.get('phone', '—')}\n"
    if obj.get('description'):
        text += f"\n📝 {obj['description'][:200]}\n"
    text += f"\n📅 {obj.get('created_at', '')}"
    return text


def format_ijara_text(obj: dict) -> str:
    from utils.constants import format_price, format_area, get_region_name_by_code, get_property_type_name_by_code
    status = "✅ Faol" if obj.get('is_active', 1) else "❌ O'chirilgan"
    text = (
        f"📋 <b>#{obj['id']} — {get_property_type_name_by_code(obj.get('property_type', ''))} (Ijara)</b>\n"
        f"📌 Holat: {status}\n\n"
        f"🗺️ <b>Viloyat:</b> {get_region_name_by_code(obj.get('region', ''))}\n"
        f"🏘️ <b>Tuman:</b> {obj.get('district') or '—'}\n"
        f"📐 <b>Maydon:</b> {format_area(obj.get('area', 0))}\n"
    )
    if obj.get('rooms'):
        text += f"🚪 <b>Xonalar:</b> {obj['rooms']} ta\n"
    if obj.get('floor'):
        text += f"🏢 <b>Qavat:</b> {obj['floor']}/{obj.get('total_floors', '?')}\n"
    text += f"💰 <b>Oylik:</b> {format_price(obj.get('monthly_price', 0))}/oy\n"
    if obj.get('min_rental_period'):
        text += f"📅 <b>Min. muddat:</b> {obj['min_rental_period']}\n"
    text += f"📍 <b>Manzil:</b> {obj.get('address', '—')}\n"
    text += f"👤 <b>Egasi:</b> {obj.get('full_name', '—')} | {obj.get('phone', '—')}\n"
    if obj.get('description'):
        text += f"\n📝 {obj['description'][:200]}\n"
    text += f"\n📅 {obj.get('created_at', '')}"
    return text