"""Ko'chmas Mulk - Asosiy Handler"""
from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from utils.keyboards import get_kochmas_mulk_menu

router = Router()


@router.message(F.text == "🏠 Ko'chmas mulk")
async def show_kochmas_menu(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "🏠 <b>Ko'chmas Mulk Bo'limi</b>\n\n"
        "Siz bu yerda o'z mulkingizni sotishingiz yoki\n"
        "yangi mulk sotib olishingiz mumkin.",
        reply_markup=get_kochmas_mulk_menu(),
        parse_mode="HTML"
    )