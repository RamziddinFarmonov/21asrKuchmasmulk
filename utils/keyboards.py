"""
Keyboard Utilities - FULL FIXED
Tahrirlash tugmasi o'chirildi
"""
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from typing import List, Dict
from utils.constants import REGIONS, PROPERTY_TYPES, RENTAL_TYPES, RENTAL_PERIODS


# ============================================================================
# ASOSIY KLAVIATURALAR
# ============================================================================

def get_main_menu() -> ReplyKeyboardMarkup:
    """Asosiy menyu"""
    keyboard = [
        [KeyboardButton(text="🏠 Ko'chmas mulk")],
        [KeyboardButton(text="🏛 Auksion")],
        [KeyboardButton(text="📋 Ijaralar")]
    ]
    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True,
        input_field_placeholder="Bo'limni tanlang..."
    )


def get_back_button() -> ReplyKeyboardMarkup:
    """Orqaga qaytish tugmasi"""
    keyboard = [[KeyboardButton(text="🔙 Orqaga")]]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)


def get_cancel_button() -> ReplyKeyboardMarkup:
    """Bekor qilish tugmasi"""
    keyboard = [
        [KeyboardButton(text="❌ Bekor qilish")],
        [KeyboardButton(text="🔙 Orqaga")]
    ]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)


def get_skip_and_cancel() -> ReplyKeyboardMarkup:
    """O'tkazib yuborish va bekor qilish"""
    keyboard = [
        [KeyboardButton(text="⏭️ O'tkazib yuborish")],
        [KeyboardButton(text="❌ Bekor qilish")]
    ]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)


# ============================================================================
# KO'CHMAS MULK KLAVIATURALARI
# ============================================================================

def get_kochmas_mulk_menu() -> ReplyKeyboardMarkup:
    """Ko'chmas mulk bo'limi menyu - QIDIRUVSIZ"""
    keyboard = [
        [
            KeyboardButton(text="📤 Sotish"),
            KeyboardButton(text="📥 Sotib olish")
        ],
        [
            KeyboardButton(text="📊 Mening e'lonlarim"),
            KeyboardButton(text="❤️ Sevimlilar")
        ],
        [KeyboardButton(text="🔙 Asosiy menyuga qaytish")]
    ]
    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True,
        input_field_placeholder="Amalni tanlang..."
    )


def get_property_types_keyboard(include_land: bool = True) -> ReplyKeyboardMarkup:
    """Mulk turlarini tanlash klaviaturasi"""
    keyboard = []
    
    types_list = list(PROPERTY_TYPES.keys())
    if not include_land:
        types_list = [t for t in types_list if "Yer" not in t]
    
    # 2 tadan joylashtirish
    for i in range(0, len(types_list), 2):
        row = types_list[i:i+2]
        keyboard.append([KeyboardButton(text=t) for t in row])
    
    keyboard.append([KeyboardButton(text="🔙 Orqaga")])
    
    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True,
        input_field_placeholder="Mulk turini tanlang..."
    )


def get_regions_keyboard() -> ReplyKeyboardMarkup:
    """Viloyatlarni tanlash klaviaturasi"""
    keyboard = []
    regions_list = list(REGIONS.keys())
    
    # 2 tadan joylashtirish
    for i in range(0, len(regions_list), 2):
        row = regions_list[i:i+2]
        keyboard.append([KeyboardButton(text=r) for r in row])
    
    keyboard.append([KeyboardButton(text="🔙 Orqaga")])
    
    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True,
        input_field_placeholder="Viloyatni tanlang..."
    )


# ============================================================================
# IJARA KLAVIATURALARI
# ============================================================================

def get_ijara_menu() -> ReplyKeyboardMarkup:
    """Ijara bo'limi menyu - QIDIRUVSIZ"""
    keyboard = [
        [
            KeyboardButton(text="📤 Ijaraga berish"),
            KeyboardButton(text="📥 Ijaraga olish")
        ],
        [
            KeyboardButton(text="📊 Mening e'lonlarim"),
            KeyboardButton(text="❤️ Sevimlilar")
        ],
        [KeyboardButton(text="🔙 Asosiy menyuga qaytish")]
    ]
    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True,
        input_field_placeholder="Amalni tanlang..."
    )


def get_rental_types_keyboard() -> ReplyKeyboardMarkup:
    """Ijara turlarini tanlash klaviaturasi"""
    keyboard = []
    types_list = list(RENTAL_TYPES.keys())
    
    # 2 tadan joylashtirish
    for i in range(0, len(types_list), 2):
        row = types_list[i:i+2]
        keyboard.append([KeyboardButton(text=t) for t in row])
    
    keyboard.append([KeyboardButton(text="🔙 Orqaga")])
    
    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True,
        input_field_placeholder="Ijara turini tanlang..."
    )


def get_rental_period_keyboard() -> ReplyKeyboardMarkup:
    """Ijara muddatini tanlash"""
    keyboard = []
    
    for i in range(0, len(RENTAL_PERIODS), 2):
        row = RENTAL_PERIODS[i:i+2]
        keyboard.append([KeyboardButton(text=r) for r in row])
    
    keyboard.append([KeyboardButton(text="🔙 Orqaga")])
    
    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True,
        input_field_placeholder="Minimal ijara muddatini tanlang..."
    )


# ============================================================================
# INLINE KLAVIATURALAR
# ============================================================================

def get_object_actions_keyboard(object_id: int, object_type: str) -> InlineKeyboardMarkup:
    """Obyekt uchun amallar (inline)"""
    keyboard = [
        [
            InlineKeyboardButton(
                text="📞 Bog'lanish",
                callback_data=f"contact_{object_type}_{object_id}"
            )
        ],
        [
            InlineKeyboardButton(
                text="📤 Ulashish",
                callback_data=f"share_{object_type}_{object_id}"
            )
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_pagination_keyboard(
    current_page: int,
    total_pages: int,
    callback_prefix: str
) -> InlineKeyboardMarkup:
    """Sahifalash klaviaturasi"""
    keyboard = []
    
    row = []
    if current_page > 0:
        row.append(InlineKeyboardButton(
            text="◀️ Orqaga",
            callback_data=f"{callback_prefix}_page_{current_page - 1}"
        ))
    
    row.append(InlineKeyboardButton(
        text=f"{current_page + 1}/{total_pages}",
        callback_data="current_page"
    ))
    
    if current_page < total_pages - 1:
        row.append(InlineKeyboardButton(
            text="Keyingi ▶️",
            callback_data=f"{callback_prefix}_page_{current_page + 1}"
        ))
    
    keyboard.append(row)
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_confirmation_keyboard() -> ReplyKeyboardMarkup:
    """Tasdiqlash klaviaturasi - FIXED (Tahrirlash o'chirildi)"""
    keyboard = [
        [KeyboardButton(text="✅ Ha, e'lon berish")],
        [KeyboardButton(text="❌ Bekor qilish")]
    ]
    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True,
        input_field_placeholder="Tasdiqlang..."
    )


def get_my_objects_keyboard(has_objects: bool = True) -> InlineKeyboardMarkup:
    """Mening obyektlarim klaviaturasi"""
    keyboard = []
    
    if has_objects:
        keyboard.append([
            InlineKeyboardButton(
                text="🔄 Yangilash",
                callback_data="refresh_my_objects"
            )
        ])
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard) if keyboard else None


# ============================================================================
# USHBU KODNI utils/keyboards.py GA QO'SHING (mavjud kod o'chirilmaydi)
# ============================================================================
# Import: from utils.constants import DISTRICTS
# (agar mavjud importlarga DISTRICTS ni qo'shing)

def get_districts_keyboard(region_code: str):
    """Tanlangan viloyat tumanlarini ko'rsatuvchi klaviatura"""
    from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
    from utils.constants import DISTRICTS

    districts = DISTRICTS.get(region_code, [])
    buttons = [[KeyboardButton(text=d)] for d in districts]
    buttons.append([KeyboardButton(text="🔙 Orqaga")])

    return ReplyKeyboardMarkup(
        keyboard=buttons,
        resize_keyboard=True,
        one_time_keyboard=True
    )