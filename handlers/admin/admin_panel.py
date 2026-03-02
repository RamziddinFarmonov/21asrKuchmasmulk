"""
Admin Panel - Ko'chmas Mulk va Ijara
=======================================
IMKONIYATLAR:
  Ko'chmas mulk:
    - Barcha e'lonlarni ko'rish
    - Yangi e'lon qo'shish
    - E'lonni tahrirlash (narx, manzil, tavsif, rasm, video)
    - E'lonni o'chirish

  Ijara:
    - Barcha e'lonlarni ko'rish
    - Yangi e'lon qo'shish
    - E'lonni tahrirlash (oylik narx, manzil, tavsif, rasm, video)
    - E'lonni o'chirish

  Statistika:
    - Jami e'lonlar soni

SOZLASH:
  .env fayliga qo'shing:
    ADMIN_IDS=123456789,987654321
"""
import logging
from datetime import datetime
from os import getenv

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.filters import Command
from aiogram.fsm.state import State, StatesGroup

from utils.constants import (
    REGIONS, PROPERTY_TYPES, RENTAL_TYPES, RENTAL_PERIODS,
    format_price, format_area,
    get_region_name_by_code, get_property_type_name_by_code
)
from utils.keyboards import (
    get_regions_keyboard, get_property_types_keyboard,
    get_rental_types_keyboard, get_rental_period_keyboard,
)

router = Router()

# ── DB yordamchi funksiyalar (admin uchun) ───────────────────────────────────

def _db_get_all_kochmas(db, limit: int = 100) -> list:
    """Barcha Ko'chmas mulk e'lonlarini olish (region/type filtrsiz)"""
    from utils.constants import REGIONS, PROPERTY_TYPES
    objects, seen = [], set()
    for region_code in list(REGIONS.values()):
        for prop_code in list(PROPERTY_TYPES.values()):
            try:
                chunk = db.get_kochmas_mulk_list(
                    region=region_code,
                    property_type=prop_code,
                    action_type='sell',
                    limit=limit
                ) or []
                for obj in chunk:
                    if obj['id'] not in seen:
                        seen.add(obj['id'])
                        objects.append(obj)
            except Exception:
                pass
    return objects[:limit]


def _db_get_all_ijara(db, limit: int = 100) -> list:
    """Barcha Ijara e'lonlarini olish (region/type filtrsiz)"""
    from utils.constants import REGIONS, RENTAL_TYPES
    objects, seen = [], set()
    for region_code in list(REGIONS.values()):
        for prop_code in list(RENTAL_TYPES.values()):
            try:
                chunk = db.get_ijara_list(
                    region=region_code,
                    property_type=prop_code,
                    action_type='rent_out'
                ) or []
                for obj in chunk:
                    if obj['id'] not in seen:
                        seen.add(obj['id'])
                        objects.append(obj)
            except Exception:
                pass
    return objects[:limit]

logger = logging.getLogger(__name__)

# ── Admin IDlarni .env dan olish ─────────────────────────────────────────────
_raw = getenv("ADMIN_IDS", "")
ADMIN_IDS: set[int] = set()
for _a in _raw.split(","):
    _a = _a.strip()
    if _a.isdigit():
        ADMIN_IDS.add(int(_a))
# Eski ADMIN_CHAT_ID ni ham qo'shish
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


# ============================================================================
# KLAVIATURALAR
# ============================================================================

def _kb(*rows):
    """ReplyKeyboardMarkup yaratish"""
    from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=t) for t in row] for row in rows],
        resize_keyboard=True
    )


def get_admin_main_menu():
    return _kb(
        ["🏠 Ko'chmas mulk (Admin)", "📋 Ijara (Admin)"],
        ["📊 Statistika"],
        ["🔙 Asosiy menyuga qaytish"]
    )


def get_admin_kochmas_menu():
    return _kb(
        ["➕ Ko'chmas mulk qo'shish"],
        ["📋 Barcha Ko'chmas mulk e'lonlar"],
        ["🔙 Admin menyu"]
    )


def get_admin_ijara_menu():
    return _kb(
        ["➕ Ijara e'loni qo'shish"],
        ["📋 Barcha Ijara e'lonlar"],
        ["🔙 Admin menyu"]
    )


def get_cancel_admin():
    return _kb(["❌ Bekor qilish"])


def get_skip_cancel_admin():
    return _kb(["⏭️ O'tkazib yuborish"], ["❌ Bekor qilish"])


def get_confirm_admin():
    return _kb(["✅ Saqlash"], ["❌ Bekor qilish"])


def kochmas_detail_kb(obj_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✏️ Narx",    callback_data=f"ake_kochmas_price_{obj_id}"),
            InlineKeyboardButton(text="✏️ Manzil",  callback_data=f"ake_kochmas_address_{obj_id}"),
        ],
        [
            InlineKeyboardButton(text="✏️ Tavsif",  callback_data=f"ake_kochmas_description_{obj_id}"),
            InlineKeyboardButton(text="📸 Rasm",    callback_data=f"ake_kochmas_photo_{obj_id}"),
            InlineKeyboardButton(text="🎥 Video",   callback_data=f"ake_kochmas_video_{obj_id}"),
        ],
        [InlineKeyboardButton(text="🗑️ O'chirish",  callback_data=f"akd_kochmas_{obj_id}")],
        [InlineKeyboardButton(text="🔙 Ro'yxatga qaytish", callback_data="akl_kochmas")],
    ])


def ijara_detail_kb(obj_id: int) -> InlineKeyboardMarkup:
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
        [InlineKeyboardButton(text="🔙 Ro'yxatga qaytish", callback_data="akl_ijara")],
    ])


def confirm_delete_kb(obj_type: str, obj_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Ha, o'chir!", callback_data=f"akdc_{obj_type}_{obj_id}"),
            InlineKeyboardButton(text="❌ Yo'q",        callback_data=f"akv_{obj_type}_{obj_id}"),
        ]
    ])


# ============================================================================
# ADMIN KIRISH
# ============================================================================

@router.message(Command("admin"))
async def admin_command(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        await message.answer("❌ Sizda admin huquqi yo'q.")
        return
    await state.clear()
    await message.answer(
        f"👑 <b>ADMIN PANEL</b>\n\nXush kelibsiz, {message.from_user.first_name}!\n\nBo'limni tanlang:",
        reply_markup=get_admin_main_menu(),
        parse_mode="HTML"
    )


@router.message(F.text == "🔙 Admin menyu")
async def back_to_admin_menu(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    await state.clear()
    await message.answer("👑 Admin panel:", reply_markup=get_admin_main_menu())


# ============================================================================
# STATISTIKA
# ============================================================================

@router.message(F.text == "📊 Statistika")
async def admin_statistics(message: Message):
    if not is_admin(message.from_user.id):
        return
    from database.db_manager import db
    try:
        stats = db.get_statistics()
        text = (
            "📊 <b>BOT STATISTIKASI</b>\n\n"
            f"🏠 Ko'chmas mulk: <b>{stats.get('kochmas_mulk', 0)}</b> ta\n"
            f"📋 Ijara: <b>{stats.get('ijara', 0)}</b> ta\n"
            f"📌 Jami: <b>{stats.get('total', 0)}</b> ta\n\n"
            f"📅 {datetime.now().strftime('%d.%m.%Y %H:%M')}"
        )
    except Exception as e:
        text = f"❌ Xato: {e}"
    await message.answer(text, reply_markup=get_admin_main_menu(), parse_mode="HTML")


# ============================================================================
#  KO'CHMAS MULK — RO'YXAT VA BATAFSIL
# ============================================================================

@router.message(F.text == "🏠 Ko'chmas mulk (Admin)")
async def admin_kochmas_section(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    await state.clear()
    await message.answer("🏠 Ko'chmas mulk boshqaruvi:", reply_markup=get_admin_kochmas_menu())


@router.message(F.text == "📋 Barcha Ko'chmas mulk e'lonlar")
async def admin_list_kochmas(message: Message):
    if not is_admin(message.from_user.id):
        return
    from database.db_manager import db
    objects = _db_get_all_kochmas(db)
    if not objects:
        await message.answer("📭 Ko'chmas mulk e'lonlari yo'q.", reply_markup=get_admin_kochmas_menu())
        return
    keyboard = []
    for obj in objects:
        prop   = get_property_type_name_by_code(obj.get('property_type', ''))
        rooms  = f"{obj['rooms']}-xona " if obj.get('rooms') else ""
        price  = format_price(obj.get('price', 0))
        region = get_region_name_by_code(obj.get('region', ''))
        label  = f"#{obj['id']} | {rooms}{prop} | {price} | {region}"
        keyboard.append([InlineKeyboardButton(text=label[:64], callback_data=f"akv_kochmas_{obj['id']}")])
    await message.answer(
        f"🏠 <b>BARCHA KO'CHMAS MULK E'LONLAR</b>\n\nJami: {len(objects)} ta",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard),
        parse_mode="HTML"
    )


@router.callback_query(F.data.startswith("akv_kochmas_"))
async def admin_view_kochmas(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Ruxsat yo'q", show_alert=True)
        return
    from database.db_manager import db
    try:
        obj_id = int(callback.data.split("_")[-1])
    except (ValueError, IndexError):
        await callback.answer("❌ Xato", show_alert=True)
        return
    obj = db.get_kochmas_mulk_by_id(obj_id)
    if not obj:
        await callback.answer("❌ Topilmadi!", show_alert=True)
        return
    text = (
        f"🏠 <b>#{obj['id']} — {get_property_type_name_by_code(obj.get('property_type', ''))}</b>\n\n"
        f"🗺️ {get_region_name_by_code(obj.get('region', ''))}\n"
        f"📐 {format_area(obj.get('area', 0))}\n"
    )
    if obj.get('rooms'):
        text += f"🚪 {obj['rooms']} xona\n"
    if obj.get('floor'):
        text += f"🏢 {obj['floor']}/{obj.get('total_floors', '?')} qavat\n"
    text += f"💰 {format_price(obj.get('price', 0))}\n"
    text += f"📍 {obj.get('address', '—')}\n"
    text += f"👤 {obj.get('full_name', '—')} | {obj.get('phone', '—')}\n"
    if obj.get('description'):
        text += f"\n📝 {obj['description'][:200]}\n"
    text += f"\n📅 {obj.get('created_at', '')}"
    try:
        if obj.get('photo_id'):
            await callback.message.delete()
            await callback.bot.send_photo(
                chat_id=callback.message.chat.id,
                photo=obj['photo_id'], caption=text,
                reply_markup=kochmas_detail_kb(obj_id), parse_mode="HTML"
            )
        else:
            await callback.message.edit_text(text, reply_markup=kochmas_detail_kb(obj_id), parse_mode="HTML")
    except Exception:
        await callback.message.answer(text, reply_markup=kochmas_detail_kb(obj_id), parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data == "akl_kochmas")
async def adm_back_kochmas_list(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Ruxsat yo'q", show_alert=True)
        return
    try:
        await callback.message.delete()
    except Exception:
        pass
    await admin_list_kochmas(callback.message)
    await callback.answer()


# ── Ko'chmas O'chirish ───────────────────────────────────────────────────────

@router.callback_query(F.data.startswith("akd_kochmas_"))
async def admin_delete_kochmas_ask(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Ruxsat yo'q", show_alert=True)
        return
    try:
        obj_id = int(callback.data.split("_")[-1])
    except (ValueError, IndexError):
        await callback.answer("❌ Xato", show_alert=True)
        return
    await callback.message.answer(
        f"⚠️ <b>#{obj_id} e'lonni o'chirmoqchimisiz?</b>\n\nBu amalni qaytarib bo'lmaydi!",
        reply_markup=confirm_delete_kb("kochmas", obj_id), parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data.startswith("akdc_kochmas_"))
async def admin_delete_kochmas_do(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Ruxsat yo'q", show_alert=True)
        return
    from database.db_manager import db
    try:
        obj_id = int(callback.data.split("_")[-1])
    except (ValueError, IndexError):
        await callback.answer("❌ Xato", show_alert=True)
        return
    try:
        db.delete_kochmas_mulk(obj_id)
        await callback.message.edit_text(f"✅ Ko'chmas mulk #{obj_id} o'chirildi!")
        logger.info(f"Admin {callback.from_user.id}: Ko'chmas #{obj_id} o'chirildi")
    except Exception as e:
        await callback.message.edit_text(f"❌ Xato: {e}")
    await callback.answer()


# ── Ko'chmas Tahrirlash ──────────────────────────────────────────────────────

@router.callback_query(F.data.startswith("ake_kochmas_"))
async def admin_edit_kochmas_start(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Ruxsat yo'q", show_alert=True)
        return
    # format: ake_kochmas_FIELD_ID
    parts  = callback.data.split("_")   # ['ake','kochmas','field','123']
    obj_id = int(parts[-1])
    field  = parts[-2]   # price / address / description / photo / video

    await state.update_data(edit_obj_id=obj_id, edit_obj_type="kochmas", edit_field=field)
    await state.set_state(AdminEditKochmas.entering_value)

    prompts = {
        "price":       "💰 Yangi narxni kiriting (so'm):\n<i>Masalan: 350000000</i>",
        "address":     "📍 Yangi manzilni kiriting:",
        "description": "📝 Yangi tavsifni kiriting:",
        "photo":       "📸 Yangi rasmni yuboring:",
        "video":       "🎥 Yangi videoni yuboring:",
    }
    await callback.message.answer(
        f"✏️ <b>Tahrirlash</b>\n\n{prompts.get(field, 'Yangi qiymat:')}",
        reply_markup=get_cancel_admin(), parse_mode="HTML"
    )
    await callback.answer()


@router.message(AdminEditKochmas.entering_value)
async def admin_edit_kochmas_save(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    if message.text == "❌ Bekor qilish":
        await state.clear()
        await message.answer("Bekor qilindi.", reply_markup=get_admin_kochmas_menu())
        return
    from database.db_manager import db
    data   = await state.get_data()
    obj_id = data['edit_obj_id']
    field  = data['edit_field']
    try:
        if field == "price":
            val = float(message.text.replace(" ", "").replace(",", ""))
            db.update_kochmas_mulk(obj_id, {"price": val})
            await message.answer(f"✅ Narx yangilandi: {format_price(val)}", reply_markup=get_admin_kochmas_menu())
        elif field == "address":
            db.update_kochmas_mulk(obj_id, {"address": message.text.strip()})
            await message.answer("✅ Manzil yangilandi!", reply_markup=get_admin_kochmas_menu())
        elif field == "description":
            db.update_kochmas_mulk(obj_id, {"description": message.text.strip()})
            await message.answer("✅ Tavsif yangilandi!", reply_markup=get_admin_kochmas_menu())
        elif field == "photo":
            if not message.photo:
                await message.answer("❌ Rasm yuboring!")
                return
            db.update_kochmas_mulk(obj_id, {"photo_id": message.photo[-1].file_id})
            await message.answer("✅ Rasm yangilandi!", reply_markup=get_admin_kochmas_menu())
        elif field == "video":
            if not message.video:
                await message.answer("❌ Video yuboring!")
                return
            db.update_kochmas_mulk(obj_id, {"video_id": message.video.file_id})
            await message.answer("✅ Video yangilandi!", reply_markup=get_admin_kochmas_menu())
        logger.info(f"Admin {message.from_user.id}: Ko'chmas #{obj_id} '{field}' yangilandi")
    except Exception as e:
        await message.answer(f"❌ Xato: {e}", reply_markup=get_admin_kochmas_menu())
    await state.clear()


# ============================================================================
# KO'CHMAS MULK QO'SHISH (Admin)
# ============================================================================

@router.message(F.text == "➕ Ko'chmas mulk qo'shish")
async def admin_add_kochmas_start(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    await state.set_state(AdminAddKochmas.choosing_region)
    await message.answer("🗺️ <b>Viloyatni tanlang:</b>", reply_markup=get_regions_keyboard(), parse_mode="HTML")


@router.message(AdminAddKochmas.choosing_region)
async def _ak_region(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    if message.text == "❌ Bekor qilish":
        await state.clear()
        return await message.answer("Bekor.", reply_markup=get_admin_kochmas_menu())
    if message.text not in REGIONS:
        return await message.answer("❌ Tugmadan tanlang!", reply_markup=get_regions_keyboard())
    await state.update_data(region=REGIONS[message.text], region_name=message.text)
    await state.set_state(AdminAddKochmas.choosing_property_type)
    await message.answer("🏠 <b>Mulk turi:</b>", reply_markup=get_property_types_keyboard(), parse_mode="HTML")


@router.message(AdminAddKochmas.choosing_property_type)
async def _ak_prop(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    if message.text == "❌ Bekor qilish":
        await state.clear()
        return await message.answer("Bekor.", reply_markup=get_admin_kochmas_menu())
    if message.text not in PROPERTY_TYPES:
        return await message.answer("❌ Tugmadan tanlang!", reply_markup=get_property_types_keyboard())
    await state.update_data(property_type=PROPERTY_TYPES[message.text], property_type_name=message.text)
    await state.set_state(AdminAddKochmas.entering_full_name)
    await message.answer("👤 <b>Sotuvchi ismi:</b>", reply_markup=get_cancel_admin(), parse_mode="HTML")


@router.message(AdminAddKochmas.entering_full_name)
async def _ak_name(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    if message.text == "❌ Bekor qilish":
        await state.clear()
        return await message.answer("Bekor.", reply_markup=get_admin_kochmas_menu())
    await state.update_data(full_name=message.text.strip())
    await state.set_state(AdminAddKochmas.entering_phone)
    await message.answer("📱 <b>Telefon raqami:</b>", reply_markup=get_cancel_admin(), parse_mode="HTML")


@router.message(AdminAddKochmas.entering_phone)
async def _ak_phone(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    if message.text == "❌ Bekor qilish":
        await state.clear()
        return await message.answer("Bekor.", reply_markup=get_admin_kochmas_menu())
    phone = message.text.replace(" ", "").replace("-", "").strip()
    if not phone.startswith("+998"):
        phone = "+998" + phone.lstrip("998").lstrip("+998")
    await state.update_data(phone=phone)
    await state.set_state(AdminAddKochmas.entering_area)
    await message.answer("📐 <b>Maydon (m²):</b>", reply_markup=get_cancel_admin(), parse_mode="HTML")


@router.message(AdminAddKochmas.entering_area)
async def _ak_area(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    if message.text == "❌ Bekor qilish":
        await state.clear()
        return await message.answer("Bekor.", reply_markup=get_admin_kochmas_menu())
    try:
        area = float(message.text.replace(",", ".").strip())
        if area <= 0:
            raise ValueError
    except ValueError:
        return await message.answer("❌ To'g'ri raqam kiriting!")
    await state.update_data(area=area)
    data = await state.get_data()
    if data.get('property_type') in ['apartment', 'house']:
        await state.set_state(AdminAddKochmas.entering_rooms)
        await message.answer("🚪 <b>Xonalar soni:</b>", reply_markup=get_cancel_admin(), parse_mode="HTML")
    else:
        await state.set_state(AdminAddKochmas.entering_price)
        await message.answer("💰 <b>Narxi (so'm):</b>", reply_markup=get_cancel_admin(), parse_mode="HTML")


@router.message(AdminAddKochmas.entering_rooms)
async def _ak_rooms(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    if message.text == "❌ Bekor qilish":
        await state.clear()
        return await message.answer("Bekor.", reply_markup=get_admin_kochmas_menu())
    try:
        rooms = int(message.text.strip())
        if rooms <= 0:
            raise ValueError
    except ValueError:
        return await message.answer("❌ To'g'ri raqam kiriting!")
    await state.update_data(rooms=rooms)
    data = await state.get_data()
    if data.get('property_type') == 'apartment':
        await state.set_state(AdminAddKochmas.entering_floor)
        await message.answer("🏢 <b>Qavat:</b>", reply_markup=get_cancel_admin(), parse_mode="HTML")
    else:
        await state.set_state(AdminAddKochmas.entering_price)
        await message.answer("💰 <b>Narxi (so'm):</b>", reply_markup=get_cancel_admin(), parse_mode="HTML")


@router.message(AdminAddKochmas.entering_floor)
async def _ak_floor(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    if message.text == "❌ Bekor qilish":
        await state.clear()
        return await message.answer("Bekor.", reply_markup=get_admin_kochmas_menu())
    try:
        floor = int(message.text.strip())
        if floor <= 0:
            raise ValueError
    except ValueError:
        return await message.answer("❌ To'g'ri raqam!")
    await state.update_data(floor=floor)
    await state.set_state(AdminAddKochmas.entering_total_floors)
    await message.answer("🏢 <b>Jami qavatlar soni:</b>", reply_markup=get_cancel_admin(), parse_mode="HTML")


@router.message(AdminAddKochmas.entering_total_floors)
async def _ak_total_floors(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    if message.text == "❌ Bekor qilish":
        await state.clear()
        return await message.answer("Bekor.", reply_markup=get_admin_kochmas_menu())
    try:
        total = int(message.text.strip())
        if total <= 0:
            raise ValueError
        data = await state.get_data()
        if data.get('floor', 0) > total:
            return await message.answer("❌ Qavat jami qavatdan katta bo'lmaydi!")
    except ValueError:
        return await message.answer("❌ To'g'ri raqam!")
    await state.update_data(total_floors=total)
    await state.set_state(AdminAddKochmas.entering_price)
    await message.answer("💰 <b>Narxi (so'm):</b>", reply_markup=get_cancel_admin(), parse_mode="HTML")


@router.message(AdminAddKochmas.entering_price)
async def _ak_price(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    if message.text == "❌ Bekor qilish":
        await state.clear()
        return await message.answer("Bekor.", reply_markup=get_admin_kochmas_menu())
    try:
        price = float(message.text.replace(" ", "").replace(",", "").strip())
        if price <= 0:
            raise ValueError
    except ValueError:
        return await message.answer("❌ To'g'ri narx kiriting!")
    await state.update_data(price=price)
    await state.set_state(AdminAddKochmas.entering_address)
    await message.answer("📍 <b>Manzil:</b>", reply_markup=get_cancel_admin(), parse_mode="HTML")


@router.message(AdminAddKochmas.entering_address)
async def _ak_address(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    if message.text == "❌ Bekor qilish":
        await state.clear()
        return await message.answer("Bekor.", reply_markup=get_admin_kochmas_menu())
    await state.update_data(address=message.text.strip())
    await state.set_state(AdminAddKochmas.entering_description)
    await message.answer("📝 <b>Tavsif (ixtiyoriy):</b>", reply_markup=get_skip_cancel_admin(), parse_mode="HTML")


@router.message(AdminAddKochmas.entering_description)
async def _ak_desc(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    if message.text == "❌ Bekor qilish":
        await state.clear()
        return await message.answer("Bekor.", reply_markup=get_admin_kochmas_menu())
    if message.text != "⏭️ O'tkazib yuborish":
        await state.update_data(description=message.text.strip())
    await state.set_state(AdminAddKochmas.uploading_photo)
    await message.answer("📸 <b>Rasm (ixtiyoriy):</b>", reply_markup=get_skip_cancel_admin(), parse_mode="HTML")


@router.message(AdminAddKochmas.uploading_photo, F.photo)
async def _ak_photo(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    await state.update_data(photo_id=message.photo[-1].file_id)
    await state.set_state(AdminAddKochmas.uploading_video)
    await message.answer("🎥 <b>Video (ixtiyoriy):</b>", reply_markup=get_skip_cancel_admin(), parse_mode="HTML")


@router.message(AdminAddKochmas.uploading_photo)
async def _ak_photo_skip(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    if message.text == "❌ Bekor qilish":
        await state.clear()
        return await message.answer("Bekor.", reply_markup=get_admin_kochmas_menu())
    if message.text != "⏭️ O'tkazib yuborish":
        return await message.answer("❌ Rasm yuboring yoki o'tkazib yuboring!", reply_markup=get_skip_cancel_admin())
    await state.set_state(AdminAddKochmas.uploading_video)
    await message.answer("🎥 <b>Video (ixtiyoriy):</b>", reply_markup=get_skip_cancel_admin(), parse_mode="HTML")


@router.message(AdminAddKochmas.uploading_video, F.video)
async def _ak_video(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    await state.update_data(video_id=message.video.file_id)
    await _ak_show_confirm(message, state)


@router.message(AdminAddKochmas.uploading_video)
async def _ak_video_skip(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    if message.text == "❌ Bekor qilish":
        await state.clear()
        return await message.answer("Bekor.", reply_markup=get_admin_kochmas_menu())
    if message.text != "⏭️ O'tkazib yuborish":
        return await message.answer("❌ Video yuboring yoki o'tkazib yuboring!", reply_markup=get_skip_cancel_admin())
    await _ak_show_confirm(message, state)


async def _ak_show_confirm(message: Message, state: FSMContext):
    data = await state.get_data()
    text = (
        "📋 <b>YANGI E'LON — Ko'chmas Mulk</b>\n\n"
        f"🗺️ {data.get('region_name')}\n"
        f"🏠 {data.get('property_type_name')}\n"
        f"👤 {data.get('full_name')} | {data.get('phone')}\n"
        f"📐 {format_area(data.get('area', 0))}\n"
    )
    if data.get('rooms'):
        text += f"🚪 {data['rooms']} xona\n"
    if data.get('floor'):
        text += f"🏢 {data['floor']}/{data.get('total_floors')} qavat\n"
    text += f"💰 {format_price(data.get('price', 0))}\n"
    text += f"📍 {data.get('address')}\n"
    if data.get('description'):
        text += f"📝 {data['description'][:200]}\n"
    text += f"\n📸 {'✅' if data.get('photo_id') else '❌'} | 🎥 {'✅' if data.get('video_id') else '❌'}"
    text += "\n\n❓ Saqlaysizmi?"
    await state.set_state(AdminAddKochmas.confirmation)
    await message.answer(text, reply_markup=get_confirm_admin(), parse_mode="HTML")


@router.message(AdminAddKochmas.confirmation)
async def _ak_confirm(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    if message.text == "❌ Bekor qilish":
        await state.clear()
        return await message.answer("Bekor.", reply_markup=get_admin_kochmas_menu())
    if message.text != "✅ Saqlash":
        return
    from database.db_manager import db
    data = await state.get_data()
    try:
        obj_id = db.add_kochmas_mulk({
            'user_id':       message.from_user.id,
            'username':      message.from_user.username,
            'full_name':     data.get('full_name', ''),
            'phone':         data.get('phone', ''),
            'region':        data['region'],
            'property_type': data['property_type'],
            'action_type':   'sell',
            'area':          data.get('area'),
            'rooms':         data.get('rooms'),
            'floor':         data.get('floor'),
            'total_floors':  data.get('total_floors'),
            'price':         data['price'],
            'description':   data.get('description'),
            'photo_id':      data.get('photo_id'),
            'video_id':      data.get('video_id'),
            'address':       data['address']
        })
        await message.answer(
            f"✅ <b>Ko'chmas mulk e'loni qo'shildi!</b>\n🆔 #{obj_id}",
            reply_markup=get_admin_kochmas_menu(), parse_mode="HTML"
        )
        logger.info(f"Admin {message.from_user.id}: Ko'chmas #{obj_id} qo'shdi")
    except Exception as e:
        await message.answer(f"❌ Xato: {e}", reply_markup=get_admin_kochmas_menu())
    await state.clear()


# ============================================================================
#  IJARA — RO'YXAT VA BATAFSIL
# ============================================================================

@router.message(F.text == "📋 Ijara (Admin)")
async def admin_ijara_section(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    await state.clear()
    await message.answer("📋 Ijara boshqaruvi:", reply_markup=get_admin_ijara_menu())


@router.message(F.text == "📋 Barcha Ijara e'lonlar")
async def admin_list_ijara(message: Message):
    if not is_admin(message.from_user.id):
        return
    from database.db_manager import db
    objects = _db_get_all_ijara(db)
    if not objects:
        await message.answer("📭 Ijara e'lonlari yo'q.", reply_markup=get_admin_ijara_menu())
        return
    keyboard = []
    for obj in objects:
        prop   = get_property_type_name_by_code(obj.get('property_type', ''))
        rooms  = f"{obj['rooms']}-xona " if obj.get('rooms') else ""
        price  = format_price(obj.get('monthly_price', 0))
        region = get_region_name_by_code(obj.get('region', ''))
        label  = f"#{obj['id']} | {rooms}{prop} | {price}/oy | {region}"
        keyboard.append([InlineKeyboardButton(text=label[:64], callback_data=f"akv_ijara_{obj['id']}")])
    await message.answer(
        f"📋 <b>BARCHA IJARA E'LONLAR</b>\n\nJami: {len(objects)} ta",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard),
        parse_mode="HTML"
    )


@router.callback_query(F.data.startswith("akv_ijara_"))
async def admin_view_ijara(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Ruxsat yo'q", show_alert=True)
        return
    from database.db_manager import db
    try:
        obj_id = int(callback.data.split("_")[-1])
    except (ValueError, IndexError):
        await callback.answer("❌ Xato", show_alert=True)
        return
    obj = db.get_ijara_by_id(obj_id)
    if not obj:
        await callback.answer("❌ Topilmadi!", show_alert=True)
        return
    text = (
        f"📋 <b>#{obj['id']} — {get_property_type_name_by_code(obj.get('property_type', ''))} (Ijara)</b>\n\n"
        f"🗺️ {get_region_name_by_code(obj.get('region', ''))}\n"
        f"📐 {format_area(obj.get('area', 0))}\n"
    )
    if obj.get('rooms'):
        text += f"🚪 {obj['rooms']} xona\n"
    if obj.get('floor'):
        text += f"🏢 {obj['floor']}/{obj.get('total_floors', '?')} qavat\n"
    text += f"💰 {format_price(obj.get('monthly_price', 0))}/oy\n"
    if obj.get('min_rental_period'):
        text += f"📅 Min: {obj['min_rental_period']}\n"
    text += f"📍 {obj.get('address', '—')}\n"
    text += f"👤 {obj.get('full_name', '—')} | {obj.get('phone', '—')}\n"
    if obj.get('description'):
        text += f"\n📝 {obj['description'][:200]}\n"
    text += f"\n📅 {obj.get('created_at', '')}"
    try:
        if obj.get('photo_id'):
            await callback.message.delete()
            await callback.bot.send_photo(
                chat_id=callback.message.chat.id,
                photo=obj['photo_id'], caption=text,
                reply_markup=ijara_detail_kb(obj_id), parse_mode="HTML"
            )
        else:
            await callback.message.edit_text(text, reply_markup=ijara_detail_kb(obj_id), parse_mode="HTML")
    except Exception:
        await callback.message.answer(text, reply_markup=ijara_detail_kb(obj_id), parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data == "akl_ijara")
async def adm_back_ijara_list(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Ruxsat yo'q", show_alert=True)
        return
    try:
        await callback.message.delete()
    except Exception:
        pass
    await admin_list_ijara(callback.message)
    await callback.answer()


# ── Ijara O'chirish ──────────────────────────────────────────────────────────

@router.callback_query(F.data.startswith("akd_ijara_"))
async def admin_delete_ijara_ask(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Ruxsat yo'q", show_alert=True)
        return
    try:
        obj_id = int(callback.data.split("_")[-1])
    except (ValueError, IndexError):
        await callback.answer("❌ Xato", show_alert=True)
        return
    await callback.message.answer(
        f"⚠️ <b>Ijara #{obj_id} e'lonni o'chirmoqchimisiz?</b>",
        reply_markup=confirm_delete_kb("ijara", obj_id), parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data.startswith("akdc_ijara_"))
async def admin_delete_ijara_do(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Ruxsat yo'q", show_alert=True)
        return
    from database.db_manager import db
    try:
        obj_id = int(callback.data.split("_")[-1])
    except (ValueError, IndexError):
        await callback.answer("❌ Xato", show_alert=True)
        return
    try:
        db.delete_ijara(obj_id)
        await callback.message.edit_text(f"✅ Ijara #{obj_id} o'chirildi!")
        logger.info(f"Admin {callback.from_user.id}: Ijara #{obj_id} o'chirildi")
    except Exception as e:
        await callback.message.edit_text(f"❌ Xato: {e}")
    await callback.answer()


# ── Ijara Tahrirlash ─────────────────────────────────────────────────────────

@router.callback_query(F.data.startswith("ake_ijara_"))
async def admin_edit_ijara_start(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Ruxsat yo'q", show_alert=True)
        return
    parts  = callback.data.split("_")   # ['ake','ijara','field','123']
    obj_id = int(parts[-1])
    field  = parts[-2]

    await state.update_data(edit_obj_id=obj_id, edit_obj_type="ijara", edit_field=field)
    await state.set_state(AdminEditIjara.entering_value)

    prompts = {
        "monthly_price": "💰 Yangi oylik narxni kiriting (so'm):",
        "address":       "📍 Yangi manzilni kiriting:",
        "description":   "📝 Yangi tavsifni kiriting:",
        "photo":         "📸 Yangi rasmni yuboring:",
        "video":         "🎥 Yangi videoni yuboring:",
    }
    await callback.message.answer(
        f"✏️ <b>Tahrirlash</b>\n\n{prompts.get(field, 'Yangi qiymat:')}",
        reply_markup=get_cancel_admin(), parse_mode="HTML"
    )
    await callback.answer()


@router.message(AdminEditIjara.entering_value)
async def admin_edit_ijara_save(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    if message.text == "❌ Bekor qilish":
        await state.clear()
        return await message.answer("Bekor.", reply_markup=get_admin_ijara_menu())
    from database.db_manager import db
    data   = await state.get_data()
    obj_id = data['edit_obj_id']
    field  = data['edit_field']
    try:
        if field == "monthly_price":
            val = float(message.text.replace(" ", "").replace(",", ""))
            db.update_ijara(obj_id, {"monthly_price": val})
            await message.answer(f"✅ Oylik narx: {format_price(val)}", reply_markup=get_admin_ijara_menu())
        elif field == "address":
            db.update_ijara(obj_id, {"address": message.text.strip()})
            await message.answer("✅ Manzil yangilandi!", reply_markup=get_admin_ijara_menu())
        elif field == "description":
            db.update_ijara(obj_id, {"description": message.text.strip()})
            await message.answer("✅ Tavsif yangilandi!", reply_markup=get_admin_ijara_menu())
        elif field == "photo":
            if not message.photo:
                return await message.answer("❌ Rasm yuboring!")
            db.update_ijara(obj_id, {"photo_id": message.photo[-1].file_id})
            await message.answer("✅ Rasm yangilandi!", reply_markup=get_admin_ijara_menu())
        elif field == "video":
            if not message.video:
                return await message.answer("❌ Video yuboring!")
            db.update_ijara(obj_id, {"video_id": message.video.file_id})
            await message.answer("✅ Video yangilandi!", reply_markup=get_admin_ijara_menu())
        logger.info(f"Admin {message.from_user.id}: Ijara #{obj_id} '{field}' yangilandi")
    except Exception as e:
        await message.answer(f"❌ Xato: {e}", reply_markup=get_admin_ijara_menu())
    await state.clear()


# ============================================================================
# IJARA QO'SHISH (Admin)
# ============================================================================

@router.message(F.text == "➕ Ijara e'loni qo'shish")
async def admin_add_ijara_start(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    await state.set_state(AdminAddIjara.choosing_region)
    await message.answer("🗺️ <b>Viloyatni tanlang:</b>", reply_markup=get_regions_keyboard(), parse_mode="HTML")


@router.message(AdminAddIjara.choosing_region)
async def _ai_region(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    if message.text == "❌ Bekor qilish":
        await state.clear()
        return await message.answer("Bekor.", reply_markup=get_admin_ijara_menu())
    if message.text not in REGIONS:
        return await message.answer("❌ Tugmadan tanlang!", reply_markup=get_regions_keyboard())
    await state.update_data(region=REGIONS[message.text], region_name=message.text)
    await state.set_state(AdminAddIjara.choosing_property_type)
    await message.answer("🏠 <b>Ijara turi:</b>", reply_markup=get_rental_types_keyboard(), parse_mode="HTML")


@router.message(AdminAddIjara.choosing_property_type)
async def _ai_prop(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    if message.text == "❌ Bekor qilish":
        await state.clear()
        return await message.answer("Bekor.", reply_markup=get_admin_ijara_menu())
    if message.text not in RENTAL_TYPES:
        return await message.answer("❌ Tugmadan tanlang!", reply_markup=get_rental_types_keyboard())
    await state.update_data(property_type=RENTAL_TYPES[message.text], property_type_name=message.text)
    await state.set_state(AdminAddIjara.entering_full_name)
    await message.answer("👤 <b>Egasi ismi:</b>", reply_markup=get_cancel_admin(), parse_mode="HTML")


@router.message(AdminAddIjara.entering_full_name)
async def _ai_name(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    if message.text == "❌ Bekor qilish":
        await state.clear()
        return await message.answer("Bekor.", reply_markup=get_admin_ijara_menu())
    await state.update_data(full_name=message.text.strip())
    await state.set_state(AdminAddIjara.entering_phone)
    await message.answer("📱 <b>Telefon:</b>", reply_markup=get_cancel_admin(), parse_mode="HTML")


@router.message(AdminAddIjara.entering_phone)
async def _ai_phone(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    if message.text == "❌ Bekor qilish":
        await state.clear()
        return await message.answer("Bekor.", reply_markup=get_admin_ijara_menu())
    phone = message.text.replace(" ", "").replace("-", "").strip()
    if not phone.startswith("+998"):
        phone = "+998" + phone.lstrip("998").lstrip("+998")
    await state.update_data(phone=phone)
    await state.set_state(AdminAddIjara.entering_area)
    await message.answer("📐 <b>Maydon (m²):</b>", reply_markup=get_cancel_admin(), parse_mode="HTML")


@router.message(AdminAddIjara.entering_area)
async def _ai_area(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    if message.text == "❌ Bekor qilish":
        await state.clear()
        return await message.answer("Bekor.", reply_markup=get_admin_ijara_menu())
    try:
        area = float(message.text.replace(",", ".").strip())
        if area <= 0:
            raise ValueError
    except ValueError:
        return await message.answer("❌ To'g'ri raqam!")
    await state.update_data(area=area)
    data = await state.get_data()
    if data.get('property_type') in ['apartment', 'house']:
        await state.set_state(AdminAddIjara.entering_rooms)
        await message.answer("🚪 <b>Xonalar soni:</b>", reply_markup=get_cancel_admin(), parse_mode="HTML")
    else:
        await state.set_state(AdminAddIjara.entering_monthly_price)
        await message.answer("💰 <b>Oylik narx (so'm):</b>", reply_markup=get_cancel_admin(), parse_mode="HTML")


@router.message(AdminAddIjara.entering_rooms)
async def _ai_rooms(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    if message.text == "❌ Bekor qilish":
        await state.clear()
        return await message.answer("Bekor.", reply_markup=get_admin_ijara_menu())
    try:
        rooms = int(message.text.strip())
        if rooms <= 0:
            raise ValueError
    except ValueError:
        return await message.answer("❌ To'g'ri raqam!")
    await state.update_data(rooms=rooms)
    data = await state.get_data()
    if data.get('property_type') == 'apartment':
        await state.set_state(AdminAddIjara.entering_floor)
        await message.answer("🏢 <b>Qavat:</b>", reply_markup=get_cancel_admin(), parse_mode="HTML")
    else:
        await state.set_state(AdminAddIjara.entering_monthly_price)
        await message.answer("💰 <b>Oylik narx (so'm):</b>", reply_markup=get_cancel_admin(), parse_mode="HTML")


@router.message(AdminAddIjara.entering_floor)
async def _ai_floor(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    if message.text == "❌ Bekor qilish":
        await state.clear()
        return await message.answer("Bekor.", reply_markup=get_admin_ijara_menu())
    try:
        floor = int(message.text.strip())
        if floor <= 0:
            raise ValueError
    except ValueError:
        return await message.answer("❌ To'g'ri raqam!")
    await state.update_data(floor=floor)
    await state.set_state(AdminAddIjara.entering_total_floors)
    await message.answer("🏢 <b>Jami qavatlar:</b>", reply_markup=get_cancel_admin(), parse_mode="HTML")


@router.message(AdminAddIjara.entering_total_floors)
async def _ai_total_floors(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    if message.text == "❌ Bekor qilish":
        await state.clear()
        return await message.answer("Bekor.", reply_markup=get_admin_ijara_menu())
    try:
        total = int(message.text.strip())
        if total <= 0:
            raise ValueError
        data = await state.get_data()
        if data.get('floor', 0) > total:
            return await message.answer("❌ Qavat jami qavatdan katta bo'lmaydi!")
    except ValueError:
        return await message.answer("❌ To'g'ri raqam!")
    await state.update_data(total_floors=total)
    await state.set_state(AdminAddIjara.entering_monthly_price)
    await message.answer("💰 <b>Oylik narx (so'm):</b>", reply_markup=get_cancel_admin(), parse_mode="HTML")


@router.message(AdminAddIjara.entering_monthly_price)
async def _ai_price(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    if message.text == "❌ Bekor qilish":
        await state.clear()
        return await message.answer("Bekor.", reply_markup=get_admin_ijara_menu())
    try:
        price = float(message.text.replace(" ", "").replace(",", "").strip())
        if price <= 0:
            raise ValueError
    except ValueError:
        return await message.answer("❌ To'g'ri narx!")
    await state.update_data(monthly_price=price)
    await state.set_state(AdminAddIjara.entering_rental_period)
    await message.answer("📅 <b>Minimal ijara muddati:</b>", reply_markup=get_rental_period_keyboard(), parse_mode="HTML")


@router.message(AdminAddIjara.entering_rental_period)
async def _ai_period(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    if message.text == "❌ Bekor qilish":
        await state.clear()
        return await message.answer("Bekor.", reply_markup=get_admin_ijara_menu())
    if message.text not in RENTAL_PERIODS:
        return await message.answer("❌ Tugmadan tanlang!", reply_markup=get_rental_period_keyboard())
    await state.update_data(min_rental_period=message.text)
    await state.set_state(AdminAddIjara.entering_address)
    await message.answer("📍 <b>Manzil:</b>", reply_markup=get_cancel_admin(), parse_mode="HTML")


@router.message(AdminAddIjara.entering_address)
async def _ai_address(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    if message.text == "❌ Bekor qilish":
        await state.clear()
        return await message.answer("Bekor.", reply_markup=get_admin_ijara_menu())
    await state.update_data(address=message.text.strip())
    await state.set_state(AdminAddIjara.entering_description)
    await message.answer("📝 <b>Tavsif (ixtiyoriy):</b>", reply_markup=get_skip_cancel_admin(), parse_mode="HTML")


@router.message(AdminAddIjara.entering_description)
async def _ai_desc(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    if message.text == "❌ Bekor qilish":
        await state.clear()
        return await message.answer("Bekor.", reply_markup=get_admin_ijara_menu())
    if message.text != "⏭️ O'tkazib yuborish":
        await state.update_data(description=message.text.strip())
    await state.set_state(AdminAddIjara.uploading_photo)
    await message.answer("📸 <b>Rasm (ixtiyoriy):</b>", reply_markup=get_skip_cancel_admin(), parse_mode="HTML")


@router.message(AdminAddIjara.uploading_photo, F.photo)
async def _ai_photo(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    await state.update_data(photo_id=message.photo[-1].file_id)
    await state.set_state(AdminAddIjara.uploading_video)
    await message.answer("🎥 <b>Video (ixtiyoriy):</b>", reply_markup=get_skip_cancel_admin(), parse_mode="HTML")


@router.message(AdminAddIjara.uploading_photo)
async def _ai_photo_skip(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    if message.text == "❌ Bekor qilish":
        await state.clear()
        return await message.answer("Bekor.", reply_markup=get_admin_ijara_menu())
    if message.text != "⏭️ O'tkazib yuborish":
        return await message.answer("❌ Rasm yuboring yoki o'tkazib yuboring!", reply_markup=get_skip_cancel_admin())
    await state.set_state(AdminAddIjara.uploading_video)
    await message.answer("🎥 <b>Video (ixtiyoriy):</b>", reply_markup=get_skip_cancel_admin(), parse_mode="HTML")


@router.message(AdminAddIjara.uploading_video, F.video)
async def _ai_video(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    await state.update_data(video_id=message.video.file_id)
    await _ai_show_confirm(message, state)


@router.message(AdminAddIjara.uploading_video)
async def _ai_video_skip(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    if message.text == "❌ Bekor qilish":
        await state.clear()
        return await message.answer("Bekor.", reply_markup=get_admin_ijara_menu())
    if message.text != "⏭️ O'tkazib yuborish":
        return await message.answer("❌ Video yuboring yoki o'tkazib yuboring!", reply_markup=get_skip_cancel_admin())
    await _ai_show_confirm(message, state)


async def _ai_show_confirm(message: Message, state: FSMContext):
    data = await state.get_data()
    text = (
        "📋 <b>YANGI IJARA E'LONI</b>\n\n"
        f"🗺️ {data.get('region_name')}\n"
        f"🏠 {data.get('property_type_name')}\n"
        f"👤 {data.get('full_name')} | {data.get('phone')}\n"
        f"📐 {format_area(data.get('area', 0))}\n"
    )
    if data.get('rooms'):
        text += f"🚪 {data['rooms']} xona\n"
    if data.get('floor'):
        text += f"🏢 {data['floor']}/{data.get('total_floors')} qavat\n"
    text += f"💰 {format_price(data.get('monthly_price', 0))}/oy\n"
    text += f"📅 Min. muddat: {data.get('min_rental_period')}\n"
    text += f"📍 {data.get('address')}\n"
    if data.get('description'):
        text += f"📝 {data['description'][:200]}\n"
    text += f"\n📸 {'✅' if data.get('photo_id') else '❌'} | 🎥 {'✅' if data.get('video_id') else '❌'}"
    text += "\n\n❓ Saqlaysizmi?"
    await state.set_state(AdminAddIjara.confirmation)
    await message.answer(text, reply_markup=get_confirm_admin(), parse_mode="HTML")


@router.message(AdminAddIjara.confirmation)
async def _ai_confirm(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    if message.text == "❌ Bekor qilish":
        await state.clear()
        return await message.answer("Bekor.", reply_markup=get_admin_ijara_menu())
    if message.text != "✅ Saqlash":
        return
    from database.db_manager import db
    data = await state.get_data()
    try:
        obj_id = db.add_ijara({
            'user_id':           message.from_user.id,
            'username':          message.from_user.username,
            'full_name':         data.get('full_name', ''),
            'phone':             data.get('phone', ''),
            'region':            data['region'],
            'property_type':     data['property_type'],
            'action_type':       'rent_out',
            'area':              data.get('area'),
            'rooms':             data.get('rooms'),
            'floor':             data.get('floor'),
            'total_floors':      data.get('total_floors'),
            'monthly_price':     data['monthly_price'],
            'min_rental_period': data.get('min_rental_period'),
            'description':       data.get('description'),
            'photo_id':          data.get('photo_id'),
            'video_id':          data.get('video_id'),
            'address':           data['address']
        })
        await message.answer(
            f"✅ <b>Ijara e'loni qo'shildi!</b>\n🆔 #{obj_id}",
            reply_markup=get_admin_ijara_menu(), parse_mode="HTML"
        )
        logger.info(f"Admin {message.from_user.id}: Ijara #{obj_id} qo'shdi")
    except Exception as e:
        await message.answer(f"❌ Xato: {e}", reply_markup=get_admin_ijara_menu())
    await state.clear()