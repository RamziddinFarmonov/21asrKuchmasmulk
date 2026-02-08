"""
Ko'chmas Mulk - SOTISH Bo'limi
Professional refactored version
Funksiyalar:
Foydalanuvchi mulkini sotish uchun ariza yuborish
Media (rasm/video) yuklash
Viloyat avtomatik aniqlash
Admin ga to'liq ma'lumot yuborish
"""
import logging
import re
from typing import List, Dict
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

# O'zbekiston viloyatlari (bo'shliqsiz)
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

# Mulk turlari (bo'shliqsiz)
MULK_TYPES = {
    "🏢 Ko'p qavatli uy sotish": "Ko'p qavatli uy",
    "🏡 Hovli sotish": "Hovli",
    "🏬 Savdo do'konini sotish": "Savdo do'koni",
    "🗺 Yer uchastkasini sotish": "Yer uchastkasi"
}

# ============================================================================
# FSM STATES
# ============================================================================
class SellForm(StatesGroup):
    """Sotish uchun holatlar"""
    ism_familiya = State()
    viloyat = State()
    joylashuv_detail = State()
    telefon = State()
    maydon = State()
    narx = State()
    izoh = State()
    media = State()
    confirm = State()

# ============================================================================
# YORDAMCHI FUNKSIYALAR
# ============================================================================
def validate_phone(phone: str) -> bool:
    """Telefon raqamini tekshirish (+998901234567 formatida)"""
    phone = phone.strip().replace(' ', '').replace('-', '')
    pattern = r'^\+998\d{9}$'
    return bool(re.match(pattern, phone))

def format_phone(phone: str) -> str:
    """Telefon raqamini formatlash"""
    phone = phone.strip().replace(' ', '').replace('-', '')
    if not phone.startswith('+'):
        phone = '+' + phone
    return phone

def format_media_list(media_list: List[Dict[str, str]]) -> str:
    """
    Media ro'yxatini DB uchun string formatga o'tkazish
    Format: 'photo:file_id,video:file_id'
    """
    if not media_list:
        return ""
    return ','.join([f"{m['type']}:{m['file_id']}" for m in media_list])

# ============================================================================
# KEYBOARD (TUGMALAR)
# ============================================================================
def get_viloyat_keyboard() -> ReplyKeyboardMarkup:
    """Viloyat tanlash tugmalari"""
    keyboard = [[KeyboardButton(text=v)] for v in VILOYATLAR]
    keyboard.append([KeyboardButton(text="🔙 Bekor qilish")])
    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True,
        input_field_placeholder="Viloyatingizni tanlang..."
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

def get_confirm_keyboard() -> InlineKeyboardMarkup:
    """Tasdiqlash tugmalari"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Tasdiqlash", callback_data="sell_confirm_yes"),
            InlineKeyboardButton(text="❌ Bekor qilish", callback_data="sell_confirm_no")
        ]
    ])

# ============================================================================
# HANDLER'LAR - FORMA BOSHLASH
# ============================================================================
@router.message(F.text.in_(MULK_TYPES.keys()))
async def start_sell_form(message: Message, state: FSMContext):
    """Sotish formasini boshlash"""
    mulk_turi = MULK_TYPES[message.text]
    await state.clear()
    await state.update_data(mulk_turi=mulk_turi, media=[])
    await state.set_state(SellForm.ism_familiya)

    await message.answer(
        f"🏠 <b>{mulk_turi} - Sotish</b>\n\n"
        "Quyidagi ma'lumotlarni to'ldiring:\n\n"
        "👤 <b>Ism va familiyangizni kiriting:</b>\n\n"
        "Masalan: <i>Akmal Toshmatov</i>",
        parse_mode="HTML"
    )

# ============================================================================
# HANDLER'LAR - ISM FAMILIYA
# ============================================================================
@router.message(SellForm.ism_familiya)
async def process_name(message: Message, state: FSMContext):
    """Ism-familiyani qabul qilish"""
    ism_familiya = message.text.strip()
    if not ism_familiya or len(ism_familiya) < 3:
        await message.answer(
            "⚠️ Ism va familiya juda qisqa!\n\n"
            "Iltimos, to'liq ism va familiyangizni kiriting:"
        )
        return

    await state.update_data(ism_familiya=ism_familiya)
    await state.set_state(SellForm.viloyat)

    await message.answer(
        "📍 <b>Viloyatingizni tanlang:</b>",
        reply_markup=get_viloyat_keyboard(),
        parse_mode="HTML"
    )

# ============================================================================
# HANDLER'LAR - VILOYAT
# ============================================================================
@router.message(SellForm.viloyat)
async def process_viloyat(message: Message, state: FSMContext):
    """Viloyatni qabul qilish"""
    viloyat = message.text.strip()
    # Bekor qilish
    if viloyat == "🔙 Bekor qilish":
        await state.clear()
        await message.answer(
            "❌ Bekor qilindi.",
            reply_markup=ReplyKeyboardRemove()
        )
        from handlers.common import kochmas_menu
        await message.answer(
            "Ko'chmas mulk bo'limiga qaytdingiz:",
            reply_markup=kochmas_menu
        )
        return

    # Validatsiya
    if viloyat not in VILOYATLAR:
        await message.answer(
            "⚠️ Noto'g'ri viloyat!\n\n"
            "Iltimos, tugmalardan birini tanlang:",
            reply_markup=get_viloyat_keyboard()
        )
        return

    await state.update_data(viloyat=viloyat)
    await state.set_state(SellForm.joylashuv_detail)

    await message.answer(
        "📍 <b>Batafsil manzilni kiriting:</b>\n\n"
        "Masalan: <i>Yunusobod tumani, 5-kvartal, 12-uy</i>",
        reply_markup=ReplyKeyboardRemove(),
        parse_mode="HTML"
    )

# ============================================================================
# HANDLER'LAR - JOYLASHUV
# ============================================================================
@router.message(SellForm.joylashuv_detail)
async def process_joylashuv(message: Message, state: FSMContext):
    """Batafsil joylashuvni qabul qilish"""
    detail = message.text.strip()
    if not detail or len(detail) < 5:
        await message.answer(
            "⚠️ Manzil juda qisqa!\n\n"
            "Iltimos, batafsil manzilni kiriting:\n"
            "Masalan: <i>Yunusobod tumani, 5-kvartal, 12-uy</i>",
            parse_mode="HTML"
        )
        return

    data = await state.get_data()
    full_joylashuv = f"{data['viloyat']}, {detail}"
    await state.update_data(joylashuv=full_joylashuv)
    await state.set_state(SellForm.telefon)

    await message.answer(
        "📞 <b>Telefon raqamingizni kiriting:</b>\n\n"
        "Format: <code>+998901234567</code>\n\n"
        "Yoki quyidagi tugmani bosing:",
        reply_markup=get_contact_keyboard(),
        parse_mode="HTML"
    )

# ============================================================================
# HANDLER'LAR - TELEFON
# ============================================================================
@router.message(SellForm.telefon, F.contact)
async def process_phone_contact(message: Message, state: FSMContext):
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

    await state.update_data(telefon=phone)
    await state.set_state(SellForm.maydon)

    await message.answer(
        "📏 <b>Mulk maydonini kiriting:</b>\n\n"
        "Masalan:\n"
        "• <i>100 kv.m</i>\n"
        "• <i>6 sotix</i>\n"
        "• <i>2.5 gektar</i>",
        reply_markup=ReplyKeyboardRemove(),
        parse_mode="HTML"
    )

@router.message(SellForm.telefon)
async def process_phone_text(message: Message, state: FSMContext):
    """Telefon matn orqali qabul qilish"""
    # Bekor qilish
    if message.text == "🔙 Bekor qilish":
        await state.clear()
        await message.answer(
            "❌ Bekor qilindi.",
            reply_markup=ReplyKeyboardRemove()
        )
        from handlers.common import kochmas_menu
        await message.answer(
            "Ko'chmas mulk bo'limiga qaytdingiz:",
            reply_markup=kochmas_menu
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

    await state.update_data(telefon=phone)
    await state.set_state(SellForm.maydon)

    await message.answer(
        "📏 <b>Mulk maydonini kiriting:</b>\n\n"
        "Masalan:\n"
        "• <i>100 kv.m</i>\n"
        "• <i>6 sotix</i>\n"
        "• <i>2.5 gektar</i>",
        reply_markup=ReplyKeyboardRemove(),
        parse_mode="HTML"
    )

# ============================================================================
# HANDLER'LAR - MAYDON
# ============================================================================
@router.message(SellForm.maydon)
async def process_maydon(message: Message, state: FSMContext):
    """Maydonni qabul qilish"""
    maydon = message.text.strip()
    if not maydon or len(maydon) < 2:
        await message.answer(
            "⚠️ Maydon juda qisqa!\n\n"
            "Iltimos, to'g'ri maydonni kiriting:"
        )
        return

    await state.update_data(maydon=maydon)
    await state.set_state(SellForm.narx)

    await message.answer(
        "💰 <b>Narxni kiriting:</b>\n\n"
        "Masalan:\n"
        "• <i>500 mln so'm</i>\n"
        "• <i>$100,000</i>\n"
        "• <i>Kelishiladi</i>",
        parse_mode="HTML"
    )

# ============================================================================
# HANDLER'LAR - NARX
# ============================================================================
@router.message(SellForm.narx)
async def process_narx(message: Message, state: FSMContext):
    """Narxni qabul qilish"""
    narx = message.text.strip()
    if not narx or len(narx) < 2:
        await message.answer(
            "⚠️ Narx juda qisqa!\n\n"
            "Iltimos, to'g'ri narxni kiriting:"
        )
        return

    await state.update_data(narx=narx)
    await state.set_state(SellForm.izoh)

    await message.answer(
        "📝 <b>Qo'shimcha izoh kiriting:</b>\n\n"
        "Masalan:\n"
        "• <i>Yangi ta'mirlangan</i>\n"
        "• <i>Hujjatlari tayyor</i>\n"
        "• <i>Yaqinida maktab va bozor bor</i>\n\n"
        "Agar izoh yo'q bo'lsa, <code>yo'q</code> deb yozing:",
        parse_mode="HTML"
    )

# ============================================================================
# HANDLER'LAR - IZOH
# ============================================================================
@router.message(SellForm.izoh)
async def process_izoh(message: Message, state: FSMContext):
    """Izohni qabul qilish"""
    izoh_text = message.text.strip()
    izoh = "" if izoh_text.lower() in ["yo'q", "yoq", "no", "-"] else izoh_text
    await state.update_data(izoh=izoh)
    await state.set_state(SellForm.media)

    await message.answer(
        "📸 <b>Mulk rasmini yoki videosini yuboring</b>\n\n"
        "• Bir necha rasm/video yuborishingiz mumkin\n"
        "• Tugatgach <code>tugatdim</code> deb yozing\n"
        "• Media yo'q bo'lsa <code>yo'q</code> deb yozing",
        parse_mode="HTML"
    )

# ============================================================================
# HANDLER'LAR - MEDIA
# ============================================================================
@router.message(SellForm.media, F.photo)
async def process_photo(message: Message, state: FSMContext):
    """Rasmni qabul qilish"""
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
        logger.error(f"Rasm qabul qilishda xato: {e}")
        await message.answer("❌ Rasm yuklashda xato. Qaytadan urinib ko'ring.")

@router.message(SellForm.media, F.video)
async def process_video(message: Message, state: FSMContext):
    """Videoni qabul qilish"""
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
        logger.error(f"Video qabul qilishda xato: {e}")
        await message.answer("❌ Video yuklashda xato. Qaytadan urinib ko'ring.")

@router.message(SellForm.media, F.text)
async def finish_media(message: Message, state: FSMContext):
    """Media to'plashni tugatish"""
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

    # Ma'lumotlarni ko'rsatish va tasdiqlash
    data = await state.get_data()
    media_count = len(data.get('media', []))
    izoh_text = data['izoh'] or "Yo'q"

    preview = (
        "📋 <b>MA'LUMOTLARINGIZ:</b>\n"
        "━━━━━━━━━━━━━━━━━━━\n\n"
        f"👤 <b>Ism:</b> {data['ism_familiya']}\n"
        f"🏠 <b>Mulk:</b> {data['mulk_turi']}\n"
        f"📍 <b>Joylashuv:</b> {data['joylashuv']}\n"
        f"📞 <b>Telefon:</b> {data['telefon']}\n"
        f"📏 <b>Maydon:</b> {data['maydon']}\n"
        f"💰 <b>Narx:</b> {data['narx']}\n"
        f"📝 <b>Izoh:</b> {izoh_text}\n"
        f"📸 <b>Media:</b> {media_count} ta\n\n"
        "━━━━━━━━━━━━━━━━━━━\n\n"
        "Tasdiqlaysizmi?"
    )

    await state.set_state(SellForm.confirm)
    await message.answer(
        preview,
        reply_markup=get_confirm_keyboard(),
        parse_mode="HTML"
    )

# ============================================================================
# HANDLER'LAR - TASDIQLASH
# ============================================================================
@router.callback_query(F.data == "sell_confirm_yes")
async def confirm_sell(callback: CallbackQuery, state: FSMContext, bot: Bot):
    """Arizani tasdiqlash va yuborish"""
    try:
        data = await state.get_data()
        # Media ni string formatga o'tkazish
        media_str = format_media_list(data.get('media', []))
        
        # Ma'lumotlar bazasiga saqlash (type='sale' bilan!)
        obj_data = {
            'type': 'sale',  # ✅ MUHIM: Faqat sotuv obyekti
            'mulk_turi': data['mulk_turi'],
            'joylashuv': data['joylashuv'],
            'narx': data['narx'],
            'izoh': data.get('izoh', ''),
            'media': media_str,
            'viloyat': data.get('viloyat', '')
        }
        
        obj_id = db.insert_object(obj_data)  # ✅ Umumiy database dan foydalanish
        
        # Admin ga yuborish
        await send_to_admin(bot, data, obj_id)
        
        await callback.message.edit_text(
            "✅ <b>Arizangiz muvaffaqiyatli yuborildi!</b>\n\n"
            f"🆔 Ariza ID: <code>{obj_id}</code>\n\n"
            "Admin tez orada siz bilan bog'lanadi.",
            parse_mode="HTML"
        )
        
        logger.info(f"Sotish arizasi qabul qilindi: user_id={callback.from_user.id}, obj_id={obj_id}")
        
        await state.clear()
        
        # Asosiy menyuga qaytish
        from handlers.common import main_menu
        await callback.message.answer(
            "Asosiy menyuga qaytdingiz:",
            reply_markup=main_menu
        )
        
    except Exception as e:
        logger.error(f"Arizani tasdiqlashda xato: {e}")
        await callback.message.edit_text(
            "❌ Xatolik yuz berdi. Iltimos, qaytadan urinib ko'ring."
        )

    await callback.answer()

@router.callback_query(F.data == "sell_confirm_no")
async def cancel_sell(callback: CallbackQuery, state: FSMContext):
    """Arizani bekor qilish"""
    await state.clear()
    await callback.message.edit_text("❌ Ariza bekor qilindi.")
    from handlers.common import main_menu
    await callback.message.answer(
        "Asosiy menyuga qaytdingiz:",
        reply_markup=main_menu
    )
    await callback.answer()

# ============================================================================
# ADMIN GA YUBORISH
# ============================================================================
async def send_to_admin(bot: Bot, data: Dict, obj_id: int):
    """
    Admin ga to'liq ma'lumot yuborish (media bilan)
    """
    try:
        # Matn xabari
        izoh_text = data.get('izoh', '') or "Yo'q"
        text = (
            "🔔 <b>YANGI SOTISH ARIZASI</b>\n"
            "━━━━━━━━━━━━━━━━━━━\n\n"
            f"🆔 <b>ID:</b> {obj_id}\n"
            f"🏠 <b>Mulk:</b> {data['mulk_turi']}\n"
            f"📍 <b>Joylashuv:</b> {data['joylashuv']}\n"
            f"📏 <b>Maydon:</b> {data['maydon']}\n"
            f"💰 <b>Narx:</b> {data['narx']}\n\n"
            "👤 <b>MIJOZ:</b>\n"
            f"• Ism: {data['ism_familiya']}\n"
            f"• Telefon: {data['telefon']}\n\n"
            f"📝 <b>Izoh:</b>\n{izoh_text}\n\n"
            "━━━━━━━━━━━━━━━━━━━"
        )
        
        await bot.send_message(ADMIN_CHAT_ID, text, parse_mode="HTML")
        
        # Media yuborish
        media_list = data.get('media', [])
        for media in media_list:
            try:
                if media['type'] == 'photo':
                    await bot.send_photo(
                        ADMIN_CHAT_ID,
                        photo=media['file_id'],
                        caption=f"📸 Ariza #{obj_id}"
                    )
                elif media['type'] == 'video':
                    await bot.send_video(
                        ADMIN_CHAT_ID,
                        video=media['file_id'],
                        caption=f"📹 Ariza #{obj_id}"
                    )
            except Exception as e:
                logger.error(f"Admin ga media yuborishda xato: {e}")
                await bot.send_message(
                    ADMIN_CHAT_ID,
                    f"⚠️ Media yuklanmadi (Ariza #{obj_id})"
                )
        
    except Exception as e:
        logger.error(f"Admin ga yuborishda xato: {e}")
        raise