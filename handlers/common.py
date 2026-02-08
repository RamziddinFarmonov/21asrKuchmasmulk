"""
Umumiy Handler va Menyular
Professional version - UPDATED
"""
from aiogram import Router, F
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from aiogram.fsm.context import FSMContext

router = Router()

# ============================================================================
# ASOSIY MENYULAR
# ============================================================================
main_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🏠 Ko'chmas mulk")],
        [KeyboardButton(text="🏛 Auksion")],  # YANGILANDI
        [KeyboardButton(text="📋 Ijaralar")]
    ],
    resize_keyboard=True,
    input_field_placeholder="Bo'limni tanlang..."
)

kochmas_menu = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="🏢 Ko'p qavatli uy sotish"),
            KeyboardButton(text="🏢 Ko'p qavatli uy sotib olish")
        ],
        [
            KeyboardButton(text="🏡 Hovli sotish"),
            KeyboardButton(text="🏡 Hovli sotib olish")
        ],
        [
            KeyboardButton(text="🏬 Savdo do'konini sotish"),
            KeyboardButton(text="🏬 Savdo do'konini sotib olish")
        ],
        [
            KeyboardButton(text="🗺 Yer uchastkasini sotish"),
            KeyboardButton(text="🗺 Yer uchastkasini sotib olish")
        ],
        [KeyboardButton(text="🔙 Asosiy menyuga qaytish")]
    ],
    resize_keyboard=True,
    input_field_placeholder="Ko'chmas mulk bo'limidan tanlang..."
)

ijara_menu = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="🏢 Ko'p qavatli uyni ijaraga berish"),
            KeyboardButton(text="🏢 Ko'p qavatli uyni ijaraga olish")
        ],
        [
            KeyboardButton(text="🏡 Hovli ijaraga berish"),
            KeyboardButton(text="🏡 Hovli ijaraga olish")
        ],
        [
            KeyboardButton(text="🏬 Savdo do'konini ijaraga berish"),
            KeyboardButton(text="🏬 Savdo do'konini ijaraga olish")
        ],
        [
            KeyboardButton(text="🏨 Mehmonxona ijaraga berish"),
            KeyboardButton(text="🏨 Mehmonxona ijaraga olish")
        ],
        [
            KeyboardButton(text="📄 Boshqa ijara joylarini berish"),
            KeyboardButton(text="📄 Boshqa ijara joylarini olish")
        ],
        [KeyboardButton(text="🔙 Asosiy menyuga qaytish")]
    ],
    resize_keyboard=True,
    input_field_placeholder="Ijara bo'limidan tanlang..."
)

# ============================================================================
# HANDLER'LAR
# ============================================================================
@router.message(F.text == "/start")
async def start_handler(message: Message, state: FSMContext):
    await state.clear()
    user_name = message.from_user.first_name
    await message.answer(
        f"👋 <b>Xush kelibsiz, {user_name}!</b>\n\n"
        "🏢 <b>Ko'chmas Mulk va Auksion Bot</b>\n\n"
        "Bu bot orqali siz:\n"
        "• Ko'chmas mulk sotish/sotib olish\n"
        "• Mulk ijaraga berish/olish\n"
        "• Davlat auksionlarida ishtirok etish\n\n"
        "Kerakli bo'limni tanlang:",
        reply_markup=main_menu,
        parse_mode="HTML"
    )

@router.message(F.text == "🏠 Ko'chmas mulk")
async def show_kochmas_menu(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "🏠 Ko'chmas Mulk Bo'limi\n\n"
        "Kerakli amalni tanlang:",
        reply_markup=kochmas_menu,
        parse_mode="HTML"
    )

# YANGI - Auksion tugmasi handler
@router.message(F.text == "🏛 Auksion")
async def show_auksion_from_button(message: Message):
    """Auksion tugmasi bosilganda"""
    # Auksion handler'ini import qilib chaqirish
    from handlers.auksion_v2.handlers import show_auksion_main_menu
    await show_auksion_main_menu(message)

@router.message(F.text == "📋 Ijaralar")
async def show_ijara_menu(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "📋 Ijaralar Bo'limi\n\n"
        "Kerakli amalni tanlang:",
        reply_markup=ijara_menu,
        parse_mode="HTML"
    )

@router.message(F.text == "🔙 Asosiy menyuga qaytish")
async def back_to_main(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "Asosiy menyuga qaytdingiz:",
        reply_markup=main_menu
    )