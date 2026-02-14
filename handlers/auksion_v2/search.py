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
        [InlineKeyboardButton(text="💰 Narx oralig'i", callback_data="search:price")],
        [InlineKeyboardButton(text="📍 Joylashuv", callback_data="search:location")],
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
        "💰 <b>Narx:</b> Narx oralig'i\n"
        "📍 <b>Joylashuv:</b> Viloyat/tuman"
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


# 3. NARX BO'YICHA QIDIRUV
@router.callback_query(F.data == "search:price")
async def callback_search_price(callback: CallbackQuery, state: FSMContext):
    """Narx oralig'i tanlash"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💵 100M so'mdan kam", callback_data="price:0-100000000")],
        [InlineKeyboardButton(text="💵 100M - 500M", callback_data="price:100000000-500000000")],
        [InlineKeyboardButton(text="💵 500M - 1B", callback_data="price:500000000-1000000000")],
        [InlineKeyboardButton(text="💵 1B - 5B", callback_data="price:1000000000-5000000000")],
        [InlineKeyboardButton(text="💵 5B dan yuqori", callback_data="price:5000000000-999999999999")],
        [InlineKeyboardButton(text="✍️ Qo'lda kiritish", callback_data="price:custom")],
        [InlineKeyboardButton(text="🔙 Orqaga", callback_data="auk2:search")]
    ])
    
    await callback.message.edit_text(
        "🔍 <b>NARX BO'YICHA QIDIRUV</b>\n\n"
        "Narx oralig'ini tanlang:",
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data.startswith("price:"))
async def callback_price_range(callback: CallbackQuery, state: FSMContext):
    """Narx oralig'i tanlandi"""
    price_range = callback.data.split(":")[1]
    
    if price_range == "custom":
        await state.set_state(AuksionStatesV2.searching)
        await state.update_data(search_type="price_custom")
        
        await callback.message.edit_text(
            "🔍 <b>NARX ORALIG'I</b>\n\n"
            "Narx oralig'ini kiriting:\n\n"
            "<i>Format: 100M-500M yoki 1B-5B</i>\n"
            "<i>Misol: 200M-800M</i>",
            parse_mode="HTML"
        )
        await callback.answer()
        return
    
    # Narx oralig'ini parse qilish
    min_price, max_price = price_range.split("-")
    min_price = int(min_price)
    max_price = int(max_price)
    
    await callback.message.edit_text("⏳ Qidirilmoqda...")
    
    # Qidiruv
    lots = await search_by_price(min_price, max_price)
    
    await show_search_results(callback.message, lots, f"Narx: {format_price(min_price)} - {format_price(max_price)}")
    await callback.answer()


# 4. JOYLASHUV BO'YICHA
@router.callback_query(F.data == "search:location")
async def callback_search_location(callback: CallbackQuery, state: FSMContext):
    """Joylashuv bo'yicha qidiruv"""
    await state.set_state(AuksionStatesV2.searching)
    await state.update_data(search_type="location")
    
    await callback.message.edit_text(
        "🔍 <b>JOYLASHUV BO'YICHA QIDIRUV</b>\n\n"
        "Viloyat yoki tuman nomini kiriting:\n\n"
        "<i>Misol: Toshkent, Samarqand, Buxoro, Andijon</i>",
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
    
    elif search_type == "price_custom":
        # Narx (custom)
        min_price, max_price = parse_price_range(query)
        if min_price and max_price:
            lots = await search_by_price(min_price, max_price)
            await show_search_results(message, lots, f"Narx: {format_price(min_price)} - {format_price(max_price)}")
        else:
            await message.answer(
                "❌ Narx formati noto'g'ri!\n\n"
                "Format: 100M-500M yoki 1B-5B\n"
                "Qaytadan kiriting:"
            )
            return
    
    elif search_type == "location":
        # Joylashuv bo'yicha
        lots = await api_client.search_lots(query)
        # Location filter
        filtered_lots = [lot for lot in lots if lot.location and query.lower() in lot.location.lower()]
        await show_search_results(message, filtered_lots, f"Joylashuv: {query}")
    
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
    
    # Narx bo'yicha filter
    filtered = []
    for lot in all_lots:
        price = lot.current_price or lot.start_price
        if min_price <= price <= max_price:
            filtered.append(lot)
    
    return filtered


def parse_price_range(query: str) -> tuple:
    """Narx oralig'ini parse qilish"""
    query = query.upper().replace(" ", "")
    
    # Format: 100M-500M yoki 1B-5B
    match = re.match(r'(\d+)([MB])?-(\d+)([MB])?', query)
    if not match:
        return None, None
    
    min_val = int(match.group(1))
    min_unit = match.group(2) or 'M'
    max_val = int(match.group(3))
    max_unit = match.group(4) or 'M'
    
    # Million yoki Billion
    if min_unit == 'B':
        min_price = min_val * 1_000_000_000
    else:
        min_price = min_val * 1_000_000
    
    if max_unit == 'B':
        max_price = max_val * 1_000_000_000
    else:
        max_price = max_val * 1_000_000
    
    return min_price, max_price