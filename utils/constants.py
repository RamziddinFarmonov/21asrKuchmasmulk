"""
Constants va Konfiguratsiya
O'zbekiston viloyatlari, mulk turlari va boshqa konstantalar
"""

# ============================================================================
# O'ZBEKISTON VILOYATLARI
# ============================================================================
REGIONS = {
    "🏛️ Toshkent shahri": "tashkent_city",
    "🏞️ Toshkent viloyati": "tashkent_region",
    "🕌 Samarqand": "samarkand",
    "🏔️ Farg'ona": "fergana",
    "🌾 Andijon": "andijan",
    "🏜️ Namangan": "namangan",
    "🏰 Buxoro": "bukhara",
    "🌆 Xorazm": "khorezm",
    "🏞️ Qashqadaryo": "kashkadarya",
    "🌄 Surxondaryo": "surkhandarya",
    "🏔️ Jizzax": "jizzakh",
    "🌾 Sirdaryo": "sirdarya",
    "🏜️ Navoiy": "navoiy",
    "🏛️ Qoraqalpog'iston": "karakalpakstan"
}

# ============================================================================
# KO'CHMAS MULK TURLARI
# ============================================================================
PROPERTY_TYPES = {
    "🏢 Ko'p qavatli uy": "apartment",
    "🏡 Hovli": "house",
    "🏬 Savdo do'koni": "shop",
    "🗺️ Yer uchastkasi": "land"
}

# ============================================================================
# IJARA TURLARI
# ============================================================================
RENTAL_TYPES = {
    "🏢 Ko'p qavatli uy": "apartment",
    "🏡 Hovli": "house",
    "🏬 Savdo do'koni": "shop",
    "🏨 Mehmonxona": "hotel",
    "📄 Boshqa ijara joylari": "other"
}

# ============================================================================
# AMAL TURLARI
# ============================================================================
ACTION_TYPES = {
    "sotish": "sell",
    "sotib_olish": "buy",
    "ijaraga_berish": "rent_out",
    "ijaraga_olish": "rent_in"
}

# ============================================================================
# IJARA MUDDATLARI
# ============================================================================
RENTAL_PERIODS = [
    "1 oy",
    "3 oy",
    "6 oy",
    "1 yil",
    "1 yildan ko'p",
    "Muhim emas"
]

# ============================================================================
# FORMAT FUNKSIYALARI
# ============================================================================

def format_price(price: float) -> str:
    """Narxni formatlash"""
    if price >= 1_000_000_000:
        return f"{price / 1_000_000_000:.1f} mlrd so'm"
    elif price >= 1_000_000:
        return f"{price / 1_000_000:.1f} mln so'm"
    else:
        return f"{int(price):,} so'm".replace(",", " ")


def format_area(area: float) -> str:
    """Maydonni formatlash"""
    return f"{area:.1f} m²"


def get_region_name_by_code(code: str) -> str:
    """Kod bo'yicha viloyat nomini olish"""
    for name, c in REGIONS.items():
        if c == code:
            return name
    return code


def get_property_type_name_by_code(code: str) -> str:
    """Kod bo'yicha mulk turi nomini olish"""
    for name, c in PROPERTY_TYPES.items():
        if c == code:
            return name
    for name, c in RENTAL_TYPES.items():
        if c == code:
            return name
    return code


def validate_phone(phone: str) -> bool:
    """Telefon raqamni tekshirish"""
    # +998 XX XXX XX XX format
    import re
    pattern = r'^\+998\d{9}$'
    return bool(re.match(pattern, phone.replace(' ', '')))


def format_phone(phone: str) -> str:
    """Telefon raqamni formatlash"""
    # Faqat raqamlarni qoldirish
    digits = ''.join(filter(str.isdigit, phone))
    
    # +998 bilan boshlash
    if len(digits) == 12 and digits.startswith('998'):
        return f"+{digits[:3]} {digits[3:5]} {digits[5:8]} {digits[8:10]} {digits[10:]}"
    elif len(digits) == 9:
        return f"+998 {digits[:2]} {digits[2:5]} {digits[5:7]} {digits[7:]}"
    else:
        return phone
