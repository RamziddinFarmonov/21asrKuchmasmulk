"""
handlers/auksion_v2/region_filter.py
Viloyat + Tuman filtri

YANGILANGAN:
  - Viloyat tanlanganida → tuman tanlash ekrani chiqadi
  - Tuman tanlanganidan keyin → lotlar ko'rsatiladi
  - "Barcha tumanlar" tugmasi ham mavjud
  - API ga areas_id uzatiladi
"""
from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

from .api import api_client
from .models import storage
from .keyboards import get_lots_list_keyboard, get_back_to_main_keyboard
from .utils import format_price
from .categories import get_breadcrumb, CATEGORY_FILTERS

router = Router()

# ============================================================================
# VILOYATLAR
# ============================================================================

REGIONS = {
    "all":          "🌍 Barcha viloyatlar",
    "toshkent_sh":  "🏛 Toshkent shahri",
    "toshkent":     "🏙 Toshkent viloyati",
    "samarqand":    "🕌 Samarqand",
    "buxoro":       "🕌 Buxoro",
    "andijon":      "🏔 Andijon",
    "fargona":      "🌄 Farg'ona",
    "namangan":     "🏔 Namangan",
    "qashqadaryo":  "🏜 Qashqadaryo",
    "surxondaryo":  "🌞 Surxondaryo",
    "jizzax":       "🏞 Jizzax",
    "sirdaryo":     "🌊 Sirdaryo",
    "navoiy":       "⛰ Navoiy",
    "xorazm":       "🏜 Xorazm",
    "qoraqalpog":   "🐪 Qoraqalpog'iston",
}

REGION_IDS = {
    "all":         None,
    "toshkent_sh": 1,
    "toshkent":    2,
    "samarqand":   3,
    "buxoro":      11,
    "andijon":     7,
    "fargona":     6,
    "namangan":    8,
    "qashqadaryo": 9,
    "surxondaryo": 10,
    "jizzax":      4,
    "sirdaryo":    5,
    "navoiy":      12,
    "xorazm":      14,
    "qoraqalpog":  13,
}

# ============================================================================
# TUMANLAR (areas_id)
# ============================================================================

DISTRICTS = {
    # ── Toshkent shahri (regions_id=1) ──────────────────────────────────────
    "toshkent_sh": {
        "mirobod":        ("Mirobod tumani",          1),
        "mirzo_ulugbek":  ("Mirzo Ulug'bek tumani",   2),
        "yakkasaroy":     ("Yakkasaroy tumani",        3),
        "olmazor":        ("Olmazor tumani",           4),
        "yunusobod":      ("Yunusobod tumani",         5),
        "chilonzor":      ("Chilonzor tumani",         6),
        "uchtepa":        ("Uchtepa tumani",           7),
        "sirg_ali":       ("Sirg'ali tumani",          8),
        "yashnobod":      ("Yashnobod tumani",         9),
        "shayxontohur":   ("Shayxontohur tumani",      10),
        "bektimir":       ("Bektimir tumani",          11),
        "yangihayot":     ("Yangihayot tumani",        230),
        "yangi_toshkent": ("Yangi Toshkent shahri",    236),
    },

    # ── Toshkent viloyati (regions_id=2) ────────────────────────────────────
    "toshkent": {
        "olmaliq_sh":      ("Olmaliq shahri",          12),
        "angren_sh":       ("Angren shahri",           13),
        "ohangaron_t":     ("Ohangaron tumani",        14),
        "oqqo_rgon":       ("Oqqo'rg'on tumani",       15),
        "bekobod_sh":      ("Bekobod shahri",          16),
        "bo_ka":           ("Bo'ka tumani",            17),
        "bo_stonliq":      ("Bo'stonliq tumani",       18),
        "bekobod_t":       ("Bekobod tumani",          19),
        "zangiota":        ("Zangiota tumani",         20),
        "qibray":          ("Qibray tumani",           21),
        "parkent":         ("Parkent tumani",          22),
        "piskent":         ("Piskent tumani",          23),
        "quyichirchiq":    ("Quyichirchiq tumani",     24),
        "o_rtachirchiq":   ("O'rtachirchiq tumani",    25),
        "chirchiq_sh":     ("Chirchiq shahri",         26),
        "chinoz":          ("Chinoz tumani",           27),
        "yuqorichirchiq":  ("Yuqorichirchiq tumani",   28),
        "yangiyo_l_t":     ("Yangiyo'l tumani",        29),
        "toshkent_t":      ("Toshkent tumani",         218),
        "nurafshon_sh":    ("Nurafshon shahri",        219),
        "yangiyo_l_sh":    ("Yangiyo'l shahri",        220),
        "ohangaron_sh":    ("Ohangaron shahri",        221),
    },

    # ── Samarqand viloyati (regions_id=3) ───────────────────────────────────
    "samarqand": {
        "samarqand_sh":    ("Samarqand shahri",        30),
        "samarqand_t":     ("Samarqand tumani",        31),
        "bulung_ur":       ("Bulung'ur tumani",        32),
        "jomboy":          ("Jomboy tumani",           33),
        "pastdarg_om":     ("Pastdarg'om tumani",      34),
        "ishtixon":        ("Ishtixon tumani",         35),
        "kattaqo_sh":      ("Kattaqo'rg'on shahri",    36),
        "nurobod":         ("Nurobod tumani",          37),
        "oqdaryo":         ("Oqdaryo tumani",          38),
        "narpay":          ("Narpay tumani",           39),
        "payariq":         ("Payariq tumani",          40),
        "kattaqo_t":       ("Kattaqo'rg'on tumani",    41),
        "paxtachi":        ("Paxtachi tumani",         42),
        "tayloq":          ("Tayloq tumani",           43),
        "urgut":           ("Urgut tumani",            44),
        "qo_shrabot":      ("Qo'shrabot tumani",       45),
    },

    # ── Jizzax viloyati (regions_id=4) ──────────────────────────────────────
    "jizzax": {
        "jizzax_sh":       ("Jizzax shahri",           47),
        "sharof_rashidov": ("Sharof Rashidov tumani",  48),
        "g_allaorol":      ("G'allaorol tumani",       49),
        "baxmal":          ("Baxmal tumani",           50),
        "paxtakor":        ("Paxtakor tumani",         51),
        "zafarobot":       ("Zafarobot tumani",        52),
        "do_stlik":        ("Do'stlik tumani",         53),
        "arnasoy":         ("Arnasoy tumani",          54),
        "mirzacho_l":      ("Mirzacho'l tumani",       55),
        "zarbdor":         ("Zarbdor tumani",          56),
        "zomin":           ("Zomin tumani",            57),
        "forish":          ("Forish tumani",           59),
        "yangiobod":       ("Yangiobod tumani",        60),
    },

    # ── Sirdaryo viloyati (regions_id=5) ────────────────────────────────────
    "sirdaryo": {
        "guliston_sh":     ("Guliston shahri",         61),
        "yangiyer_sh":     ("Yangiyer shahri",         62),
        "shirin_sh":       ("Shirin shahri",           63),
        "oqoltin":         ("Oqoltin tumani",          64),
        "boyovut":         ("Boyovut tumani",          65),
        "guliston_t":      ("Guliston tumani",         66),
        "sirdaryo_t":      ("Sirdaryo tumani",         67),
        "sayxunobod":      ("Sayxunobod tumani",       69),
        "xovos":           ("Xovos tumani",            70),
        "mirzaobod":       ("Mirzaobod tumani",        71),
        "sardoba":         ("Sardoba tumani",          72),
    },

    # ── Farg'ona viloyati (regions_id=6) ────────────────────────────────────
    "fargona": {
        "marg_ilon_sh":    ("Marg'ilon shahri",        73),
        "fargona_sh":      ("Farg'ona shahri",         74),
        "quvasoy_sh":      ("Quvasoy shahri",          75),
        "qo_qon_sh":       ("Qo'qon shahri",           76),
        "bag_dod":         ("Bag'dod tumani",          77),
        "beshariq":        ("Beshariq tumani",         78),
        "dang_ara":        ("Dang'ara tumani",         80),
        "yozyovon":        ("Yozyovon tumani",         81),
        "oltiariq":        ("Oltiariq tumani",         82),
        "qo_shtepa":       ("Qo'shtepa tumani",        83),
        "rishton":         ("Rishton tumani",          84),
        "so_x":            ("So'x tumani",             85),
        "toshloq":         ("Toshloq tumani",          86),
        "uchko_prik":      ("Uchko'prik tumani",       87),
        "fargona_t":       ("Farg'ona tumani",         88),
        "furqat":          ("Furqat tumani",           89),
        "o_zbekiston":     ("O'zbekiston tumani",      90),
        "quva":            ("Quva tumani",             91),
        "buvayda":         ("Buvayda tumani",          214),
    },

    # ── Andijon viloyati (regions_id=7) ─────────────────────────────────────
    "andijon": {
        "andijon_sh":      ("Andijon shahri",          92),
        "andijon_t":       ("Andijon tumani",          93),
        "asaka":           ("Asaka tumani",            94),
        "baliqchi":        ("Baliqchi tumani",         95),
        "bo_ston":         ("Bo'ston tumani",          96),
        "buloqboshi":      ("Buloqboshi tumani",       97),
        "julaquduq":       ("Jalaquduq tumani",        98),
        "izboskan":        ("Izboskan tumani",         99),
        "qo_rg_ontepa":    ("Qo'rg'ontepa tumani",    100),
        "marhamat":        ("Marhamat tumani",         103),
        "oltinko_l":       ("Oltinko'l tumani",        104),
        "paxtaobod":       ("Paxtaobod tumani",        105),
        "ulug_nor":        ("Ulug'nor tumani",         106),
        "xo_jabod":        ("Xo'jabod tumani",         107),
        "shahrixon":       ("Shahrixon tumani",        108),
        "xonobod_sh":      ("Xonobod shahri",          216),
    },

    # ── Namangan viloyati (regions_id=8) ────────────────────────────────────
    "namangan": {
        "namangan_sh":     ("Namangan shahri",         109),
        "kosonsoy":        ("Kosonsoy tumani",         110),
        "norin":           ("Norin tumani",            111),
        "uchqo_rg_on":     ("Uchqo'rg'on tumani",     112),
        "chartoq":         ("Chartoq tumani",          113),
        "chust":           ("Chust tumani",            114),
        "to_raqo_rg_on":   ("To'raqo'rg'on tumani",   115),
        "pop":             ("Pop tumani",              116),
        "mingbuloq":       ("Mingbuloq tumani",        117),
        "namangan_t":      ("Namangan tumani",         118),
        "uychi":           ("Uychi tumani",            119),
        "yangiqo_rg_on":   ("Yangiqo'rg'on tumani",   120),
        "davlatobod":      ("Davlatobod tumani",       232),
        "yangi_namangan":  ("Yangi Namangan tumani",   234),
    },

    # ── Qashqadaryo viloyati (regions_id=9) ─────────────────────────────────
    "qashqadaryo": {
        "qarshi_sh":       ("Qarshi shahri",           121),
        "shahrizabz_t":    ("Shahrizabz tumani",       122),
        "kitob":           ("Kitob tumani",            123),
        "yakkabog_":       ("Yakkabog' tumani",        124),
        "chiroqchi":       ("Chiroqchi tumani",        125),
        "qamashi":         ("Qamashi tumani",          126),
        "g_uzor":          ("G'uzor tumani",           127),
        "qarshi_t":        ("Qarshi tumani",           128),
        "nishon":          ("Nishon tumani",           129),
        "koson":           ("Koson tumani",            130),
        "kasbi":           ("Kasbi tumani",            131),
        "mirishkor":       ("Mirishkor tumani",        132),
        "muborak":         ("Muborak tumani",          133),
        "dehqonobod":      ("Dehqonobod tumani",       134),
        "ko_kdala":        ("Ko'kdala tumani",         235),
        "shahrizabz_sh":   ("Shahrizabz shahri",       222),
    },

    # ── Surxondaryo viloyati (regions_id=10) ────────────────────────────────
    "surxondaryo": {
        "oltinsoy":        ("Oltinsoy tumani",         143),
        "angor":           ("Angor tumani",            135),
        "bandixon":        ("Bandixon tumani",         228),
        "boysun":          ("Boysun tumani",           136),
        "muzrabot":        ("Muzrabot tumani",         142),
        "denov":           ("Denov tumani",            138),
        "jarqo_rg_on":     ("Jarqo'rg'on tumani",     139),
        "qumqo_rg_on":     ("Qumqo'rg'on tumani",     141),
        "qiziriq":         ("Qiziriq tumani",          140),
        "sariosiyo":       ("Sariosiyo tumani",        144),
        "termiz_t":        ("Termiz tumani",           146),
        "uzun":            ("Uzun tumani",             149),
        "sherobod":        ("Sherobod tumani",         147),
        "sho_rchi":        ("Sho'rchi tumani",         148),
        "termiz_sh":       ("Termiz shahri",           145),
    },

    # ── Buxoro viloyati (regions_id=11) ─────────────────────────────────────
    "buxoro": {
        "buxoro_sh":       ("Buxoro shahri",           150),
        "romitan":         ("Romitan tumani",          151),
        "kogon_t":         ("Kogon tumani",            152),
        "g_ijduvon":       ("G'ijduvon tumani",        153),
        "buxoro_t":        ("Buxoro tumani",           154),
        "jondor":          ("Jondor tumani",           155),
        "vobkent":         ("Vobkent tumani",          156),
        "peshko_":         ("Peshko' tumani",          157),
        "shofirkon":       ("Shofirkon tumani",        158),
        "qorako_l":        ("Qorako'l tumani",         159),
        "olot":            ("Olot tumani",             160),
        "qorovulbozor":    ("Qorovulbozor tumani",     161),
        "kogon_sh":        ("Kogon shahri",            210),
    },

    # ── Navoiy viloyati (regions_id=12) ─────────────────────────────────────
    "navoiy": {
        "zarafshon_sh":    ("Zarafshon shahri",        162),
        "karmana":         ("Karmana tumani",          163),
        "qiziltepa":       ("Qiziltepa tumani",        164),
        "konimex":         ("Konimex tumani",          165),
        "navoiy_sh":       ("Navoiy shahri",           166),
        "navbahor":        ("Navbahor tumani",         167),
        "nurota":          ("Nurota tumani",           168),
        "xatirchi":        ("Xatirchi tumani",         169),
        "tomdi":           ("Tomdi tumani",            211),
        "uchquduq":        ("Uchquduq tumani",         212),
        "go_zg_on_sh":     ("Go'zg'on shahri",         224),
    },

    # ── Qoraqalpog'iston (regions_id=13) ────────────────────────────────────
    "qoraqalpog": {
        "nukus_sh":        ("Nukus shahri",            170),
        "nukus_t":         ("Nukus tumani",            171),
        "kegeyli":         ("Kegeyli tumani",          172),
        "chimboy":         ("Chimboy tumani",          173),
        "qorao_zak":       ("Qorao'zak tumani",        174),
        "taxtako_pir":     ("Taxtako'pir tumani",      175),
        "xo_jayli":        ("Xo'jayli tumani",         176),
        "shumanay":        ("Shumanay tumani",         177),
        "qonliko_l":       ("Qonliko'l tumani",        178),
        "taxiatosh":       ("Taxiatosh tumani",        179),
        "qo_ng_irot":      ("Qo'ng'irot tumani",       180),
        "mo_ynoq":         ("Mo'ynoq tumani",          181),
        "amudaryo":        ("Amudaryo tumani",         182),
        "to_rtko_l":       ("To'rtko'l tumani",        183),
        "ellikqal_a":      ("Ellikqal'a tumani",       184),
        "beruniy":         ("Beruniy tumani",          185),
        "bo_zatov":        ("Bo'zatov tumani",         198),
    },

    # ── Xorazm viloyati (regions_id=14) ─────────────────────────────────────
    "xorazm": {
        "urganch_sh":      ("Urganch shahri",          186),
        "urganch_t":       ("Urganch tumani",          187),
        "xiva_t":          ("Xiva tumani",             188),
        "xonqa":           ("Xonqa tumani",            189),
        "shovot":          ("Shovot tumani",           190),
        "bog_dot":         ("Bog'dot tumani",          191),
        "yangiariq":       ("Yangiariq tumani",        192),
        "yangibozor":      ("Yangibozor tumani",       193),
        "gurlan":          ("Gurlan tumani",           194),
        "qo_shko_prik":    ("Qo'shko'prik tumani",     195),
        "xazorasp":        ("Xazorasp tumani",         196),
        "tuproqqal_a":     ("Tuproqqal'a tumani",      226),
        "xiva_sh":         ("Xiva shahri",             223),
    },
}


# ============================================================================
# KLAVIATURALAR
# ============================================================================

def get_region_filter_keyboard(main_cat: str, sub_cat: str) -> InlineKeyboardMarkup:
    """Viloyat tanlash klaviaturasi"""
    buttons = [[InlineKeyboardButton(
        text=REGIONS["all"],
        callback_data=f"auk2:region:all:{main_cat}:{sub_cat}"
    )]]
    region_list = list(REGIONS.items())[1:]
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
    buttons.append([InlineKeyboardButton(text="🔙 Orqaga", callback_data=f"auk2:cat:{main_cat}")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_district_filter_keyboard(region_code: str, main_cat: str, sub_cat: str) -> InlineKeyboardMarkup:
    """Tuman tanlash klaviaturasi"""
    districts = DISTRICTS.get(region_code, {})
    buttons = []

    # "Barcha tumanlar" — birinchi
    buttons.append([InlineKeyboardButton(
        text="🌍 Barcha tumanlar",
        callback_data=f"auk2:district:all:{region_code}:{main_cat}:{sub_cat}"
    )])

    # Tumanlar — 2 tadan
    items = [(k, v) for k, v in districts.items() if k != "all"]
    for i in range(0, len(items), 2):
        row = []
        for j in range(2):
            if i + j < len(items):
                d_code, (d_name, _) = items[i + j]
                row.append(InlineKeyboardButton(
                    text=d_name,
                    callback_data=f"auk2:district:{d_code}:{region_code}:{main_cat}:{sub_cat}"
                ))
        buttons.append(row)

    buttons.append([InlineKeyboardButton(
        text="🔙 Viloyatlar",
        callback_data=f"auk2:subcat:{main_cat}:{sub_cat}"
    )])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


# ============================================================================
# HANDLERLAR
# ============================================================================

@router.callback_query(F.data.startswith("auk2:subcat:"))
async def callback_show_region_selection(callback: CallbackQuery):
    """Sub-kategoriya → Viloyat tanlash"""
    parts = callback.data.split(":")
    main_cat, sub_cat = parts[2], parts[3]
    breadcrumb = get_breadcrumb(main_cat, sub_cat)
    await callback.message.edit_text(
        f"📂 <b>{breadcrumb}</b>\n\n📍 <b>Viloyatni tanlang:</b>",
        reply_markup=get_region_filter_keyboard(main_cat, sub_cat),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data.startswith("auk2:region:"))
async def callback_region_selected(callback: CallbackQuery):
    """Viloyat tanlandi → Tuman tanlash ekrani"""
    parts = callback.data.split(":")
    region_code = parts[2]
    main_cat    = parts[3]
    sub_cat     = parts[4]

    # "Barcha viloyatlar" — tuman ekranisiz to'g'ridan API
    if region_code == "all":
        await _load_and_show_lots(callback, None, None, main_cat, sub_cat)
        return

    # Tuman ro'yxati bormi?
    if region_code in DISTRICTS and len(DISTRICTS[region_code]) > 1:
        region_name = REGIONS.get(region_code, "")
        breadcrumb  = get_breadcrumb(main_cat, sub_cat)
        await callback.message.edit_text(
            f"📂 <b>{breadcrumb}</b>\n\n"
            f"🗺️ <b>{region_name}</b>\n\n"
            "📍 <b>Tumanni tanlang:</b>",
            reply_markup=get_district_filter_keyboard(region_code, main_cat, sub_cat),
            parse_mode="HTML"
        )
        await callback.answer()
    else:
        # Tuman yo'q → to'g'ridan viloyat bo'yicha
        region_id = REGION_IDS.get(region_code)
        await _load_and_show_lots(callback, region_id, None, main_cat, sub_cat)


@router.callback_query(F.data.startswith("auk2:district:"))
async def callback_district_selected(callback: CallbackQuery):
    """Tuman tanlandi → Lotlar yuklash"""
    parts       = callback.data.split(":")
    dist_code   = parts[2]
    region_code = parts[3]
    main_cat    = parts[4]
    sub_cat     = parts[5]

    region_id = REGION_IDS.get(region_code)

    if dist_code == "all":
        area_id = None
    else:
        district_data = DISTRICTS.get(region_code, {}).get(dist_code)
        area_id = district_data[1] if district_data else None

    await _load_and_show_lots(callback, region_id, area_id, main_cat, sub_cat)


@router.callback_query(F.data.startswith("auk2:change_region:"))
async def callback_change_region(callback: CallbackQuery):
    """Viloyatni o'zgartirish"""
    parts = callback.data.split(":")
    main_cat, sub_cat = parts[2], parts[3]
    await callback.message.edit_text(
        f"📂 <b>{get_breadcrumb(main_cat, sub_cat)}</b>\n\n📍 <b>Viloyatni tanlang:</b>",
        reply_markup=get_region_filter_keyboard(main_cat, sub_cat),
        parse_mode="HTML"
    )
    await callback.answer()


# ============================================================================
# LOTLARNI YUKLASH VA KO'RSATISH
# ============================================================================

async def _load_and_show_lots(
    callback, region_id, area_id, main_cat: str, sub_cat: str
):
    """API dan lotlar olib ko'rsatish (viloyat + tuman filtri bilan)"""
    await callback.message.edit_text("⏳ Lotlar yuklanmoqda...")

    filter_data = CATEGORY_FILTERS.get(sub_cat)
    if not filter_data:
        await callback.answer("❌ Xato", show_alert=True)
        return

    try:
        lots = await api_client.get_lots_by_category(
            groups_id=filter_data["groups_id"],
            categories_id=filter_data["categories_id"],
            region_id=region_id,
            area_id=area_id,
            page=1
        )

        breadcrumb   = get_breadcrumb(main_cat, sub_cat)
        region_name  = _get_location_name(region_id, area_id)

        if not lots:
            buttons = [
                [InlineKeyboardButton(text="🌍 Boshqa viloyat", callback_data=f"auk2:subcat:{main_cat}:{sub_cat}")],
                [InlineKeyboardButton(text="🏠 Bosh menyu",     callback_data="auk2:menu")],
            ]
            await callback.message.edit_text(
                f"📂 <b>{breadcrumb}</b>\n\n"
                f"📍 <b>{region_name}</b>\n\n"
                "❌ <b>Bu hududda lotlar topilmadi</b>\n\n"
                "• Boshqa viloyat/tumanni tanlang\n"
                "• Yoki keyinroq urinib ko'ring",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons),
                parse_mode="HTML"
            )
            await callback.answer("Bu hududda lotlar yo'q", show_alert=True)
            return

        keyboard = get_lots_list_keyboard(lots, main_cat, sub_cat, 1, 999)
        keyboard.inline_keyboard.insert(0, [
            InlineKeyboardButton(
                text=f"📍 {region_name}  |  🔄 O'zgartirish",
                callback_data=f"auk2:change_region:{main_cat}:{sub_cat}"
            )
        ])

        await callback.message.edit_text(
            f"📂 <b>{breadcrumb}</b>\n\n"
            f"📍 <b>{region_name}</b>\n"
            f"📦 Topildi: <b>{len(lots)}</b> ta lot\n\n"
            "Lotni tanlang 👇",
            reply_markup=keyboard,
            parse_mode="HTML"
        )
        await callback.answer()

    except Exception as e:
        import logging
        logging.error(f"District filter error: {e}")
        await callback.message.edit_text(
            "❌ Xatolik yuz berdi. Qaytadan urinib ko'ring.",
            reply_markup=get_back_to_main_keyboard()
        )
        await callback.answer()


def _get_location_name(region_id, area_id) -> str:
    """Ko'rsatiladigan joy nomi"""
    if region_id is None:
        return "Barcha viloyatlar"

    # Viloyat nomini topish
    region_name = ""
    for code, rid in REGION_IDS.items():
        if rid == region_id:
            region_name = REGIONS.get(code, "")
            # Agar tuman ham bo'lsa
            if area_id is not None and code in DISTRICTS:
                for d_code, (d_name, a_id) in DISTRICTS[code].items():
                    if a_id == area_id:
                        return f"{region_name} → {d_name}"
            break
    return region_name or "Noma'lum hudud"