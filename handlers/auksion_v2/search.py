"""
PROFESSIONAL QIDIRUV TIZIMI
handlers/auksion_v2/search.py
"""
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext

from .states import AuksionStatesV2
from .api import api_client
from .models import storage
from .keyboards import get_lots_list_keyboard, get_back_to_main_keyboard
from .utils import format_price

import re

router = Router()


def get_search_keyboard() -> InlineKeyboardMarkup:
    """Qidiruv turi klaviaturasi"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔤 Matn bo'yicha", callback_data="search:text")],
        [InlineKeyboardButton(text="🔢 Lot ID bo'yicha", callback_data="search:id")],
        [InlineKeyboardButton(text="🔙 Orqaga", callback_data="auk2:menu")]
    ])


@router.callback_query(F.data == "auk2:search")
async def callback_show_search(callback: CallbackQuery, state: FSMContext):
    """Qidiruv menyusi"""
    await state.clear()
    
    text = (
        "🔍 <b>QIDIRUV</b>\n\n"
        "Qidiruv turini tanlang:\n\n"
        "🔤 <b>Matn:</b> Lot nomida qidirish\n"
        "🔢 <b>ID:</b> Lot raqami bo'yicha\n"
    )
    
    await callback.message.edit_text(
        text,
        reply_markup=get_search_keyboard(),
        parse_mode="HTML"
    )
    await callback.answer()


# 1. MATN BO'YICHA QIDIRUV
@router.callback_query(F.data == "search:text")
async def callback_search_text(callback: CallbackQuery, state: FSMContext):
    """Matn bo'yicha qidiruv"""
    await state.set_state(AuksionStatesV2.searching)
    await state.update_data(search_type="text")
    
    await callback.message.edit_text(
        "🔍 <b>MATN BO'YICHA QIDIRUV</b>\n\n"
        "Lot nomini yoki kalit so'zni kiriting:\n\n"
        "<i>Misol: hovli, ko'p qavatli, kompressor, yer</i>",
        parse_mode="HTML"
    )
    await callback.answer()


# 2. ID BO'YICHA QIDIRUV
@router.callback_query(F.data == "search:id")
async def callback_search_id(callback: CallbackQuery, state: FSMContext):
    """ID bo'yicha qidiruv"""
    await state.set_state(AuksionStatesV2.searching)
    await state.update_data(search_type="id")
    
    await callback.message.edit_text(
        "🔍 <b>ID BO'YICHA QIDIRUV</b>\n\n"
        "Lot raqamini kiriting:\n\n"
        "<i>Misol: 21587155 yoki #21587155</i>",
        parse_mode="HTML"
    )
    await callback.answer()


# QIDIRUV NATIJALARINI QAYTA ISHLASH
@router.message(AuksionStatesV2.searching)
async def process_search_query(message: Message, state: FSMContext):
    """Qidiruv so'rovini qayta ishlash"""
    data = await state.get_data()
    search_type = data.get("search_type", "text")
    query = message.text.strip()
    
    await message.answer("⏳ Qidirilmoqda...")
    
    # Qidiruv turi bo'yicha
    if search_type == "id":
        # ID bo'yicha
        lot_id = re.sub(r'[^0-9]', '', query)  # Faqat raqamlar
        if lot_id:
            lot = await api_client.get_lot_detail(int(lot_id))
            if lot:
                lots = [lot]
            else:
                lots = []
        else:
            lots = []
        
        await show_search_results(message, lots, f"ID: #{lot_id}")
    
    else:
        # Matn bo'yicha (default)
        lots = await api_client.search_lots(query)
        await show_search_results(message, lots, f"Qidiruv: {query}")
    
    await state.clear()


async def show_search_results(message, lots, search_info):
    """Qidiruv natijalarini ko'rsatish"""
    if not lots:
        text = (
            f"🔍 <b>{search_info}</b>\n\n"
            "❌ Hech narsa topilmadi.\n\n"
            "Boshqa so'z bilan qidiring yoki kategoriyalardan tanlang."
        )
        await message.answer(
            text,
            reply_markup=get_back_to_main_keyboard(),
            parse_mode="HTML"
        )
        return
    
    text = (
        f"🔍 <b>{search_info}</b>\n\n"
        f"✅ Topildi: {len(lots)} ta lot\n\n"
        "Lotni tanlang:"
    )
    
    # Keyboard - birinchi 10 ta lot
    display_lots = lots[:10]
    keyboard = get_lots_list_keyboard(display_lots, "search", "results", 1, 1)
    
    # Agar ko'p bo'lsa, ogohlantirish
    if len(lots) > 10:
        text += f"\n\n<i>Ko'rsatildi: 10/{len(lots)}</i>"
    
    await message.answer(text, reply_markup=keyboard, parse_mode="HTML")


async def search_by_price(min_price: int, max_price: int):
    """Narx oralig'i bo'yicha qidiruv"""
    # Barcha lotlarni olish
    all_lots = []
    
    # Bir nechta kategoriyadan qidirish (optimizatsiya)
    # Faqat eng ko'p ishlatiladigan kategoriyalar
    categories_to_search = [
        ("1", 3),   # Ko'chmas mulk - Ko'p qavatli
        ("1", 2),   # Ko'chmas mulk - Turar-joy
        ("6", 46),  # Yer - Tadbirkorlik
        ("5", 27),  # Davlat - Davlat obyekti
    ]
    
    for groups_id, categories_id in categories_to_search:
        lots = await api_client.get_lots_by_category(
            groups_id=groups_id,
            categories_id=categories_id,
            page=1,
            per_page=50
        )
        all_lots.extend(lots)
    

