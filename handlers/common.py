"""
Umumiy Handler - TO'LIQ TUZATILGAN

TUZATILGAN:
- AttributeError uchun alohida except qo'shildi
- Global "❌ Bekor qilish" handler qo'shildi
"""
import logging
from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from utils.keyboards import get_main_menu

router = Router()
logger = logging.getLogger(__name__)


@router.message(F.text == "/start")
async def start_handler(message: Message, state: FSMContext):
    await state.clear()
    user_name = message.from_user.first_name or "Foydalanuvchi"
    await message.answer(
        f"👋 <b>Xush kelibsiz, {user_name}!</b>\n\n"
        "🏢 <b>Ko'chmas Mulk va Auksion Bot</b>\n\n"
        "Bu bot orqali siz:\n"
        "• Ko'chmas mulk sotish / sotib olish\n"
        "• Mulk ijaraga berish / olish\n"
        "• Davlat auksionlarida ishtirok etish\n\n"
        "Kerakli bo'limni tanlang 👇",
        reply_markup=get_main_menu(),
        parse_mode="HTML"
    )


@router.message(F.text == "🔙 Asosiy menyuga qaytish")
async def back_to_main(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("🏠 Asosiy menyu:", reply_markup=get_main_menu())


@router.message(F.text == "❌ Bekor qilish")
async def global_cancel(message: Message, state: FSMContext):
    current = await state.get_state()
    if current:
        await state.clear()
    await message.answer("❌ Bekor qilindi.", reply_markup=get_main_menu())


@router.message(F.text == "🏛 Auksion")
async def show_auksion(message: Message, state: FSMContext):
    await state.clear()
    try:
        from handlers.auksion_v2.handlers import show_auksion_main_menu
        await show_auksion_main_menu(message)
        logger.info("✅ Auksion menyu ko'rsatildi")
    except ImportError as e:
        logger.error(f"❌ Auksion import xatosi: {e}")
        await message.answer(
            "⚠️ Auksion bo'limi hozircha ishlamayapti.\nTez orada qo'shiladi!",
            reply_markup=get_main_menu()
        )
    except AttributeError as e:
        logger.error(f"❌ Auksion funksiya topilmadi: {e}")
        await message.answer(
            "⚠️ Auksion bo'limida texnik nosozlik.\nAdmin bilan bog'laning.",
            reply_markup=get_main_menu()
        )
    except Exception as e:
        logger.error(f"❌ Auksion xatosi: {e}")
        await message.answer(
            "❌ Xatolik yuz berdi. Qaytadan urinib ko'ring.",
            reply_markup=get_main_menu()
        )