"""
E-Auksion kategoriyalar - REAL API FILTERS
"""

# Asosiy kategoriyalar (groups_id)
MAIN_CATEGORIES = {
    "davlat_aktivlari": "🏛 Davlat aktivlari",
    "kochmas_mulk": "🏠 Ko'chmas mulk",
    "yer_uchastkalari": "🌍 Yer uchaskalari",
    "dehqon_yer": "🌾 Dehqon xo'jaligiga mo'ljallangan yer",
    "qishloq_yer": "🚜 Qishloq xo'jaligiga mo'ljallangan yer",
    "yer_qari": "💎 Yer qa'ri uchastkasidan foydalanish",
    "daryo_tozalash": "🌊 Daryo o'zanlarini tozalash",
    "kochma_savdo": "🛒 Ko'chma savdo joylari",
    "elektr_stansiya": "⚡ Elektr stansiyalarini qurish",
    "mikromarkazlar": "🏘 Mikromarkazlar",
}

# Groups ID mapping
GROUPS_IDS = {
    "davlat_aktivlari": "5",
    "kochmas_mulk": "1",
    "yer_uchastkalari": "6",
    "dehqon_yer": "24",
    "qishloq_yer": "33",
    "yer_qari": "10",
    "daryo_tozalash": "9",
    "kochma_savdo": "23",
    "elektr_stansiya": "27",
    "mikromarkazlar": "28",
}

# Sub-kategoriyalar (2-daraja)
SUB_CATEGORIES = {
    # 1. Davlat aktivlari (groups_id = "5")
    "davlat_aktivlari": {
        "davlat_obyekt": "🏢 Davlat obyekti",
        "davlat_obyekt_tanlov": "📋 Davlat obyekti (Tanlov)",
    },
    
    # 2. Ko'chmas mulk (groups_id = "1")
    "kochmas_mulk": {
        "kop_qavatli": "🏢 Ko'p qavatli turar-joylar",
        "turar_joy_uchastka": "🏡 Turar-joy uchastkasi (hovli)",
        "qishloq_yer": "🌾 Qishloq xo'jalik yerlari",
        "noturar_joy": "🏭 Noturar-joy obyektlari",
        "tugallanmagan_kop": "🏗 Qurilishi tugallanmagan ko'p qavatli",
        "tugallanmagan_uchastka": "🏗 Qurilishi tugallanmagan turar-joy uchastkalari",
        "tugallanmagan_bino": "🏗 Qurilishi tugallanmagan binolar",
        "bosh_yer": "📍 Bo'sh yerlar",
        "boshqa_mulk": "📦 Boshqa turdagi ko'chmas mulklar",
        "ozogroservis": "🌱 O'zagroservis AJ ko'chmas mulklari",
        "ozagrokimyo": "🧪 O'zagrokimyohimoya AJ bino-inshootlari",
        "davlat_obyekt_km": "🏛 Davlat obyekti",
    },
    
    # 3. Yer uchaskalari (groups_id = "6")
    "yer_uchastkalari": {
        "tadbirkorlik": "🏪 Tadbirkorlik va shaharsozlik uchun",
        "yakka_uy": "🏡 Yakka tartibda uy-joy qurish",
        "kop_qavatli_uy": "🏢 Ko'p qavatli uy-joy qurish",
        "yoshlar_zona": "👥 Yoshlar sanoat zonalari",
        "ormon_fond": "🌲 O'rmon fondi yer uchastkalari",
        "yangi_toshkent": "🏙 Yangi Toshkent loyihasi",
        "ekoturizm": "🏞 Ekoturizmni tashkil etish",
        "kichik_sanoat": "🏭 Kichik sanoat zonalari",
        "erkin_zona": "🌐 Erkin iqtisodiy zonalari",
        "yangi_ozbekiston_kop": "🏙 Yangi O'zbekiston (ko'p qavatli)",
        "turistik_rekreatsion": "🏖 Turistik rekreatsion zona",
        "turistik_zona": "🗿 Turistik zona",
        "yangi_ozbekiston_xizmat": "🏪 Yangi O'zbekiston xizmat joylari",
        "maxsus_sanoat": "🏭 Maxsus sanoat zonalari",
        "xalqaro_yol": "🛣 Xalqaro yo'llar bo'yidagi xizmat joylari",
        "nodavlat_talim": "🎓 Nodavlat ta'lim muassasalari",
        "vm63": "🏘 Uy-joy qurish (VM-63)",
        "mikromarkaz_yer": "🏘 Mikromarkazlar uchun",
        "elektromobil": "🔌 Elektromobillar quvvatlantirish",
        "master_reja": "📐 Master-reja asosida savdoga chiqarilgan",
        "hudud_master": "🗺 Hududlar uchun master-reja",
        "renovatsiya": "🔨 Renovatsiya loyihalari",
        "olis_hudud": "🏜 Olis va cho'l hududlardagi yoshlar zonalari",
        "bosh_yer_uch": "📍 Bo'sh yerlar",
    },
    
    # 4. Dehqon xo'jaligiga mo'ljallangan yer (groups_id = "24")
    "dehqon_yer": {
        "ijaraga_berish": "📋 Dehqon xo'jaligi yuritish uchun ijara",
        "kooperativ": "🤝 Qishloq xo'jaligi kooperativini tashkil etish",
        "yoshlar_dehqon": "👥 Yoshlarga dehqon xo'jaligi",
        "yangi_ozlash_pf10": "🆕 Yangi o'zlashtirilayotgan yerlar (PF-10)",
    },
    
    # 5. Qishloq xo'jaligiga mo'ljallangan yer (groups_id = "33")
    "qishloq_yer": {
        "qishloq_ijara": "📋 Qishloq xo'jaligi maqsadlari uchun ijara",
        "ekin_pf18": "🌾 Qishloq xo'jaligi ekinlarini yetishtirish (PF-18)",
        "qishloq_yangi_pf10": "🆕 Yangi o'zlashtirilayotgan yerlar (PF-10)",
    },
    
    # 6. Yer qa'ri (groups_id = "10")
    "yer_qari": {
        "oltin_izlash": "💰 Qimmatbaho metallarni izlovchilar usulida",
        "strategik": "💎 Strategik turdagi foydali qazilmalar",
        "noruda": "⛏ Noruda foydali qazilmalar",
        "uglevodorod": "🛢 Uglevodorod foydali qazilmasi",
    },
    
    # 7. Daryo o'zanlarini tozalash (groups_id = "9")
    "daryo_tozalash": {
        "daryo_ozan": "🌊 Daryolar o'zanlarini tozalash",
    },
    
    # 8. Ko'chma savdo (groups_id = "23")
    "kochma_savdo": {
        "kochma_obyekt": "🛒 Ko'chma savdo obyektlari",
    },
    
    # 9. Elektr stansiya (groups_id = "27")
    "elektr_stansiya": {
        "gidroelektr": "💧 Gidroelektr stansiyalarini qurish",
    },
    
    # 10. Mikromarkazlar (groups_id = "28")
    "mikromarkazlar": {
        "mulk_ijara": "🏢 Mikromarkazlar uchun davlat mulkini ijara",
        "yer_mikromarkaz": "🌍 Mikromarkazlar uchun yer uchastkasi",
    },
}

# REAL API FILTERS - confiscant_categories_id
CATEGORY_FILTERS = {
    # Davlat aktivlari (groups_id = "5")
    "davlat_obyekt": {"groups_id": "5", "categories_id": 27},
    "davlat_obyekt_tanlov": {"groups_id": "5", "categories_id": 121},  
    
    # Ko'chmas mulk (groups_id = "1")
    "kop_qavatli": {"groups_id": "1", "categories_id": 3},
    "turar_joy_uchastka": {"groups_id": "1", "categories_id": 2},
    "qishloq_yer": {"groups_id": "1", "categories_id": 161},
    "noturar_joy": {"groups_id": "1", "categories_id": 1}, 
    "tugallanmagan_kop": {"groups_id": "1", "categories_id": 6},  # Taxmin
    "tugallanmagan_uchastka": {"groups_id": "1", "categories_id": 5},  # Taxmin
    "tugallanmagan_bino": {"groups_id": "1", "categories_id": 4},  # Taxmin
    "bosh_yer": {"groups_id": "1", "categories_id": 39},  # Taxmin
    "boshqa_mulk": {"groups_id": "1", "categories_id": 68},  # Taxmin
    "ozogroservis": {"groups_id": "1", "categories_id": 143},  # Taxmin
    "ozagrokimyo": {"groups_id": "1", "categories_id": 99},  # Taxmin
    "davlat_obyekt_km": {"groups_id": "1", "categories_id": 27},  # Taxmin
    
    # Yer uchaskalari (groups_id = "6")
    "tadbirkorlik": {"groups_id": "6", "categories_id": 46},
    "yakka_uy": {"groups_id": "6", "categories_id": 97},  # Taxmin
    "kop_qavatli_uy": {"groups_id": "6", "categories_id": 48},  # Taxmin
    "yoshlar_zona": {"groups_id": "6", "categories_id": 69},  # Taxmin
    "ormon_fond": {"groups_id": "6", "categories_id": 124},  # Taxmin
    "yangi_toshkent": {"groups_id": "6", "categories_id": 123},  # Taxmin
    "ekoturizm": {"groups_id": "6", "categories_id": 50},  # Taxmin
    "kichik_sanoat": {"groups_id": "6", "categories_id": 72},  # Taxmin
    "erkin_zona": {"groups_id": "6", "categories_id": 73},  # Taxmin
    "yangi_ozbekiston_kop": {"groups_id": "6", "categories_id": 90},  # Taxmin
    "turistik_rekreatsion": {"groups_id": "6", "categories_id": 74},  # Taxmin
    "turistik_zona": {"groups_id": "6", "categories_id": 106},  # Taxmin
    "yangi_ozbekiston_xizmat": {"groups_id": "6", "categories_id": 92},  # Taxmin
    "maxsus_sanoat": {"groups_id": "6", "categories_id": 120},  # Taxmin
    "xalqaro_yol": {"groups_id": "6", "categories_id": 94},  # Taxmin
    "nodavlat_talim": {"groups_id": "6", "categories_id": 95},  # Taxmin
    "vm63": {"groups_id": "6", "categories_id": 37},  # Taxmin
    "mikromarkaz_yer": {"groups_id": "6", "categories_id": 98},  # Taxmin
    "elektromobil": {"groups_id": "6", "categories_id": 104},  # Taxmin
    "master_reja": {"groups_id": "6", "categories_id": 110},  # Taxmin
    "hudud_master": {"groups_id": "6", "categories_id": 160},  # Taxmin
    "renovatsiya": {"groups_id": "6", "categories_id": 181},  # Taxmin
    "olis_hudud": {"groups_id": "6", "categories_id": 182},  # Taxmin
    "bosh_yer_uch": {"groups_id": "6", "categories_id": 39},  # Taxmin
    
    # Dehqon xo'jaligi (groups_id = "24")
    "ijaraga_berish": {"groups_id": "24", "categories_id": 126},
    "kooperativ": {"groups_id": "24", "categories_id": 127},  # Taxmin
    "yoshlar_dehqon": {"groups_id": "24", "categories_id": 132},  # Taxmin
    "yangi_ozlash_pf10": {"groups_id": "24", "categories_id": 156},  # Taxmin
    
    # Qishloq xo'jaligi (groups_id = "33")
    "qishloq_ijara": {"groups_id": "33", "categories_id": 128},
    "ekin_pf18": {"groups_id": "33", "categories_id": 153},  # Taxmin
    "qishloq_yangi_pf10": {"groups_id": "33", "categories_id": 155},  # Taxmin
    
    # Yer qa'ri (groups_id = "10")
    "oltin_izlash": {"groups_id": "10", "categories_id": 38},
    "strategik": {"groups_id": "10", "categories_id": 52},  # Taxmin
    "noruda": {"groups_id": "10", "categories_id": 43},  # Taxmin
    "uglevodorod": {"groups_id": "10", "categories_id": 178},  # Taxmin
    
    # Daryo (groups_id = "9")
    "daryo_ozan": {"groups_id": "9", "categories_id": 36},
    
    # Ko'chma savdo (groups_id = "23")
    "kochma_obyekt": {"groups_id": "23", "categories_id": 86},
    
    # Elektr stansiya (groups_id = "27")
    "gidroelektr": {"groups_id": "27", "categories_id": 103},
    
    # Mikromarkazlar (groups_id = "28")
    "mulk_ijara": {"groups_id": "28", "categories_id": 105},
    "yer_mikromarkaz": {"groups_id": "28", "categories_id": 98},  # Taxmin
}

# Breadcrumb
def get_breadcrumb(main_cat: str, sub_cat: str = None) -> str:
    """Navigatsiya yo'li"""
    parts = ["E-AUKSION", "Lotlar - Yangi lotlar"]
    
    if main_cat in MAIN_CATEGORIES:
        parts.append(MAIN_CATEGORIES[main_cat].replace("🏛 ", "").replace("🏠 ", "").replace("🌍 ", "").replace("🌾 ", "").replace("🚜 ", "").replace("💎 ", "").replace("🌊 ", "").replace("🛒 ", "").replace("⚡ ", "").replace("🏘 ", ""))
    
    if sub_cat and main_cat in SUB_CATEGORIES:
        if sub_cat in SUB_CATEGORIES[main_cat]:
            cat_name = SUB_CATEGORIES[main_cat][sub_cat]
            for emoji in ["🏢", "📋", "🏡", "🌾", "🏭", "🏗", "📍", "📦", "🌱", "🧪", "🏛", "🏪", "👥", "🌲", "🏙", "🏞", "🌐", "🏖", "🗿", "🛣", "🎓", "🏘", "🔌", "📐", "🗺", "🔨", "🏜", "🤝", "🆕", "💰", "💎", "⛏", "🛢", "🌊", "🛒", "💧"]:
                cat_name = cat_name.replace(emoji + " ", "")
            parts.append(cat_name)
    
    return " || ".join(parts)