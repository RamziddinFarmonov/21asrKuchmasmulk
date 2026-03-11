"""
handlers/auksion_v2/region_filter.py
TUZATILDI: BUTTON_DATA_INVALID
  - Tuman callback_data 64 baytdan oshib ketardi
  - Yangi format: auk2:dst:{area_id}:{region_id}  (faqat raqamlar, max ~20 bayt)
  - main_cat va sub_cat → FSMContext state da saqlanadi
"""
from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext

from .api import api_client
from .keyboards import get_lots_list_keyboard, get_back_to_main_keyboard
from .categories import get_breadcrumb, CATEGORY_FILTERS
from .config import ITEMS_PER_PAGE

import logging
logger = logging.getLogger(__name__)

router = Router()

REGIONS = {
    "all":         "🌍 Barcha viloyatlar",
    "toshkent_sh": "🏛 Toshkent shahri",
    "toshkent":    "🏙 Toshkent viloyati",
    "samarqand":   "🕌 Samarqand",
    "buxoro":      "🕌 Buxoro",
    "andijon":     "🏔 Andijon",
    "fargona":     "🌄 Farg'ona",
    "namangan":    "🏔 Namangan",
    "qashqadaryo": "🏜 Qashqadaryo",
    "surxondaryo": "🌞 Surxondaryo",
    "jizzax":      "🏞 Jizzax",
    "sirdaryo":    "🌊 Sirdaryo",
    "navoiy":      "⛰ Navoiy",
    "xorazm":      "🏜 Xorazm",
    "qoraqalpog":  "🐪 Qoraqalpog'iston",
}

REGION_IDS = {
    "all": None, "toshkent_sh": 1, "toshkent": 2, "samarqand": 3,
    "buxoro": 11, "andijon": 7, "fargona": 6, "namangan": 8,
    "qashqadaryo": 9, "surxondaryo": 10, "jizzax": 4, "sirdaryo": 5,
    "navoiy": 12, "xorazm": 14, "qoraqalpog": 13,
}

REGION_CODE_BY_ID = {v: k for k, v in REGION_IDS.items() if v is not None}

# Tumanlar: list of (nomi, areas_id)
DISTRICTS = {
    "toshkent_sh": [
        ("Mirobod", 1), ("Mirzo Ulug'bek", 2), ("Yakkasaroy", 3),
        ("Olmazor", 4), ("Yunusobod", 5), ("Chilonzor", 6),
        ("Uchtepa", 7), ("Sirg'ali", 8), ("Yashnobod", 9),
        ("Shayxontohur", 10), ("Bektimir", 11),
        ("Yangihayot", 230), ("Yangi Toshkent", 236),
    ],
    "toshkent": [
        ("Olmaliq sh", 12), ("Angren sh", 13), ("Ohangaron t", 14),
        ("Oqqo'rg'on", 15), ("Bekobod sh", 16), ("Bo'ka", 17),
        ("Bo'stonliq", 18), ("Bekobod t", 19), ("Zangiota", 20),
        ("Qibray", 21), ("Parkent", 22), ("Piskent", 23),
        ("Quyichirchiq", 24), ("O'rtachirchiq", 25), ("Chirchiq sh", 26),
        ("Chinoz", 27), ("Yuqorichirchiq", 28), ("Yangiyo'l t", 29),
        ("Toshkent t", 218), ("Nurafshon sh", 219),
        ("Yangiyo'l sh", 220), ("Ohangaron sh", 221),
    ],
    "samarqand": [
        ("Samarqand sh", 30), ("Samarqand t", 31), ("Bulung'ur", 32),
        ("Jomboy", 33), ("Pastdarg'om", 34), ("Ishtixon", 35),
        ("Kattaqo'rg'on sh", 36), ("Nurobod", 37), ("Oqdaryo", 38),
        ("Narpay", 39), ("Payariq", 40), ("Kattaqo'rg'on t", 41),
        ("Paxtachi", 42), ("Tayloq", 43), ("Urgut", 44), ("Qo'shrabot", 45),
    ],
    "jizzax": [
        ("Jizzax sh", 47), ("Sharof Rashidov", 48), ("G'allaorol", 49),
        ("Baxmal", 50), ("Paxtakor", 51), ("Zafarobot", 52),
        ("Do'stlik", 53), ("Arnasoy", 54), ("Mirzacho'l", 55),
        ("Zarbdor", 56), ("Zomin", 57), ("Forish", 59), ("Yangiobod", 60),
    ],
    "sirdaryo": [
        ("Guliston sh", 61), ("Yangiyer sh", 62), ("Shirin sh", 63),
        ("Oqoltin", 64), ("Boyovut", 65), ("Guliston t", 66),
        ("Sirdaryo t", 67), ("Sayxunobod", 69), ("Xovos", 70),
        ("Mirzaobod", 71), ("Sardoba", 72),
    ],
    "fargona": [
        ("Marg'ilon sh", 73), ("Farg'ona sh", 74), ("Quvasoy sh", 75),
        ("Qo'qon sh", 76), ("Bag'dod", 77), ("Beshariq", 78),
        ("Dang'ara", 80), ("Yozyovon", 81), ("Oltiariq", 82),
        ("Qo'shtepa", 83), ("Rishton", 84), ("So'x", 85),
        ("Toshloq", 86), ("Uchko'prik", 87), ("Farg'ona t", 88),
        ("Furqat", 89), ("O'zbekiston t", 90), ("Quva", 91), ("Buvayda", 214),
    ],
    "andijon": [
        ("Andijon sh", 92), ("Andijon t", 93), ("Asaka", 94),
        ("Baliqchi", 95), ("Bo'ston", 96), ("Buloqboshi", 97),
        ("Jalaquduq", 98), ("Izboskan", 99), ("Qo'rg'ontepa", 100),
        ("Marhamat", 103), ("Oltinko'l", 104), ("Paxtaobod", 105),
        ("Ulug'nor", 106), ("Xo'jabod", 107), ("Shahrixon", 108),
        ("Xonobod sh", 216),
    ],
    "namangan": [
        ("Namangan sh", 109), ("Kosonsoy", 110), ("Norin", 111),
        ("Uchqo'rg'on", 112), ("Chartoq", 113), ("Chust", 114),
        ("To'raqo'rg'on", 115), ("Pop", 116), ("Mingbuloq", 117),
        ("Namangan t", 118), ("Uychi", 119), ("Yangiqo'rg'on", 120),
        ("Davlatobod", 232), ("Yangi Namangan", 234),
    ],
    "qashqadaryo": [
        ("Qarshi sh", 121), ("Shahrizabz t", 122), ("Kitob", 123),
        ("Yakkabog'", 124), ("Chiroqchi", 125), ("Qamashi", 126),
        ("G'uzor", 127), ("Qarshi t", 128), ("Nishon", 129),
        ("Koson", 130), ("Kasbi", 131), ("Mirishkor", 132),
        ("Muborak", 133), ("Dehqonobod", 134),
        ("Ko'kdala", 235), ("Shahrizabz sh", 222),
    ],
    "surxondaryo": [
        ("Oltinsoy", 143), ("Angor", 135), ("Bandixon", 228),
        ("Boysun", 136), ("Muzrabot", 142), ("Denov", 138),
        ("Jarqo'rg'on", 139), ("Qumqo'rg'on", 141), ("Qiziriq", 140),
        ("Sariosiyo", 144), ("Termiz t", 146), ("Uzun", 149),
        ("Sherobod", 147), ("Sho'rchi", 148), ("Termiz sh", 145),
    ],
    "buxoro": [
        ("Buxoro sh", 150), ("Romitan", 151), ("Kogon t", 152),
        ("G'ijduvon", 153), ("Buxoro t", 154), ("Jondor", 155),
        ("Vobkent", 156), ("Peshko'", 157), ("Shofirkon", 158),
        ("Qorako'l", 159), ("Olot", 160), ("Qorovulbozor", 161),
        ("Kogon sh", 210),
    ],
    "navoiy": [
        ("Zarafshon sh", 162), ("Karmana", 163), ("Qiziltepa", 164),
        ("Konimex", 165), ("Navoiy sh", 166), ("Navbahor", 167),
        ("Nurota", 168), ("Xatirchi", 169),
        ("Tomdi", 211), ("Uchquduq", 212), ("Go'zg'on sh", 224),
    ],
    "qoraqalpog": [
        ("Nukus sh", 170), ("Nukus t", 171), ("Kegeyli", 172),
        ("Chimboy", 173), ("Qorao'zak", 174), ("Taxtako'pir", 175),
        ("Xo'jayli", 176), ("Shumanay", 177), ("Qonliko'l", 178),
        ("Taxiatosh", 179), ("Qo'ng'irot", 180), ("Mo'ynoq", 181),
        ("Amudaryo", 182), ("To'rtko'l", 183), ("Ellikqal'a", 184),
        ("Beruniy", 185), ("Bo'zatov", 198),
    ],
    "xorazm": [
        ("Urganch sh", 186), ("Urganch t", 187), ("Xiva t", 188),
        ("Xonqa", 189), ("Shovot", 190), ("Bog'dot", 191),
        ("Yangiariq", 192), ("Yangibozor", 193), ("Gurlan", 194),
        ("Qo'shko'prik", 195), ("Xazorasp", 196),
        ("Tuproqqal'a", 226), ("Xiva sh", 223),
    ],
}


# ── Klaviaturalar ─────────────────────────────────────────────────────────────

def get_region_filter_keyboard(main_cat: str, sub_cat: str) -> InlineKeyboardMarkup:
    buttons = [[InlineKeyboardButton(
        text=REGIONS["all"],
        callback_data=f"auk2:region:all:{main_cat}:{sub_cat}"
    )]]
    region_list = [(k, v) for k, v in REGIONS.items() if k != "all"]
    for i in range(0, len(region_list), 2):
        row = []
        for j in range(2):
            if i + j < len(region_list):
                code, name = region_list[i + j]
                row.append(InlineKeyboardButton(
                    text=name,
                    callback_data=f"auk2:region:{code}:{main_cat}:{sub_cat}"
                ))
        buttons.append(row)
    buttons.append([InlineKeyboardButton(
        text="🔙 Orqaga",
        callback_data=f"auk2:sub:{main_cat}:{sub_cat}"
    )])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_district_filter_keyboard(region_code: str, region_id: int) -> InlineKeyboardMarkup:
    """
    Tuman klaviaturasi.
    callback_data: auk2:dst:{area_id}:{region_id}  ← faqat raqamlar, max ~20 bayt
    area_id=0 → barcha tumanlar
    """
    districts = DISTRICTS.get(region_code, [])
    buttons = [[InlineKeyboardButton(
        text="🌍 Barcha tumanlar",
        callback_data=f"auk2:dst:0:{region_id}"
    )]]
    for i in range(0, len(districts), 2):
        row = []
        for j in range(2):
            if i + j < len(districts):
                d_name, a_id = districts[i + j]
                row.append(InlineKeyboardButton(
                    text=d_name,
                    callback_data=f"auk2:dst:{a_id}:{region_id}"
                ))
        buttons.append(row)
    buttons.append([InlineKeyboardButton(text="🔙 Viloyatlar", callback_data="auk2:chrgn")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


# ── Handlerlar ────────────────────────────────────────────────────────────────

@router.callback_query(F.data.startswith("auk2:region:"))
async def callback_region_selected(callback: CallbackQuery, state: FSMContext):
    parts = callback.data.split(":")
    region_code = parts[2]
    main_cat    = parts[3]
    sub_cat     = parts[4]

    # main_cat + sub_cat ni state ga saqlash (tuman handlerida kerak)
    await state.update_data(filter_main_cat=main_cat, filter_sub_cat=sub_cat)

    if region_code == "all":
        await _load_and_show_lots(callback, state, None, None)
        return

    region_id = REGION_IDS.get(region_code)
    districts  = DISTRICTS.get(region_code, [])

    if districts:
        await callback.message.edit_text(
            f"📂 <b>{get_breadcrumb(main_cat, sub_cat)}</b>\n\n"
            f"🗺️ <b>{REGIONS.get(region_code, '')}</b>\n\n"
            "📍 <b>Tumanni tanlang:</b>",
            reply_markup=get_district_filter_keyboard(region_code, region_id),
            parse_mode="HTML"
        )
        await callback.answer()
    else:
        await _load_and_show_lots(callback, state, region_id, None)


@router.callback_query(F.data.startswith("auk2:dst:"))
async def callback_district_selected(callback: CallbackQuery, state: FSMContext):
    parts     = callback.data.split(":")
    area_id   = int(parts[2])   # 0 = barcha
    region_id = int(parts[3])
    await _load_and_show_lots(callback, state, region_id, None if area_id == 0 else area_id)


@router.callback_query(F.data == "auk2:chrgn")
async def callback_change_region(callback: CallbackQuery, state: FSMContext):
    data     = await state.get_data()
    main_cat = data.get("filter_main_cat", "kochmas_mulk")
    sub_cat  = data.get("filter_sub_cat", "kop_qavatli")
    await callback.message.edit_text(
        f"📂 <b>{get_breadcrumb(main_cat, sub_cat)}</b>\n\n📍 <b>Viloyatni tanlang:</b>",
        reply_markup=get_region_filter_keyboard(main_cat, sub_cat),
        parse_mode="HTML"
    )
    await callback.answer()


# ── Lotlarni yuklash ──────────────────────────────────────────────────────────

async def _load_and_show_lots(callback: CallbackQuery, state: FSMContext, region_id, area_id):
    data     = await state.get_data()
    main_cat = data.get("filter_main_cat", "kochmas_mulk")
    sub_cat  = data.get("filter_sub_cat", "kop_qavatli")

    await callback.message.edit_text("⏳ Lotlar yuklanmoqda...")

    filter_data = CATEGORY_FILTERS.get(sub_cat)
    if not filter_data:
        await callback.answer("❌ Kategoriya topilmadi", show_alert=True)
        return

    try:
        lots = await api_client.get_lots_by_category(
            groups_id=filter_data["groups_id"],
            categories_id=filter_data["categories_id"],
            region_id=region_id,
            area_id=area_id,
            page=1
        )

        breadcrumb    = get_breadcrumb(main_cat, sub_cat)
        location_name = _get_location_name(region_id, area_id)

        if not lots:
            await callback.message.edit_text(
                f"📂 <b>{breadcrumb}</b>\n\n"
                f"📍 <b>{location_name}</b>\n\n"
                "❌ <b>Bu hududda lotlar topilmadi</b>\n\n"
                "Boshqa viloyat yoki tumanni tanlang.",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[[
                    InlineKeyboardButton(text="🌍 Boshqa viloyat", callback_data="auk2:chrgn")
                ]]),
                parse_mode="HTML"
            )
            await callback.answer("Bu hududda lotlar yo'q", show_alert=True)
            return

        has_next = len(lots) >= ITEMS_PER_PAGE
        keyboard  = get_lots_list_keyboard(lots, main_cat, sub_cat, 1, has_next)
        keyboard.inline_keyboard.insert(0, [
            InlineKeyboardButton(
                text=f"📍 {location_name}  |  🔄 O'zgartirish",
                callback_data="auk2:chrgn"
            )
        ])

        await callback.message.edit_text(
            f"📂 <b>{breadcrumb}</b>\n\n"
            f"📍 <b>{location_name}</b>\n"
            f"📦 Topildi: <b>{len(lots)}</b> ta lot\n\nLotni tanlang 👇",
            reply_markup=keyboard,
            parse_mode="HTML"
        )
        await callback.answer()

    except Exception as e:
        logger.error(f"Filter error: {e}", exc_info=True)
        await callback.message.edit_text(
            "❌ Xatolik yuz berdi. Qaytadan urinib ko'ring.",
            reply_markup=get_back_to_main_keyboard()
        )
        await callback.answer()


def _get_location_name(region_id, area_id) -> str:
    if region_id is None:
        return "Barcha viloyatlar"
    region_code = REGION_CODE_BY_ID.get(region_id, "")
    region_name = REGIONS.get(region_code, "")
    if area_id is None:
        return region_name
    for d_name, a_id in DISTRICTS.get(region_code, []):
        if a_id == area_id:
            return f"{region_name} → {d_name}"
    return region_name