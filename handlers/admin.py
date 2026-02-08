"""
Professional Admin Panel Handler
Ko'chmas Mulk va Auksion Bot - Admin boshqaruv paneli
Asosiy funksiyalar:
Obyektlarni qo'shish (sotish/ijara)
Obyektlarni ko'rish va tahrirlash
Obyektlarni o'chirish
Statistika va hisobotlar
Xavfsiz ma'lumotlar bazasi bilan ishlash
Professional UX va navigatsiya
Author: Professional refactoring
Version: 2.0
"""
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime
from aiogram import Router, F
from aiogram.types import (
    Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton,
    ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
)
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from dotenv import load_dotenv
from os import getenv
from handlers.database import db  # ✅ Umumiy database dan foydalanish

# ============================================================================
# KONFIGURATSIYA
# ============================================================================
logger = logging.getLogger(__name__)
router = Router()
load_dotenv()
ADMIN_ID = int(getenv("ADMIN_ID", "8135506421"))
ADMIN_CHAT_ID = int(getenv("ADMIN_CHAT_ID"))

# O'zbekiston viloyatlari (BO'SH JOYSIZ!)
VILOYATLAR = [
    "Toshkent shahri",
    "Toshkent viloyati",
    "Andijon",
    "Buxoro",
    "Farg'ona",
    "Jizzax",
    "Xorazm",
    "Namangan",
    "Navoiy",
    "Qashqadaryo",
    "Qoraqalpog'iston Respublikasi",
    "Samarqand",
    "Sirdaryo",
    "Surxondaryo"
]

# Mulk turlari (BO'SH JOYSIZ!)
MULK_SALE = ["Ko'p qavatli uy", "Hovli", "Savdo do'koni", "Yer uchastkasi"]
MULK_RENT = ["Ko'p qavatli uy", "Hovli", "Savdo do'koni", "Mehmonxona", "Boshqa ijara joyi"]

# Sahifalash (pagination) parametrlari
ITEMS_PER_PAGE = 5

# ============================================================================
# FSM STATES (Holat boshqaruvi)
# ============================================================================
class AdminAddForm(StatesGroup):
    """Obyekt qo'shish uchun holatlar"""
    type = State()
    mulk_turi = State()
    viloyat = State()
    joylashuv_detail = State()
    narx = State()
    izoh = State()
    media = State()
    confirm = State()

class AdminDeleteForm(StatesGroup):
    """Obyekt o'chirish uchun holatlar"""
    confirm = State()

class AdminViewForm(StatesGroup):
    """Obyektlarni ko'rish uchun holatlar"""
    type_selected = State()

# ============================================================================
# YORDAMCHI FUNKSIYALAR
# ============================================================================
def is_admin(user_id: int) -> bool:
    """Foydalanuvchi admin ekanligini tekshirish"""
    return user_id == ADMIN_ID

def format_media_list(media_list: List[Dict[str, str]]) -> str:
    """Media ro'yxatini string formatga o'tkazish"""
    if not media_list:
        return ""
    return ','.join([f"{m['type']}:{m['file_id']}" for m in media_list])

def parse_media_string(media_str: Optional[str]) -> List[Dict[str, str]]:
    """String formatdagi medialni list formatga o'tkazish"""
    if not media_str:
        return []
    result = []
    for item in media_str.split(','):
        parts = item.split(':', 1)
        if len(parts) == 2:
            result.append({'type': parts[0], 'file_id': parts[1]})
    return result

def format_object_info(obj: Dict) -> str:
    """Obyekt ma'lumotlarini formatlash"""
    media_count = len(parse_media_string(obj.get('media', '')))
    obj_type = 'Sotuv' if obj['type'] == 'sale' else 'Ijara'
    izoh_text = obj['izoh'] or "Yo'q"
    created_at = obj.get('created_at', "Ma'lumot yo'q")
    return (
        f"🆔 ID: {obj['id']}\n"
        f"📋 Turi: {obj_type}\n"
        f"🏠 Mulk: {obj['mulk_turi']}\n"
        f"📍 Joylashuv: {obj['joylashuv']}\n"
        f"💰 Narx: {obj['narx']}\n"
        f"📝 Izoh: {izoh_text}\n"
        f"📸 Media: {media_count} ta\n"
        f"📅 Qo'shilgan: {created_at}"
    )

# ============================================================================
# KEYBOARD (TUGMALAR) YARATISH
# ============================================================================
def get_admin_menu() -> InlineKeyboardMarkup:
    """Asosiy admin menyusi"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Yangi obyekt qo'shish", callback_data="admin_add")],
        [InlineKeyboardButton(text="📋 Obyektlarni boshqarish", callback_data="admin_view")],
        [InlineKeyboardButton(text="📊 Statistika", callback_data="admin_stats")],
        [InlineKeyboardButton(text="🌐 Veb-panel", url="http://127.0.0.1:5000")],
        [InlineKeyboardButton(text="❌ Yopish", callback_data="admin_close")]
    ])

def get_type_keyboard(show_back: bool = True) -> InlineKeyboardMarkup:
    """Obyekt turi tanlash tugmalari"""
    keyboard = [
        [InlineKeyboardButton(text="💰 Sotuv", callback_data="admin_type_sale")],
        [InlineKeyboardButton(text="🏠 Ijara", callback_data="admin_type_rent")]
    ]
    if show_back:
        keyboard.append([InlineKeyboardButton(text="🔙 Orqaga", callback_data="admin_menu")])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_mulk_keyboard(obj_type: str) -> InlineKeyboardMarkup:
    """Mulk turi tanlash tugmalari"""
    buttons = MULK_SALE if obj_type == "sale" else MULK_RENT
    keyboard = [[InlineKeyboardButton(text=btn, callback_data=f"admin_mulk_{btn}")] for btn in buttons]
    keyboard.append([InlineKeyboardButton(text="🔙 Orqaga", callback_data="admin_menu")])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_viloyat_keyboard() -> ReplyKeyboardMarkup:
    """Viloyat tanlash tugmalari"""
    keyboard = [[KeyboardButton(text=v)] for v in VILOYATLAR]
    keyboard.append([KeyboardButton(text="🔙 Bekor qilish")])
    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True,
        input_field_placeholder="Viloyatni tanlang..."
    )

def get_confirm_keyboard() -> InlineKeyboardMarkup:
    """Tasdiqlash tugmalari"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Tasdiqlash", callback_data="admin_confirm_yes"),
            InlineKeyboardButton(text="❌ Bekor qilish", callback_data="admin_confirm_no")
        ]
    ])

def get_object_actions_keyboard(obj_id: int) -> InlineKeyboardMarkup:
    """Obyekt ustida amallar tugmalari"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🗑 O'chirish", callback_data=f"admin_delete_{obj_id}")],
        [InlineKeyboardButton(text="🔙 Orqaga", callback_data="admin_view")]
    ])

def get_pagination_keyboard(
    obj_type: str,
    current_page: int,
    total_pages: int
) -> InlineKeyboardMarkup:
    """Sahifalash tugmalari"""
    keyboard = []
    # Navigatsiya tugmalari
    nav_row = []
    if current_page > 0:
        nav_row.append(InlineKeyboardButton(
            text="◀️ Oldingi",
            callback_data=f"admin_page_{obj_type}_{current_page - 1}"
        ))
    nav_row.append(InlineKeyboardButton(
        text=f"📄 {current_page + 1}/{total_pages}",
        callback_data="admin_noop"
    ))
    if current_page < total_pages - 1:
        nav_row.append(InlineKeyboardButton(
            text="Keyingi ▶️",
            callback_data=f"admin_page_{obj_type}_{current_page + 1}"
        ))

    keyboard.append(nav_row)
    keyboard.append([InlineKeyboardButton(text="🔙 Orqaga", callback_data="admin_menu")])

    return InlineKeyboardMarkup(inline_keyboard=keyboard)

# ============================================================================
# ASOSIY HANDLER'LAR
# ============================================================================
@router.message(F.text == "/admin")
async def admin_panel(message: Message, state: FSMContext):
    """Admin panelga kirish"""
    if not is_admin(message.from_user.id):
        await message.answer("⛔️ Sizda admin huquqlari yo'q!")
        logger.warning(f"Ruxsatsiz ulanish urinishi: user_id={message.from_user.id}")
        return
    await state.clear()
    await message.answer(
        "👨‍💼 <b>Admin panel</b>\n\n"
        "Kerakli bo'limni tanlang:",
        reply_markup=get_admin_menu(),
        parse_mode="HTML"
    )
    logger.info(f"Admin kirdi: user_id={message.from_user.id}")

# ============================================================================
# OBYEKT QO'SHISH
# ============================================================================
@router.callback_query(F.data == "admin_add")
async def start_add_object(callback: CallbackQuery, state: FSMContext):
    """Yangi obyekt qo'shishni boshlash"""
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔️ Ruxsat yo'q!", show_alert=True)
        return
    await state.clear()
    await state.set_state(AdminAddForm.type)
    await state.update_data(media=[])

    await callback.message.answer(
        "📋 <b>Yangi obyekt qo'shish</b>\n\n"
        "Obyekt turini tanlang:",
        reply_markup=get_type_keyboard(show_back=True),
        parse_mode="HTML"
    )
    await callback.answer()

@router.callback_query(F.data.in_({"admin_type_sale", "admin_type_rent"}))
async def process_object_type(callback: CallbackQuery, state: FSMContext):
    """Obyekt turini qayta ishlash"""
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔️ Ruxsat yo'q!", show_alert=True)
        return
    current_state = await state.get_state()

    # Agar state AdminAddForm.type bo'lsa - obyekt qo'shish jarayoni
    if current_state == AdminAddForm.type:
        if callback.data == "admin_type_sale":
            obj_type = "sale"
        else:
            obj_type = "rent"
        await state.update_data(type=obj_type)
        await state.set_state(AdminAddForm.mulk_turi)
        
        text = "💰 <b>Sotuv uchun mulk turini tanlang:</b>" if obj_type == "sale" else "🏠 <b>Ijara uchun mulk turini tanlang:</b>"
        
        await callback.message.answer(
            text,
            reply_markup=get_mulk_keyboard(obj_type),
            parse_mode="HTML"
        )
    # Agar state yo'q bo'lsa - ko'rish jarayoni
    else:
        if callback.data == "admin_type_sale":
            obj_type = "sale"
        else:
            obj_type = "rent"
        await show_objects_list(callback.message, obj_type, page=0)

    await callback.answer()

@router.callback_query(F.data.startswith("admin_mulk_"))
async def process_mulk_type(callback: CallbackQuery, state: FSMContext):
    """Mulk turini qayta ishlash"""
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔️ Ruxsat yo'q!", show_alert=True)
        return
    mulk_turi = callback.data.replace("admin_mulk_", "")
    await state.update_data(mulk_turi=mulk_turi)
    await state.set_state(AdminAddForm.viloyat)

    await callback.message.answer(
        "📍 <b>Viloyatni tanlang:</b>",
        reply_markup=get_viloyat_keyboard(),
        parse_mode="HTML"
    )
    await callback.answer()

@router.message(AdminAddForm.viloyat)
async def process_viloyat(message: Message, state: FSMContext):
    """Viloyatni qayta ishlash"""
    if not is_admin(message.from_user.id):
        return
    viloyat = message.text.strip()

    # Bekor qilish
    if viloyat == "🔙 Bekor qilish":
        await state.clear()
        await message.answer(
            "❌ Bekor qilindi.",
            reply_markup=ReplyKeyboardRemove()
        )
        await message.answer(
            "👨‍💼 <b>Admin panel</b>",
            reply_markup=get_admin_menu(),
            parse_mode="HTML"
        )
        return

    # Validatsiya
    if viloyat not in VILOYATLAR:
        await message.answer(
            "⚠️ Noto'g'ri viloyat. Iltimos, tugmalardan birini tanlang:",
            reply_markup=get_viloyat_keyboard()
        )
        return

    await state.update_data(viloyat=viloyat)
    await state.set_state(AdminAddForm.joylashuv_detail)

    await message.answer(
        "📍 <b>Batafsil joylashuvni kiriting:</b>\n\n"
        "Masalan: <i>Sergeli tumani, Yangi Sergeli 5-kvartal</i>",
        reply_markup=ReplyKeyboardRemove(),
        parse_mode="HTML"
    )

@router.message(AdminAddForm.joylashuv_detail)
async def process_joylashuv_detail(message: Message, state: FSMContext):
    """Batafsil joylashuvni qayta ishlash"""
    if not is_admin(message.from_user.id):
        return
    detail = message.text.strip()

    if not detail or len(detail) < 5:
        await message.answer(
            "⚠️ Joylashuv juda qisqa. Iltimos, batafsil kiriting:\n\n"
            "Masalan: <i>Sergeli tumani, Yangi Sergeli 5-kvartal</i>",
            parse_mode="HTML"
        )
        return

    data = await state.get_data()
    full_joylashuv = f"{data['viloyat']}, {detail}"
    await state.update_data(joylashuv=full_joylashuv)
    await state.set_state(AdminAddForm.narx)

    await message.answer(
        "💰 <b>Narxni kiriting:</b>\n\n"
        "Masalan:\n"
        "• <i>500 mln so'm</i>\n"
        "• <i>Oyiga 8 mln so'm</i>\n"
        "• <i>$100,000</i>",
        parse_mode="HTML"
    )

@router.message(AdminAddForm.narx)
async def process_narx(message: Message, state: FSMContext):
    """Narxni qayta ishlash"""
    if not is_admin(message.from_user.id):
        return
    narx = message.text.strip()

    if not narx or len(narx) < 2:
        await message.answer(
            "⚠️ Narx juda qisqa. Iltimos, to'g'ri narxni kiriting:",
        )
        return

    await state.update_data(narx=narx)
    await state.set_state(AdminAddForm.izoh)

    await message.answer(
        "📝 <b>Qo'shimcha izoh kiriting:</b>\n\n"
        "Agar izoh yo'q bo'lsa, <code>yo'q</code> deb yozing.",
        parse_mode="HTML"
    )

@router.message(AdminAddForm.izoh)
async def process_izoh(message: Message, state: FSMContext):
    """Izohni qayta ishlash"""
    if not is_admin(message.from_user.id):
        return
    izoh = message.text.strip()
    izoh = "" if izoh.lower() in ["yo'q", "yoq", "no", "-"] else izoh

    await state.update_data(izoh=izoh)
    await state.set_state(AdminAddForm.media)

    await message.answer(
        "📸 <b>Rasm yoki video yuboring</b>\n\n"
        "• Bir necha rasm/video yuborishingiz mumkin\n"
        "• Tugatgach <code>tugatdim</code> deb yozing\n"
        "• Media yo'q bo'lsa <code>yo'q</code> deb yozing",
        parse_mode="HTML"
    )

@router.message(AdminAddForm.media, F.photo)
async def process_photo(message: Message, state: FSMContext):
    """Rasmni qayta ishlash"""
    if not is_admin(message.from_user.id):
        return
    try:
        data = await state.get_data()
        media = data.get('media', [])
        media.append({'type': 'photo', 'file_id': message.photo[-1].file_id})
        await state.update_data(media=media)
        
        await message.answer(
            f"✅ Rasm qabul qilindi ({len(media)} ta)\n\n"
            "Yana yuboring yoki <code>tugatdim</code> deb yozing.",
            parse_mode="HTML"
        )
    except Exception as e:
        logger.error(f"Rasm qayta ishlashda xato: {e}")
        await message.answer("❌ Rasm yuklashda xato. Qaytadan urinib ko'ring.")

@router.message(AdminAddForm.media, F.video)
async def process_video(message: Message, state: FSMContext):
    """Videoni qayta ishlash"""
    if not is_admin(message.from_user.id):
        return
    try:
        data = await state.get_data()
        media = data.get('media', [])
        media.append({'type': 'video', 'file_id': message.video.file_id})
        await state.update_data(media=media)
        
        await message.answer(
            f"✅ Video qabul qilindi ({len(media)} ta)\n\n"
            "Yana yuboring yoki <code>tugatdim</code> deb yozing.",
            parse_mode="HTML"
        )
    except Exception as e:
        logger.error(f"Video qayta ishlashda xato: {e}")
        await message.answer("❌ Video yuklashda xato. Qaytadan urinib ko'ring.")

@router.message(AdminAddForm.media, F.text)
async def finish_media(message: Message, state: FSMContext):
    """Media to'plashni tugatish"""
    if not is_admin(message.from_user.id):
        return
    text = message.text.lower().strip()

    if text in {"yo'q", "yoq", "no", "-"}:
        await state.update_data(media=[])
    elif text in {"tugatdim", "tayyor", "tugadi", "ok"}:
        pass  # Media allaqachon saqlangan
    else:
        await message.answer(
            "⚠️ Iltimos:\n"
            "• Rasm/video yuboring\n"
            "• <code>tugatdim</code> deb yozing\n"
            "• <code>yo'q</code> deb yozing",
            parse_mode="HTML"
        )
        return

    # Tasdiqlash
    data = await state.get_data()
    media_count = len(data.get('media', []))
    obj_type = 'Sotuv' if data['type'] == 'sale' else 'Ijara'
    izoh_text = data['izoh'] or "Yo'q"

    preview = (
        "📋 <b>Obyekt ma'lumotlari:</b>\n\n"
        f"🏷 Turi: <b>{obj_type}</b>\n"
        f"🏠 Mulk: <b>{data['mulk_turi']}</b>\n"
        f"📍 Joylashuv: <b>{data['joylashuv']}</b>\n"
        f"💰 Narx: <b>{data['narx']}</b>\n"
        f"📝 Izoh: <i>{izoh_text}</i>\n"
        f"📸 Media: <b>{media_count} ta</b>\n\n"
        "Tasdiqlaysizmi?"
    )

    await state.set_state(AdminAddForm.confirm)
    await message.answer(
        preview,
        reply_markup=get_confirm_keyboard(),
        parse_mode="HTML"
    )

@router.callback_query(F.data == "admin_confirm_yes")
async def confirm_add_object(callback: CallbackQuery, state: FSMContext):
    """Obyekt qo'shishni tasdiqlash"""
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔️ Ruxsat yo'q!", show_alert=True)
        return
    try:
        data = await state.get_data()
        
        # Media ni string formatga o'tkazish
        media_str = format_media_list(data.get('media', []))
        
        # Ma'lumotlar bazasiga saqlash
        obj_data = {
            'type': data['type'],
            'mulk_turi': data['mulk_turi'],
            'joylashuv': data['joylashuv'],
            'narx': data['narx'],
            'izoh': data.get('izoh', ''),
            'media': media_str,  # ✅ BO'SHLIQSIZ!
            'viloyat': data.get('viloyat', '')
        }
        
        obj_id = db.insert_object(obj_data)  # ✅ Umumiy database dan foydalanish
        
        await callback.message.answer(
            f"✅ <b>Obyekt muvaffaqiyatli qo'shildi!</b>\n\n"
            f"🆔 ID: <code>{obj_id}</code>",
            parse_mode="HTML"
        )
        
        logger.info(f"Admin {callback.from_user.id} obyekt qo'shdi: ID={obj_id}")
        
    except Exception as e:
        logger.error(f"Obyekt qo'shishda xato: {e}")
        await callback.message.answer(
            "❌ Xatolik yuz berdi. Qaytadan urinib ko'ring."
        )

    await state.clear()
    await callback.message.answer(
        "👨‍💼 <b>Admin panel</b>",
        reply_markup=get_admin_menu(),
        parse_mode="HTML"
    )
    await callback.answer()

@router.callback_query(F.data == "admin_confirm_no")
async def cancel_add_object(callback: CallbackQuery, state: FSMContext):
    """Obyekt qo'shishni bekor qilish"""
    await state.clear()
    await callback.message.answer("❌ Bekor qilindi.")
    await callback.message.answer(
        "👨‍💼 Admin panel",
        reply_markup=get_admin_menu(),
        parse_mode="HTML"
    )
    await callback.answer()

# ============================================================================
# OBYEKTLARNI KO'RISH VA BOSHQARISH
# ============================================================================
async def show_objects_list(message: Message, obj_type: str, page: int = 0):
    """Obyektlar ro'yxatini ko'rsatish"""
    total_count = db.get_count(obj_type)
    obj_type_name = 'Sotuv' if obj_type == 'sale' else 'Ijara'
    if total_count == 0:
        await message.answer(
            f"📋 <b>{obj_type_name} obyektlari</b>\n\n"
            "Hozircha obyektlar yo'q.",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔙 Orqaga", callback_data="admin_menu")]
            ])
        )
        return

    total_pages = (total_count + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE
    objects = db.get_objects(obj_type, limit=ITEMS_PER_PAGE, offset=page * ITEMS_PER_PAGE)

    # Obyektlar ro'yxatini yaratish
    keyboard = []
    for obj in objects:
        text = f"🆔 {obj['id']} | {obj['mulk_turi']} | {obj['narx']}"
        keyboard.append([InlineKeyboardButton(
            text=text,
            callback_data=f"admin_obj_{obj['id']}"
        )])

    # Sahifalash tugmalari
    nav_row = []
    if page > 0:
        nav_row.append(InlineKeyboardButton(
            text="◀️ Oldingi",
            callback_data=f"admin_page_{obj_type}_{page - 1}"
        ))
    nav_row.append(InlineKeyboardButton(
        text=f"📄 {page + 1}/{total_pages}",
        callback_data="admin_noop"
    ))
    if page < total_pages - 1:
        nav_row.append(InlineKeyboardButton(
            text="Keyingi ▶️",
            callback_data=f"admin_page_{obj_type}_{page + 1}"
        ))

    keyboard.append(nav_row)
    keyboard.append([InlineKeyboardButton(text="🔙 Orqaga", callback_data="admin_menu")])

    await message.answer(
        f"📋 <b>{obj_type_name} obyektlari</b>\n\n"
        f"Jami: {total_count} ta\n"
        f"Sahifa: {page + 1}/{total_pages}",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard),
        parse_mode="HTML"
    )

@router.callback_query(F.data == "admin_view")
async def start_view_objects(callback: CallbackQuery):
    """Obyektlarni ko'rishni boshlash"""
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔️ Ruxsat yo'q!", show_alert=True)
        return
    await callback.message.answer(
        "📋 <b>Obyektlarni boshqarish</b>\n\n"
        "Qaysi bo'limni ko'rmoqchisiz?",
        reply_markup=get_type_keyboard(),
        parse_mode="HTML"
    )
    await callback.answer()

@router.callback_query(F.data.startswith("admin_page_"))
async def handle_pagination(callback: CallbackQuery):
    """Sahifalashni boshqarish"""
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔️ Ruxsat yo'q!", show_alert=True)
        return
    parts = callback.data.split("_")
    obj_type = parts[2]  # sale yoki rent
    page = int(parts[3])

    await callback.message.delete()
    await show_objects_list(callback.message, obj_type, page)
    await callback.answer()

@router.callback_query(F.data.startswith("admin_obj_"))
async def view_single_object(callback: CallbackQuery):
    """Bitta obyektni ko'rish"""
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔️ Ruxsat yo'q!", show_alert=True)
        return
    obj_id = int(callback.data.split("_")[-1])
    obj = db.get_object_by_id(obj_id)

    if not obj:
        await callback.answer("❌ Obyekt topilmadi!", show_alert=True)
        return

    text = format_object_info(obj)

    await callback.message.answer(
        text,
        reply_markup=get_object_actions_keyboard(obj_id),
        parse_mode="HTML"
    )
    await callback.answer()

# ============================================================================
# OBYEKTNI O'CHIRISH
# ============================================================================
@router.callback_query(F.data.startswith("admin_delete_"))
async def start_delete_object(callback: CallbackQuery, state: FSMContext):
    """Obyektni o'chirishni boshlash"""
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔️ Ruxsat yo'q!", show_alert=True)
        return
    obj_id = int(callback.data.split("_")[-1])
    obj = db.get_object_by_id(obj_id)

    if not obj:
        await callback.answer("❌ Obyekt topilmadi!", show_alert=True)
        return

    await state.update_data(delete_obj_id=obj_id)
    await state.set_state(AdminDeleteForm.confirm)

    await callback.message.answer(
        f"⚠️ <b>O'chirish tasdigi</b>\n\n"
        f"Siz ID {obj_id} obyektni o'chirmoqchisiz.\n\n"
        f"<b>Bu amalni qaytarib bo'lmaydi!</b>\n\n"
        f"Tasdiqlash uchun <code>ha</code> deb yozing\n"
        f"Bekor qilish uchun <code>yo'q</code> deb yozing",
        parse_mode="HTML"
    )
    await callback.answer()

@router.message(AdminDeleteForm.confirm)
async def confirm_delete_object(message: Message, state: FSMContext):
    """Obyektni o'chirishni tasdiqlash"""
    if not is_admin(message.from_user.id):
        return
    text = message.text.lower().strip()

    if text in ["ha", "yes", "tasdiqlash", "ok"]:
        data = await state.get_data()
        obj_id = data['delete_obj_id']
        
        if db.delete_object(obj_id):
            await message.answer(
                f"✅ Obyekt ID {obj_id} muvaffaqiyatli o'chirildi!",
                parse_mode="HTML"
            )
            logger.info(f"Admin {message.from_user.id} obyektni o'chirdi: ID={obj_id}")
        else:
            await message.answer("❌ Obyekt topilmadi yoki allaqachon o'chirilgan.")

    elif text in ["yo'q", "yoq", "no", "bekor"]:
        await message.answer("❌ Bekor qilindi.")

    else:
        await message.answer(
            "⚠️ Iltimos, <code>ha</code> yoki <code>yo'q</code> deb yozing.",
            parse_mode="HTML"
        )
        return

    await state.clear()
    await message.answer(
        "👨‍💼 <b>Admin panel</b>",
        reply_markup=get_admin_menu(),
        parse_mode="HTML"
    )

# ============================================================================
# STATISTIKA
# ============================================================================
@router.callback_query(F.data == "admin_stats")
async def show_statistics(callback: CallbackQuery):
    """Statistikani ko'rsatish"""
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔️ Ruxsat yo'q!", show_alert=True)
        return
    try:
        stats = db.get_statistics()
        
        text = (
            "📊 <b>Statistika</b>\n\n"
            f"📋 Jami obyektlar: <b>{stats['total']}</b>\n"
            f"💰 Sotuv: <b>{stats['sale']}</b>\n"
            f"🏠 Ijara: <b>{stats['rent']}</b>\n\n"
            f"📅 Hozirgi vaqt: {datetime.now().strftime('%d.%m.%Y %H:%M')}"
        )
        
        await callback.message.answer(
            text,
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔙 Orqaga", callback_data="admin_menu")]
            ])
        )
    except Exception as e:
        logger.error(f"Statistika olishda xato: {e}")
        await callback.message.answer("❌ Xatolik yuz berdi.")

    await callback.answer()

# ============================================================================
# BOSHQA HANDLER'LAR
# ============================================================================
@router.callback_query(F.data == "admin_menu")
async def back_to_menu(callback: CallbackQuery, state: FSMContext):
    """Asosiy menyuga qaytish"""
    await state.clear()
    await callback.message.answer(
        "👨‍💼 Admin panel\n\n"
        "Kerakli bo'limni tanlang:",
        reply_markup=get_admin_menu(),
        parse_mode="HTML"
    )
    await callback.answer()

@router.callback_query(F.data == "admin_close")
async def close_admin_panel(callback: CallbackQuery, state: FSMContext):
    """Admin panelni yopish"""
    await state.clear()
    await callback.message.delete()
    await callback.answer("👋 Admin panel yopildi")

@router.callback_query(F.data == "admin_noop")
async def noop_handler(callback: CallbackQuery):
    """Bo'sh handler (sahifalash uchun)"""
    await callback.answer()