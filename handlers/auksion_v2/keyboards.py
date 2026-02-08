"""
Auksion V2 uchun keyboard tugmalari
Hierarchik kategoriyalar
"""
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from typing import List, Optional

from .categories import MAIN_CATEGORIES, SUB_CATEGORIES, get_breadcrumb
from .config import EMOJI_BACK, EMOJI_FAVORITE, EMOJI_UNFAVORITE, EMOJI_SEARCH, EMOJI_INFO, EMOJI_APPLY, EMOJI_IMAGES
from .models import Lot, storage
from .utils import format_price, paginate_list


def get_auksion_main_keyboard() -> InlineKeyboardMarkup:
    """
    Auksion asosiy menyusi - 10 ta asosiy kategoriya + Sevimlilar + Qidiruv
    """
    builder = InlineKeyboardBuilder()
    
    # 10 ta asosiy kategoriya
    for cat_key, cat_name in MAIN_CATEGORIES.items():
        builder.button(
            text=cat_name,
            callback_data=f"auk2:cat:{cat_key}"
        )
    
    # Sevimlilar va Qidiruv
    builder.button(
        text=f"{EMOJI_FAVORITE} Sevimlilar",
        callback_data="auk2:favorites"
    )
    builder.button(
        text=f"{EMOJI_SEARCH} Qidiruv",
        callback_data="auk2:search"
    )
    
    # Orqaga (bosh menyuga)
    builder.button(
        text=f"{EMOJI_BACK} Bosh menyu",
        callback_data="main_menu"
    )
    
    builder.adjust(2, 2, 2, 2, 2, 2, 1)
    return builder.as_markup()


def get_subcategory_keyboard(main_cat: str) -> InlineKeyboardMarkup:
    """
    Sub-kategoriyalar keyboard
    
    Args:
        main_cat: Asosiy kategoriya key
    """
    builder = InlineKeyboardBuilder()
    
    if main_cat not in SUB_CATEGORIES:
        return get_back_to_main_keyboard()
    
    # Sub-kategoriyalar
    for sub_key, sub_name in SUB_CATEGORIES[main_cat].items():
        builder.button(
            text=sub_name,
            callback_data=f"auk2:sub:{main_cat}:{sub_key}"
        )
    
    # Orqaga
    builder.button(
        text=f"{EMOJI_BACK} Orqaga",
        callback_data="auk2:menu"
    )
    
    builder.adjust(2)
    return builder.as_markup()


def get_lots_list_keyboard(
    lots: List[Lot],
    main_cat: str,
    sub_cat: str,
    page: int = 1,
    total_pages: int = 1
) -> InlineKeyboardMarkup:
    """
    Lotlar ro'yxati keyboard
    
    Args:
        lots: Lotlar ro'yxati
        main_cat: Asosiy kategoriya
        sub_cat: Sub-kategoriya
        page: Joriy sahifa
        total_pages: Jami sahifalar
    """
    builder = InlineKeyboardBuilder()
    
    # Har bir lot uchun tugma
    for lot in lots:
        # Lot nomini qisqartirish
        lot_name = lot.name[:35] + "..." if len(lot.name) > 35 else lot.name
        
        builder.button(
            text=f"📦 {lot_name}",
            callback_data=f"auk2:view:{lot.id}:{main_cat}:{sub_cat}"
        )
    
    # Navigatsiya
    nav_buttons = []
    
    if page > 1:
        nav_buttons.append(InlineKeyboardButton(
            text="⬅️ Oldingi",
            callback_data=f"auk2:page:{main_cat}:{sub_cat}:{page-1}"
        ))
    
    if total_pages > 1:
        nav_buttons.append(InlineKeyboardButton(
            text=f"📄 {page}/{total_pages}",
            callback_data="noop"
        ))
    
    if page < total_pages:
        nav_buttons.append(InlineKeyboardButton(
            text="Keyingi ➡️",
            callback_data=f"auk2:page:{main_cat}:{sub_cat}:{page+1}"
        ))
    
    if nav_buttons:
        builder.row(*nav_buttons)
    
    # Orqaga
    builder.row(InlineKeyboardButton(
        text=f"{EMOJI_BACK} Orqaga",
        callback_data=f"auk2:cat:{main_cat}"
    ))
    
    builder.adjust(1)
    return builder.as_markup()


def get_lot_detail_keyboard(
    lot: Lot,
    user_id: int,
    main_cat: str,
    sub_cat: str
) -> InlineKeyboardMarkup:
    """
    Lot batafsil ma'lumotlari keyboard
    
    Args:
        lot: Lot obyekti
        user_id: Foydalanuvchi ID
        main_cat: Asosiy kategoriya
        sub_cat: Sub-kategoriya
    """
    builder = InlineKeyboardBuilder()
    
    # Rasmlar (agar mavjud bo'lsa)
    if lot.images:
        builder.button(
            text=f"{EMOJI_IMAGES} Rasmlar ({len(lot.images)})",
            callback_data=f"auk2:images:{lot.id}:0:{main_cat}:{sub_cat}"
        )
    
    # Ariza yuborish
    builder.button(
        text=f"{EMOJI_APPLY} Ariza yuborish",
        callback_data=f"auk2:apply:{lot.id}:{main_cat}:{sub_cat}"
    )
    
    # Sevimliga qo'shish/o'chirish
    is_favorite = storage.is_favorite(user_id, lot.id)
    
    if is_favorite:
        builder.button(
            text=f"{EMOJI_UNFAVORITE} Sevimlilardan o'chirish",
            callback_data=f"auk2:unfav:{lot.id}:{main_cat}:{sub_cat}"
        )
    else:
        builder.button(
            text=f"{EMOJI_FAVORITE} Sevimliga qo'shish",
            callback_data=f"auk2:fav:{lot.id}:{main_cat}:{sub_cat}"
        )
    
    # Orqaga
    builder.button(
        text=f"{EMOJI_BACK} Orqaga",
        callback_data=f"auk2:sub:{main_cat}:{sub_cat}"
    )
    
    builder.adjust(1, 1, 1, 1)
    return builder.as_markup()


def get_image_navigation_keyboard(
    lot_id: int,
    current_index: int,
    total_images: int,
    main_cat: str,
    sub_cat: str
) -> InlineKeyboardMarkup:
    """
    Rasmlar navigatsiyasi keyboard
    
    Args:
        lot_id: Lot ID
        current_index: Joriy rasm indexi
        total_images: Jami rasmlar soni
        main_cat: Asosiy kategoriya
        sub_cat: Sub-kategoriya
    """
    builder = InlineKeyboardBuilder()
    
    nav_buttons = []
    
    # Oldingi
    if current_index > 0:
        nav_buttons.append(InlineKeyboardButton(
            text="⬅️",
            callback_data=f"auk2:images:{lot_id}:{current_index-1}:{main_cat}:{sub_cat}"
        ))
    
    # Counter
    nav_buttons.append(InlineKeyboardButton(
        text=f"{current_index + 1}/{total_images}",
        callback_data="noop"
    ))
    
    # Keyingi
    if current_index < total_images - 1:
        nav_buttons.append(InlineKeyboardButton(
            text="➡️",
            callback_data=f"auk2:images:{lot_id}:{current_index+1}:{main_cat}:{sub_cat}"
        ))
    
    builder.row(*nav_buttons)
    
    # Orqaga
    builder.row(InlineKeyboardButton(
        text=f"{EMOJI_BACK} Orqaga",
        callback_data=f"auk2:view:{lot_id}:{main_cat}:{sub_cat}"
    ))
    
    return builder.as_markup()


def get_application_confirm_keyboard(
    lot_id: int,
    main_cat: str,
    sub_cat: str
) -> InlineKeyboardMarkup:
    """
    Arizani tasdiqlash keyboard
    
    Args:
        lot_id: Lot ID
        main_cat: Asosiy kategoriya
        sub_cat: Sub-kategoriya
    """
    builder = InlineKeyboardBuilder()
    
    builder.button(
        text="✅ Ha, yuborish",
        callback_data=f"auk2:apply_confirm:{lot_id}:{main_cat}:{sub_cat}"
    )
    builder.button(
        text="❌ Yo'q, bekor qilish",
        callback_data=f"auk2:view:{lot_id}:{main_cat}:{sub_cat}"
    )
    
    builder.adjust(1)
    return builder.as_markup()


def get_favorites_keyboard(
    lots: List[Lot],
    page: int = 1,
    total_pages: int = 1
) -> InlineKeyboardMarkup:
    """
    Sevimlilar ro'yxati keyboard
    
    Args:
        lots: Sevimli lotlar ro'yxati
        page: Joriy sahifa
        total_pages: Jami sahifalar
    """
    builder = InlineKeyboardBuilder()
    
    # Har bir sevimli lot
    for lot in lots:
        lot_name = lot.name[:35] + "..." if len(lot.name) > 35 else lot.name
        
        builder.button(
            text=f"{EMOJI_FAVORITE} {lot_name}",
            callback_data=f"auk2:view_fav:{lot.id}"
        )
    
    # Navigatsiya
    nav_buttons = []
    
    if page > 1:
        nav_buttons.append(InlineKeyboardButton(
            text="⬅️ Oldingi",
            callback_data=f"auk2:fav_page:{page-1}"
        ))
    
    if total_pages > 1:
        nav_buttons.append(InlineKeyboardButton(
            text=f"📄 {page}/{total_pages}",
            callback_data="noop"
        ))
    
    if page < total_pages:
        nav_buttons.append(InlineKeyboardButton(
            text="Keyingi ➡️",
            callback_data=f"auk2:fav_page:{page+1}"
        ))
    
    if nav_buttons:
        builder.row(*nav_buttons)
    
    # Orqaga
    builder.row(InlineKeyboardButton(
        text=f"{EMOJI_BACK} Orqaga",
        callback_data="auk2:menu"
    ))
    
    builder.adjust(1)
    return builder.as_markup()


def get_search_keyboard() -> InlineKeyboardMarkup:
    """Qidiruv keyboard"""
    builder = InlineKeyboardBuilder()
    
    builder.button(
        text=f"{EMOJI_BACK} Orqaga",
        callback_data="auk2:menu"
    )
    
    return builder.as_markup()


def get_back_to_main_keyboard() -> InlineKeyboardMarkup:
    """Oddiy orqaga tugmasi"""
    builder = InlineKeyboardBuilder()
    
    builder.button(
        text=f"{EMOJI_BACK} Orqaga",
        callback_data="auk2:menu"
    )
    
    return builder.as_markup()


def noop_keyboard() -> InlineKeyboardMarkup:
    """Bo'sh keyboard"""
    return InlineKeyboardMarkup(inline_keyboard=[])