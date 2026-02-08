"""
Ijaralar - IJARAGA OLISH Bo'limi
Professional refactored version
Funksiyalar:
Viloyat bo'yicha qidirish
Ijaradagi obyektlarni ko'rish (rasm/video bilan)
Ariza yuborish
Admin ga xabar yuborish
"""
import logging
import re
from typing import List, Dict, Optional
from aiogram import Router, F, Bot
from aiogram.types import (
    Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton,
    ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
)
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from dotenv import load_dotenv
from os import getenv
from handlers.database import db  # ✅ TO'G'RI IMPORT (handlers papkasidan)

# ============================================================================
# KONFIGURATSIYA
# ============================================================================
logger = logging.getLogger(__name__)
router = Router()
load_dotenv()
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
MULK_TYPES = {
    "🏢 Ko'p qavatli uyni ijaraga olish": "Ko'p qavatli uy",
    "🏡 Hovli ijaraga olish": "Hovli",
    "🏬 Savdo do'konini ijaraga olish": "Savdo do'koni",
    "🏨 Mehmonxona ijaraga olish": "Mehmonxona",
    "🔄 Boshqa ijara joylarini olish": "Boshqa ijara joyi"
}

# Sahifalash
ITEMS_PER_PAGE = 5

# ============================================================================
# FSM STATES
# ============================================================================
class SearchForm(StatesGroup):
    """Qidirish uchun holatlar"""
    viloyat = State()

class InterestForm(StatesGroup):
    """Ariza yuborish uchun holatlar"""
    obj_id = State()
    ism_familiya = State()
    telefon = State()

# ============================================================================
# YORDAMCHI FUNKSIYALAR
# ============================================================================
def parse_media_string(media_str: Optional[str]) -> List[Dict[str, str]]:
    """
    Media string ni parse qilish
    Format: 'photo:file_id,video:file_id' -> [{'type': 'photo', 'file_id': '...'}]
    """
    if not media_str:
        return []
    result = []
    for item in media_str.split(','):
        item = item.strip()
        if ':' in item:
            media_type, file_id = item.split(':', 1)
            result.append({
                'type': media_type.strip(),
                'file_id': file_id.strip()
            })
    return result

def validate_phone(phone: str) -> bool:
    """
    Telefon raqamini tekshirish
    Format: +998901234567 (12 ta belgi)
    """
    phone = phone.strip().replace(' ', '').replace('-', '')
    pattern = r'^\+998\d{9}$'
    return bool(re.match(pattern, phone))

def format_phone(phone: str) -> str:
    """Telefon raqamini formatlash"""
    phone = phone.strip().replace(' ', '').replace('-', '')
    if not phone.startswith('+'):
        phone = '+' + phone
    return phone

def format_object_preview(obj: Dict) -> str:
    """Obyekt preview formatlash (ro'yxat uchun)"""
    narx = obj['narx'][:30] + '...' if len(obj['narx']) > 30 else obj['narx']
    joylashuv = obj['joylashuv'][:35] + '...' if len(obj['joylashuv']) > 35 else obj['joylashuv']
    return f"💰 {narx}\n📍 {joylashuv}"

def format_object_detail(obj: Dict) -> str:
    """Obyekt batafsil formatlash"""
    izoh_text = obj['izoh'] if obj['izoh'] else "Qo'shimcha ma'lumot yo'q"
    return (
        f"🏠 <b>{obj['mulk_turi']}</b>\n\n"
        f"📍 <b>Joylashuv:</b> {obj['joylashuv']}\n"
        f"💰 <b>Narx:</b> {obj['narx']}\n\n"
        f"📝 <b>Izoh:</b>\n{izoh_text}"
    )

# ============================================================================
# KEYBOARD (TUGMALAR)
# ============================================================================
def get_viloyat_keyboard() -> ReplyKeyboardMarkup:
    """Viloyat tanlash tugmalari"""
    keyboard = [[KeyboardButton(text=v)] for v in VILOYATLAR]
    keyboard.append([KeyboardButton(text="🌍 Barcha viloyatlar")])
    keyboard.append([KeyboardButton(text="🔙 Orqaga")])
    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True,
        input_field_placeholder="Viloyatni tanlang..."
    )

def get_contact_keyboard() -> ReplyKeyboardMarkup:
    """Kontakt ulashish tugmasi"""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📞 Telefonni ulashish", request_contact=True)],
            [KeyboardButton(text="🔙 Bekor qilish")]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )

def get_objects_keyboard(objects: List[Dict], page: int = 0) -> InlineKeyboardMarkup:
    """Obyektlar ro'yxati tugmalari"""
    keyboard = []
    start = page * ITEMS_PER_PAGE
    end = start + ITEMS_PER_PAGE
    page_objects = objects[start:end]

    for obj in page_objects:
        preview = format_object_preview(obj)
        keyboard.append([InlineKeyboardButton(
            text=preview,
            callback_data=f"rent_view_{obj['id']}"
        )])

    # Navigatsiya
    nav_row = []
    total_pages = (len(objects) + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE

    if page > 0:
        nav_row.append(InlineKeyboardButton(
            text="◀️ Oldingi",
            callback_data=f"rent_page_{page - 1}"
        ))

    if total_pages > 1:
        nav_row.append(InlineKeyboardButton(
            text=f"📄 {page + 1}/{total_pages}",
            callback_data="rent_noop"
        ))

    if page < total_pages - 1:
        nav_row.append(InlineKeyboardButton(
            text="Keyingi ▶️",
            callback_data=f"rent_page_{page + 1}"
        ))

    if nav_row:
        keyboard.append(nav_row)

    keyboard.append([InlineKeyboardButton(
        text="🔙 Orqaga",
        callback_data="back_to_ijara"
    )])

    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_object_detail_keyboard(obj_id: int) -> InlineKeyboardMarkup:
    """Obyekt batafsil ko'rish tugmalari"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="✅ Qiziqtirdi! Ariza yuborish",
            callback_data=f"rent_interest_{obj_id}"
        )],
        [InlineKeyboardButton(
            text="🔙 Orqaga",
            callback_data="rent_back_to_list"
        )]
    ])

# ============================================================================
# HANDLER'LAR - QIDIRISH BOSHLASH
# ============================================================================
@router.message(F.text.in_(MULK_TYPES.keys()))
async def start_search(message: Message, state: FSMContext):
    """
    Mulk turini tanlash va viloyat so'rash
    """
    mulk_turi = MULK_TYPES[message.text]
    await state.clear()
    await state.update_data(mulk_turi=mulk_turi)
    await state.set_state(SearchForm.viloyat)

    await message.answer(
        f"🏠 <b>{mulk_turi} - Ijaraga olish</b>\n\n"
        "📍 Qaysi viloyatda qidiramiz?\n\n"
        "💡 <i>Yoki \"Barcha viloyatlar\" tugmasini bosing</i>",
        reply_markup=get_viloyat_keyboard(),
        parse_mode="HTML"
    )

# ============================================================================
# HANDLER'LAR - VILOYAT TANLASH
# ============================================================================
@router.message(SearchForm.viloyat)
async def process_viloyat(message: Message, state: FSMContext):
    """
    Viloyatni qabul qilish va obyektlarni ko'rsatish
    """
    viloyat_input = message.text.strip()
    # Orqaga qaytish
    if viloyat_input == "🔙 Orqaga":
        await state.clear()
        from handlers.common import ijara_menu
        await message.answer(
            "Ijara bo'limiga qaytdingiz:",
            reply_markup=ijara_menu
        )
        return

    data = await state.get_data()
    mulk_turi = data.get('mulk_turi')

    # Viloyatni aniqlash
    viloyat = None
    if viloyat_input == "🌍 Barcha viloyatlar":
        viloyat = None
    elif viloyat_input in VILOYATLAR:
        viloyat = viloyat_input
    else:
        await message.answer(
            "⚠️ Noto'g'ri viloyat!\n\n"
            "Iltimos, tugmalardan birini tanlang:",
            reply_markup=get_viloyat_keyboard()
        )
        return

    # Obyektlarni qidirish ✅ TYPE='RENT' BILAN!
    try:
        objects = db.search_objects('rent', mulk_turi, viloyat) 

        
        if not objects:
            viloyat_name = viloyat if viloyat else "hech qaysi viloyatda"
            await message.answer(
                f"😔 <b>Afsuski, {viloyat_name} {mulk_turi.lower()} "
                f"ijaraga beruvchi yo'q</b>\n\n"
                "💡 Boshqa viloyatni sinab ko'ring yoki keyinroq qaytib ko'ring!",
                reply_markup=ReplyKeyboardRemove(),
                parse_mode="HTML"
            )
            await state.clear()
            return
        
        # Obyektlarni saqlash (pagination uchun)
        await state.update_data(objects=objects, current_page=0, viloyat=viloyat)
        
        viloyat_text = viloyat if viloyat else "barcha viloyatlarda"
        await message.answer(
            f"🏠 <b>{mulk_turi}</b>\n"
            f"📍 <b>Joy:</b> {viloyat_text}\n"
            f"📊 <b>Topildi:</b> {len(objects)} ta\n\n"
            "Quyidagilardan birini tanlang:",
            reply_markup=get_objects_keyboard(objects, page=0),
            parse_mode="HTML"
        )
        
        # Klaviaturani olib tashlash
        await message.answer(
            "👆 Yuqoridagi tugmalardan birini tanlang",
            reply_markup=ReplyKeyboardRemove()
        )
        
    except Exception as e:
        logger.error(f"Obyektlarni qidirishda xato: {e}")
        await message.answer(
            "❌ Xatolik yuz berdi. Iltimos, qaytadan urinib ko'ring.",
            reply_markup=ReplyKeyboardRemove()
        )
        await state.clear()

# ============================================================================
# HANDLER'LAR - SAHIFALASH
# ============================================================================
@router.callback_query(F.data.startswith("rent_page_"))
async def handle_pagination(callback: CallbackQuery, state: FSMContext):
    """Sahifalash"""
    page = int(callback.data.split("_")[-1])
    data = await state.get_data()
    objects = data.get('objects', [])
    
    if not objects:
        await callback.answer("❌ Obyektlar topilmadi")
        return

    await state.update_data(current_page=page)

    viloyat = data.get('viloyat')
    mulk_turi = data.get('mulk_turi')
    viloyat_text = viloyat if viloyat else "barcha viloyatlarda"

    try:
        await callback.message.edit_text(
            f"🏠 <b>{mulk_turi}</b>\n"
            f"📍 <b>Joy:</b> {viloyat_text}\n"
            f"📊 <b>Topildi:</b> {len(objects)} ta\n\n"
            "Quyidagilardan birini tanlang:",
            reply_markup=get_objects_keyboard(objects, page=page),
            parse_mode="HTML"
        )
    except Exception:
        # Message not modified - ignore
        pass

    await callback.answer()

# ============================================================================
# HANDLER'LAR - OBYEKT BATAFSIL
# ============================================================================
@router.callback_query(F.data.startswith("rent_view_"))
async def view_object_detail(callback: CallbackQuery, state: FSMContext, bot: Bot):
    """
    Obyektni batafsil ko'rish (media bilan)
    """
    obj_id = int(callback.data.split("_")[-1])
    
    try:
        obj = db.get_object_by_id(obj_id)
        
        if not obj:
            await callback.answer("❌ Obyekt topilmadi", show_alert=True)
            return
        
        # Ma'lumotlarni formatlash
        text = format_object_detail(obj)
        
        # Media ni yuborish
        media_list = parse_media_string(obj.get('media'))
        
        if media_list:
            # Birinchi media ni asosiy sifatida yuborish
            first_media = media_list[0]
            
            try:
                if first_media['type'] == 'photo':
                    await callback.message.answer_photo(
                        photo=first_media['file_id'],
                        caption=text,
                        parse_mode="HTML"
                    )
                elif first_media['type'] == 'video':
                    await callback.message.answer_video(
                        video=first_media['file_id'],
                        caption=text,
                        parse_mode="HTML"
                    )
                else:
                    # Noma'lum tur - matn sifatida yuborish
                    await callback.message.answer(text, parse_mode="HTML")
                
                # Qolgan medialani alohida yuborish
                for media in media_list[1:]:
                    try:
                        if media['type'] == 'photo':
                            await callback.message.answer_photo(photo=media['file_id'])
                        elif media['type'] == 'video':
                            await callback.message.answer_video(video=media['file_id'])
                    except Exception as e:
                        logger.error(f"Qo'shimcha media yuborishda xato: {e}")
                        
            except Exception as e:
                logger.error(f"Media yuborishda xato: {e}")
                await callback.message.answer(
                    text + "\n\n⚠️ <i>Rasm yoki video yuklanmadi</i>",
                    parse_mode="HTML"
                )
        else:
            # Media yo'q - faqat matn
            await callback.message.answer(text, parse_mode="HTML")
        
        # Amal tugmalari
        await callback.message.answer(
            "Nima qilmoqchisiz?",
            reply_markup=get_object_detail_keyboard(obj_id)
        )
        
        await state.update_data(current_object_id=obj_id)
        
    except Exception as e:
        logger.error(f"Obyektni ko'rishda xato: {e}")
        await callback.answer("❌ Xatolik yuz berdi", show_alert=True)

    await callback.answer()

@router.callback_query(F.data == "rent_back_to_list")
async def back_to_objects_list(callback: CallbackQuery, state: FSMContext):
    """Obyektlar ro'yxatiga qaytish"""
    data = await state.get_data()
    objects = data.get('objects', [])
    page = data.get('current_page', 0)
    
    if not objects:
        await callback.answer("❌ Obyektlar topilmadi")
        return

    viloyat = data.get('viloyat')
    mulk_turi = data.get('mulk_turi')
    viloyat_text = viloyat if viloyat else "barcha viloyatlarda"

    await callback.message.answer(
        f"🏠 <b>{mulk_turi}</b>\n"
        f"📍 <b>Joy:</b> {viloyat_text}\n"
        f"📊 <b>Topildi:</b> {len(objects)} ta\n\n"
        "Quyidagilardan birini tanlang:",
        reply_markup=get_objects_keyboard(objects, page=page),
        parse_mode="HTML"
    )

    await callback.answer()

# ============================================================================
# HANDLER'LAR - ARIZA YUBORISH
# ============================================================================
@router.callback_query(F.data.startswith("rent_interest_"))
async def start_interest_form(callback: CallbackQuery, state: FSMContext):
    """Ariza yuborishni boshlash - ism so'rash"""
    obj_id = int(callback.data.split("_")[-1])
    await state.update_data(interest_obj_id=obj_id)
    await state.set_state(InterestForm.ism_familiya)

    await callback.message.answer(
        "👤 <b>Ism va familiyangizni kiriting:</b>\n\n"
        "Masalan: <i>Akmal Toshmatov</i>",
        parse_mode="HTML"
    )

    await callback.answer()

@router.message(InterestForm.ism_familiya)
async def process_interest_name(message: Message, state: FSMContext):
    """Ism-familiyani qabul qilish"""
    ism_familiya = message.text.strip()
    
    if not ism_familiya or len(ism_familiya) < 3:
        await message.answer(
            "⚠️ Ism va familiya juda qisqa!\n\n"
            "Iltimos, to'liq ism va familiyangizni kiriting:"
        )
        return

    await state.update_data(interest_ism_familiya=ism_familiya)
    await state.set_state(InterestForm.telefon)

    await message.answer(
        "📞 <b>Telefon raqamingizni kiriting:</b>\n\n"
        "Format: <code>+998901234567</code>\n\n"
        "Yoki quyidagi tugmani bosing:",
        reply_markup=get_contact_keyboard(),
        parse_mode="HTML"
    )

@router.message(InterestForm.telefon, F.contact)
async def process_interest_contact(message: Message, state: FSMContext, bot: Bot):
    """Telefon kontakt orqali qabul qilish"""
    phone = message.contact.phone_number
    phone = format_phone(phone)
    
    if not validate_phone(phone):
        await message.answer(
            "⚠️ Telefon raqami noto'g'ri!\n\n"
            "Format: <code>+998901234567</code>\n\n"
            "Qaytadan kiriting yoki tugmani bosing:",
            reply_markup=get_contact_keyboard(),
            parse_mode="HTML"
        )
        return

    await state.update_data(interest_telefon=phone)
    await send_interest_to_admin(message, state, bot)

@router.message(InterestForm.telefon)
async def process_interest_phone_text(message: Message, state: FSMContext, bot: Bot):
    """Telefon matn orqali qabul qilish"""
    # Bekor qilish
    if message.text == "🔙 Bekor qilish":
        await state.clear()
        await message.answer(
            "❌ Bekor qilindi.",
            reply_markup=ReplyKeyboardRemove()
        )
        from handlers.common import ijara_menu
        await message.answer(
            "Ijara bo'limiga qaytdingiz:",
            reply_markup=ijara_menu
        )
        return
    
    phone = format_phone(message.text)

    if not validate_phone(phone):
        await message.answer(
            "⚠️ Telefon raqami noto'g'ri!\n\n"
            "Format: <code>+998901234567</code>\n\n"
            "Qaytadan kiriting yoki tugmani bosing:",
            reply_markup=get_contact_keyboard(),
            parse_mode="HTML"
        )
        return

    await state.update_data(interest_telefon=phone)
    await send_interest_to_admin(message, state, bot)

async def send_interest_to_admin(message: Message, state: FSMContext, bot: Bot):
    """Admin ga arizani yuborish"""
    try:
        data = await state.get_data()
        obj_id = data['interest_obj_id']
        ism_familiya = data['interest_ism_familiya']
        telefon = data['interest_telefon']
        user_id = message.from_user.id
        username = message.from_user.username or "yo'q"

        # Obyekt ma'lumotlarini olish
        obj = db.get_object_by_id(obj_id)
        
        if obj:
            text = (
                "🔔 <b>YANGI MIJOZ QIZIQISHI (IJARA)</b>\n"
                "━━━━━━━━━━━━━━━━━━━\n\n"
                f"📋 <b>Obyekt ID:</b> {obj_id}\n"
                f"🏠 <b>Mulk:</b> {obj['mulk_turi']}\n"
                f"📍 <b>Joylashuv:</b> {obj['joylashuv']}\n"
                f"💰 <b>Narx:</b> {obj['narx']}\n\n"
                "👤 <b>MIJOZ MA'LUMOTLARI:</b>\n"
                f"• Ism: {ism_familiya}\n"
                f"• Telefon: {telefon}\n"
                f"• User ID: <code>{user_id}</code>\n"
                f"• Username: @{username}\n\n"
                "━━━━━━━━━━━━━━━━━━━"
            )
        else:
            text = (
                "🔔 <b>YANGI MIJOZ QIZIQISHI (IJARA)</b>\n"
                "━━━━━━━━━━━━━━━━━━━\n\n"
                f"📋 <b>Obyekt ID:</b> {obj_id}\n\n"
                "👤 <b>MIJOZ MA'LUMOTLARI:</b>\n"
                f"• Ism: {ism_familiya}\n"
                f"• Telefon: {telefon}\n"
                f"• User ID: <code>{user_id}</code>\n"
                f"• Username: @{username}\n\n"
                "━━━━━━━━━━━━━━━━━━━"
            )
        
        await bot.send_message(
            ADMIN_CHAT_ID,
            text,
            parse_mode="HTML"
        )
        
        await message.answer(
            "✅ <b>Arizangiz yuborildi!</b>\n\n"
            "Admin tez orada siz bilan bog'lanadi.\n"
            f"Telefon: <code>{telefon}</code>",
            reply_markup=ReplyKeyboardRemove(),
            parse_mode="HTML"
        )
        
        logger.info(f"Mijoz qiziqishi yuborildi (ijara): user_id={user_id}, obj_id={obj_id}")
        
        await state.clear()
        
        # Asosiy menyuga qaytish
        from handlers.common import main_menu
        await message.answer(
            "Asosiy menyuga qaytdingiz:",
            reply_markup=main_menu
        )
        
    except Exception as e:
        logger.error(f"Arizani yuborishda xato: {e}")
        await message.answer(
            "❌ Xatolik yuz berdi. Iltimos, qaytadan urinib ko'ring.",
            reply_markup=ReplyKeyboardRemove()
        )
        await state.clear()

# ============================================================================
# BOSHQA HANDLER'LAR
# ============================================================================
@router.callback_query(F.data == "back_to_ijara")
async def back_to_ijara_menu(callback: CallbackQuery, state: FSMContext):
    """Ijara menyusiga qaytish"""
    await state.clear()
    from handlers.common import ijara_menu
    await callback.message.answer(
        "Ijara bo'limiga qaytdingiz:",
        reply_markup=ijara_menu
    )
    await callback.answer()

@router.callback_query(F.data == "rent_noop")
async def noop_handler(callback: CallbackQuery):
    """Bo'sh handler (sahifalash uchun)"""
    await callback.answer()