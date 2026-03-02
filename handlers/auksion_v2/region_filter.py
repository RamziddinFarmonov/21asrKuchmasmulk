"""
VILOYAT FILTRI - YANGILANGAN (TO'QNASHUVSIZ)
"""
from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext

from .api import api_client
from .models import storage
from .keyboards import get_lots_list_keyboard
from .utils import format_price
from .categories import get_breadcrumb, CATEGORY_FILTERS

router = Router()

# O'zbekiston viloyatlari
REGIONS = {
    "all": "🌍 Barcha viloyatlar",
    "toshkent_sh": "🏛 Toshkent shahri",
    "toshkent": "🏙 Toshkent viloyati",
    "samarqand": "🕌 Samarqand",
    "buxoro": "🕌 Buxoro",
    "andijon": "🏔 Andijon",
    "fargona": "🌄 Farg'ona",
    "namangan": "🏔 Namangan",
    "qashqadaryo": "🏜 Qashqadaryo",
    "surxondaryo": "🌞 Surxondaryo",
    "jizzax": "🏞 Jizzax",
    "sirdaryo": "🌊 Sirdaryo",
    "navoiy": "⛰ Navoiy",
    "xorazm": "🏜 Xorazm",
    "qoraqalpog": "🐪 Qoraqalpog'iston"
}

# Region ID mapping
REGION_IDS = {
    "all": None,
    "toshkent_sh": 1,
    "toshkent": 2,
    "samarqand": 3,
    "buxoro": 11,
    "andijon": 7,
    "fargona": 6,
    "namangan": 8,
    "qashqadaryo": 9,
    "surxondaryo": 10,
    "jizzax": 4,
    "sirdaryo": 5,
    "navoiy": 12,
    "xorazm": 14,
    "qoraqalpog": 13
}


def get_region_filter_keyboard(main_cat: str, sub_cat: str) -> InlineKeyboardMarkup:
    """Viloyat tanlash klaviaturasi"""
    buttons = []
    
    # Barcha viloyatlar
    buttons.append([
        InlineKeyboardButton(
            text=REGIONS["all"],
            callback_data=f"auk2:region:all:{main_cat}:{sub_cat}"
        )
    ])
    
    # Viloyatlar - 2 tadan
    region_list = list(REGIONS.items())[1:]
    
    for i in range(0, len(region_list), 2):
        row = []
        for j in range(2):
            if i + j < len(region_list):
                region_code, region_name = region_list[i + j]
                row.append(
                    InlineKeyboardButton(
                        text=region_name,
                        callback_data=f"auk2:region:{region_code}:{main_cat}:{sub_cat}"
                    )
                )
        buttons.append(row)
    
    # Orqaga
    buttons.append([
        InlineKeyboardButton(text="🔙 Orqaga", callback_data=f"auk2:cat:{main_cat}")
    ])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)


# YANGI CALLBACK - handlers.py dagi "auk2:sub:" bilan to'qnashmaydi
@router.callback_query(F.data.startswith("auk2:subcat:"))  # YANGILANDI!
async def callback_show_region_selection(callback: CallbackQuery):
    """Sub-kategoriya tanlanganda viloyat so'rash"""
    parts = callback.data.split(":")
    main_cat = parts[2]
    sub_cat = parts[3]
    
    breadcrumb = get_breadcrumb(main_cat, sub_cat)
    
    text = (
        f"📂 <b>{breadcrumb}</b>\n\n"
        "📍 <b>Viloyatni tanlang:</b>\n\n"
        "<i>Sizning viloyatingizdagi lotlarni ko'rsatamiz</i>"
    )
    
    keyboard = get_region_filter_keyboard(main_cat, sub_cat)
    
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data.startswith("auk2:region:"))
async def callback_filter_by_region(callback: CallbackQuery):
    """Viloyat bo'yicha filtrlash"""
    parts = callback.data.split(":")
    region_code = parts[2]
    main_cat = parts[3]
    sub_cat = parts[4]
    
    await callback.message.edit_text("⏳ Lotlar yuklanmoqda...")
    
    # Filter data
    filter_data = CATEGORY_FILTERS.get(sub_cat)
    if not filter_data:
        await callback.answer("❌ Xato", show_alert=True)
        return
    
    # Region ID
    region_id = REGION_IDS.get(region_code)
    
    # API dan lotlar
    try:
        lots = await api_client.get_lots_by_category_and_region(
            groups_id=filter_data["groups_id"],
            categories_id=filter_data["categories_id"],
            region_id=region_id,
            page=1
        )
        
        if not lots:
            breadcrumb = get_breadcrumb(main_cat, sub_cat)
            region_name = REGIONS.get(region_code, "")
            
            # Yaxshilangan xabar
            text = (
                f"📂 <b>{breadcrumb}</b>\n\n"
                f"📍 <b>{region_name}</b>\n\n"
                "❌ <b>Bu viloyatda lotlar topilmadi</b>\n\n"
                "🔍 <b>Sabablari:</b>\n"
                "• Hozircha bu hududda auksion yo'q\n"
                "• Barcha lotlar sotilgan\n"
                "• Tez orada yangi lotlar qo'shilishi mumkin\n\n"
                "💡 <b>Tavsiya:</b>\n"
                "• Boshqa viloyatni tanlang\n"
                "• Yoki 🔔 Bildirishnomani yoqing\n\n"
                "<i>Yangi lot chiqsa xabar beramiz!</i>"
            )
            
            # Keyboard
            buttons = [
                [InlineKeyboardButton(
                    text="🔔 Bildirishnoma yoqish",
                    callback_data=f"notify:{main_cat}:{sub_cat}:{region_code}"
                )],
                [InlineKeyboardButton(
                    text="🌍 Boshqa viloyat",
                    callback_data=f"auk2:subcat:{main_cat}:{sub_cat}"
                )],
                [InlineKeyboardButton(
                    text="📂 Boshqa kategoriya",
                    callback_data=f"auk2:cat:{main_cat}"
                )],
                [InlineKeyboardButton(
                    text="🏠 Bosh menyu",
                    callback_data="auk2:menu"
                )]
            ]
            keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
            
            await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
            await callback.answer("Bu viloyatda lotlar yo'q", show_alert=True)
            return
        
        # Natijalar
        breadcrumb = get_breadcrumb(main_cat, sub_cat)
        region_name = REGIONS.get(region_code, "Barcha viloyatlar")
        
        text = (
            f"📂 <b>{breadcrumb}</b>\n\n"
            f"📍 <b>{region_name}</b>\n"
            f"📦 Topildi: {len(lots)} ta lot\n\n"
            "Lotni tanlang:"
        )
        
        # Keyboard
        keyboard = get_lots_list_keyboard(lots, main_cat, sub_cat, 1, 999)
        
        # Viloyat tugmasi
        keyboard.inline_keyboard.insert(0, [
            InlineKeyboardButton(
                text=f"📍 {region_name}",
                callback_data=f"auk2:change_region:{main_cat}:{sub_cat}"
            )
        ])
        
        await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
        await callback.answer()
        
    except Exception as e:
        from .config import MSG_ERROR
        await callback.message.edit_text(MSG_ERROR)
        await callback.answer()
        import logging
        logging.error(f"Region filter error: {e}")


@router.callback_query(F.data.startswith("auk2:change_region:"))
async def callback_change_region(callback: CallbackQuery):
    """Viloyatni o'zgartirish"""
    parts = callback.data.split(":")
    main_cat = parts[2]
    sub_cat = parts[3]
    
    breadcrumb = get_breadcrumb(main_cat, sub_cat)
    
    text = (
        f"📂 <b>{breadcrumb}</b>\n\n"
        "📍 <b>Boshqa viloyatni tanlang:</b>"
    )
    
    keyboard = get_region_filter_keyboard(main_cat, sub_cat)
    
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()