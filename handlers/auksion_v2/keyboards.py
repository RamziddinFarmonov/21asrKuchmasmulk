"""
Auksion V2 - Keyboard tugmalari
YANGILANGAN: get_my_applications_keyboard + asosiy menyuda "Mening arizalarim"
"""
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from typing import List

from .categories import MAIN_CATEGORIES, SUB_CATEGORIES
from .config import EMOJI_BACK, EMOJI_FAVORITE, EMOJI_UNFAVORITE, EMOJI_SEARCH, EMOJI_IMAGES
from .models import Lot, storage
from .utils import format_price, paginate_list


def get_auksion_main_keyboard() -> InlineKeyboardMarkup:
    """
    Auksion asosiy menyusi.
    YANGI: "Mening arizalarim" tugmasi qo'shildi.
    """
    builder = InlineKeyboardBuilder()

    for cat_key, cat_name in MAIN_CATEGORIES.items():
        builder.button(text=cat_name, callback_data=f"auk2:cat:{cat_key}")

    builder.button(text=f"{EMOJI_FAVORITE} Sevimlilar",      callback_data="auk2:favorites")
    builder.button(text=f"{EMOJI_SEARCH} Qidiruv",           callback_data="auk2:search")
    builder.button(text="📋 Mening arizalarim",              callback_data="auk2:my_applications")
    builder.button(text=f"{EMOJI_BACK} Bosh menyu",          callback_data="main_menu")

    # 10 ta kategoriya = 5 qator x 2, keyin har biri alohida
    builder.adjust(2, 2, 2, 2, 2, 2, 1, 1)
    return builder.as_markup()


def get_subcategory_keyboard(main_cat: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    if main_cat not in SUB_CATEGORIES:
        return get_back_to_main_keyboard()
    for sub_key, sub_name in SUB_CATEGORIES[main_cat].items():
        builder.button(text=sub_name, callback_data=f"auk2:sub:{main_cat}:{sub_key}")
    builder.button(text=f"{EMOJI_BACK} Orqaga", callback_data="auk2:menu")
    builder.adjust(2)
    return builder.as_markup()


def get_lots_list_keyboard(
    lots: List[Lot],
    main_cat: str,
    sub_cat: str,
    page: int = 1,
    total_pages: int = 1
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    for lot in lots:
        lot_name = lot.name[:35] + "..." if len(lot.name) > 35 else lot.name
        builder.button(text=f"📦 {lot_name}", callback_data=f"auk2:view:{lot.id}:{main_cat}:{sub_cat}")

    nav = []
    if page > 1:
        nav.append(InlineKeyboardButton(text="⬅️ Oldingi", callback_data=f"auk2:page:{main_cat}:{sub_cat}:{page-1}"))
    if total_pages > 1:
        nav.append(InlineKeyboardButton(text=f"🔄 {page}/{total_pages}", callback_data="noop"))
    if page < total_pages:
        nav.append(InlineKeyboardButton(text="Keyingi ➡️", callback_data=f"auk2:page:{main_cat}:{sub_cat}:{page+1}"))
    if nav:
        builder.row(*nav)

    builder.row(InlineKeyboardButton(text=f"{EMOJI_BACK} Orqaga", callback_data=f"auk2:cat:{main_cat}"))
    builder.adjust(1)
    return builder.as_markup()


def get_lot_detail_keyboard(
    lot: Lot,
    user_id: int,
    main_cat: str,
    sub_cat: str
) -> InlineKeyboardMarkup:
    """
    Lot batafsil keyboard.
    Tugmalar:
      📸 Barcha rasmlar (agar 2+ ta bo'lsa)
      🙋 Qiziqdim — Ariza yuborish
      ⭐ / 🗑 Sevimlilar
      🌐 E-auksion.uz da ko'rish
      🔙 Orqaga
    """
    builder = InlineKeyboardBuilder()

    # Rasmlar — faqat 2 va undan ko'p bo'lsa (1-rasm allaqachon rasm xabarida bor)
    if lot.images and len(lot.images) > 1:
        builder.button(
            text=f"{EMOJI_IMAGES} Barcha rasmlar ({len(lot.images)} ta)",
            callback_data=f"auk2:images:{lot.id}:0:{main_cat}:{sub_cat}"
        )

    # Asosiy tugma
    builder.button(
        text="🙋 Qiziqdim — Ariza yuborish",
        callback_data=f"auk2:apply:{lot.id}:{main_cat}:{sub_cat}"
    )

    # Sevimlilar
    if storage.is_favorite(user_id, lot.id):
        builder.button(
            text=f"{EMOJI_UNFAVORITE} Sevimlilardan o'chirish",
            callback_data=f"auk2:unfav:{lot.id}:{main_cat}:{sub_cat}"
        )
    else:
        builder.button(
            text=f"{EMOJI_FAVORITE} Sevimliga qo'shish",
            callback_data=f"auk2:fav:{lot.id}:{main_cat}:{sub_cat}"
        )

    # Saytga havola
    builder.button(
        text="🌐 E-auksion.uz da ko'rish",
        url=f"https://e-auksion.uz/lot/{lot.id}"
    )

    # Orqaga
    builder.button(
        text=f"{EMOJI_BACK} Orqaga",
        callback_data=f"auk2:sub:{main_cat}:{sub_cat}"
    )

    builder.adjust(1)
    return builder.as_markup()


def get_image_navigation_keyboard(
    lot_id: int,
    current_index: int,
    total_images: int,
    main_cat: str,
    sub_cat: str
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    nav = []
    if current_index > 0:
        nav.append(InlineKeyboardButton(
            text="⬅️",
            callback_data=f"auk2:images:{lot_id}:{current_index-1}:{main_cat}:{sub_cat}"
        ))
    nav.append(InlineKeyboardButton(text=f"📸 {current_index+1}/{total_images}", callback_data="noop"))
    if current_index < total_images - 1:
        nav.append(InlineKeyboardButton(
            text="➡️",
            callback_data=f"auk2:images:{lot_id}:{current_index+1}:{main_cat}:{sub_cat}"
        ))
    builder.row(*nav)
    builder.row(InlineKeyboardButton(
        text=f"{EMOJI_BACK} Lotga qaytish",
        callback_data=f"auk2:view:{lot_id}:{main_cat}:{sub_cat}"
    ))
    return builder.as_markup()


def get_favorites_keyboard(
    lots: List[Lot],
    page: int = 1,
    total_pages: int = 1
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for lot in lots:
        lot_name = lot.name[:35] + "..." if len(lot.name) > 35 else lot.name
        builder.button(text=f"{EMOJI_FAVORITE} {lot_name}", callback_data=f"auk2:view_fav:{lot.id}")

    nav = []
    if page > 1:
        nav.append(InlineKeyboardButton(text="⬅️ Oldingi", callback_data=f"auk2:fav_page:{page-1}"))
    if total_pages > 1:
        nav.append(InlineKeyboardButton(text=f"🔄 {page}/{total_pages}", callback_data="noop"))
    if page < total_pages:
        nav.append(InlineKeyboardButton(text="Keyingi ➡️", callback_data=f"auk2:fav_page:{page+1}"))
    if nav:
        builder.row(*nav)

    builder.row(InlineKeyboardButton(text=f"{EMOJI_BACK} Orqaga", callback_data="auk2:menu"))
    builder.adjust(1)
    return builder.as_markup()


def get_my_applications_keyboard(applications) -> InlineKeyboardMarkup:
    """
    'Mening arizalarim' ro'yxati keyboard.
    Har bir ariza uchun:
      - Lot nomi (qisqa) + narx o'zgarish belgisi
      - Bosganda → ariza tafsilotiga o'tadi
    """
    builder = InlineKeyboardBuilder()

    for app in applications[:15]:  # Max 15 ta ko'rsatamiz
        # Narx o'zgarish belgisi
        if app.price_changed():
            diff = app.price_diff()
            price_badge = " 📈" if diff > 0 else " 📉"
        else:
            price_badge = ""

        lot_name = app.lot_name[:28] + "..." if len(app.lot_name) > 28 else app.lot_name
        date_str = app.applied_at.strftime('%d.%m')

        builder.button(
            text=f"📋 {lot_name}{price_badge} ({date_str})",
            callback_data=f"auk2:app_detail:{app.lot_id}"
        )

    builder.row(InlineKeyboardButton(text=f"{EMOJI_BACK} Orqaga", callback_data="auk2:menu"))
    builder.adjust(1)
    return builder.as_markup()


def get_search_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text=f"{EMOJI_BACK} Orqaga", callback_data="auk2:menu")
    return builder.as_markup()


def get_back_to_main_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text=f"{EMOJI_BACK} Orqaga", callback_data="auk2:menu")
    return builder.as_markup()


def noop_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[])