"""handlers/ijara/main.py"""
from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from utils.keyboards import get_ijara_menu

router = Router()


@router.message(F.text == "📋 Ijaralar")
async def show_ijara_menu(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "📋 <b>Ijara Bo'limi</b>\n\n"
        "Mulk ijaraga berish yoki olishingiz mumkin.",
        reply_markup=get_ijara_menu(),
        parse_mode="HTML"


        #finish
    )