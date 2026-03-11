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
# TUMANLAR (viloyat kodi → tumanlar ro'yxati)
# ============================================================================
DISTRICTS = {
    "tashkent_city": [
        "Mirobod", "Mirzo Ulug'bek", "Yakkasaroy", "Olmazor", "Yunusobod",
        "Chilonzor", "Uchtepa", "Sirg'ali", "Yashnobod", "Shayxontohur",
        "Bektimir", "Yangihayot",
    ],
    "tashkent_region": [
        "Olmaliq shahri", "Angren shahri", "Ohangaron", "Oqqo'rg'on", "Bekobod",
        "Bo'ka", "Bo'stonliq", "Zangiota", "Qibray", "Parkent", "Piskent",
        "Quyichirchiq", "O'rtachirchiq", "Chirchiq shahri", "Chinoz",
        "Yuqorichirchiq", "Yangiyo'l", "Toshkent tumani", "Nurafshon shahri", "chinoz", 
    ],
    "samarkand": [
        "Samarqand shahri", "Samarqand tumani", "Bulung'ur", "Jomboy", "Pastdarg'om",
        "Ishtixon", "Kattaqo'rg'on shahri", "Nurobod", "Oqdaryo", "Narpay",
        "Payariq", "Kattaqo'rg'on tumani", "Paxtachi", "Tayloq", "Urgut", "Qo'shrabot",
    ],
    "fergana": [
        "Marg'ilon shahri", "Farg'ona shahri", "Quvasoy shahri", "Qo'qon shahri", "Bag'dod",
        "Beshariq", "Dang'ara", "Yozyovon", "Oltiariq", "Qo'shtepa", "Rishton",
        "So'x", "Toshloq", "Uchko'prik", "Farg'ona tumani", "Furqat",
        "O'zbekiston tumani", "Quva", "Buvayda",
    ],
    "andijan": [
        "Andijon shahri", "Andijon tumani", "Asaka", "Baliqchi", "Bo'ston", "Buloqboshi",
        "Jalaquduq", "Izboskan", "Qo'rg'ontepa", "Marhamat", "Oltinko'l",
        "Paxtaobod", "Ulug'nor", "Xo'jabod", "Shahrixon", "Xonobod shahri",
    ],
    "namangan": [
        "Namangan shahri", "Kosonsoy", "Norin", "Uchqo'rg'on", "Chartoq", "Chust",
        "To'raqo'rg'on", "Pop", "Mingbuloq", "Namangan tumani", "Uychi",
        "Yangiqo'rg'on", "Davlatobod", "Yangi Namangan",
    ],
    "bukhara": [
        "Buxoro shahri", "Romitan", "Kogon tumani", "G'ijduvon", "Buxoro tumani", "Jondor",
        "Vobkent", "Peshko'", "Shofirkon", "Qorako'l", "Olot",
        "Qorovulbozor", "Kogon shahri",
    ],
    "kashkadarya": [
        "Qarshi shahri", "Shahrizabz shahri", "Shahrizabz tumani", "Kitob", "Yakkabog'",
        "Chiroqchi", "Qamashi", "G'uzor", "Qarshi tumani", "Nishon", "Koson",
        "Kasbi", "Mirishkor", "Muborak", "Dehqonobod", "Ko'kdala",
    ],
    "surkhandarya": [
        "Termiz shahri", "Oltinsoy", "Angor", "Bandixon", "Boysun", "Muzrabot",
        "Denov", "Jarqo'rg'on", "Qumqo'rg'on", "Qiziriq", "Sariosiyo",
        "Termiz tumani", "Uzun", "Sherobod", "Sho'rchi",
    ],
    "jizzakh": [
        "Jizzax shahri", "Sharof Rashidov", "G'allaorol", "Baxmal", "Paxtakor",
        "Zafarobot", "Do'stlik", "Arnasoy", "Mirzacho'l", "Zarbdor",
        "Zomin", "Forish", "Yangiobod",
    ],
    "sirdarya": [
        "Guliston shahri", "Yangiyer shahri", "Shirin shahri", "Oqoltin", "Boyovut",
        "Guliston tumani", "Sirdaryo tumani", "Sayxunobod", "Xovos", "Mirzaobod", "Sardoba",
    ],
    "navoiy": [
        "Navoiy shahri", "Zarafshon shahri", "Karmana", "Qiziltepa", "Konimex",
        "Navbahor", "Nurota", "Xatirchi", "Tomdi", "Uchquduq", "Go'zg'on shahri",
    ],
    "khorezm": [
        "Urganch shahri", "Xiva shahri", "Urganch tumani", "Xiva tumani", "Xonqa", "Shovot",
        "Bog'dot", "Yangiariq", "Yangibozor", "Gurlan",
        "Qo'shko'prik", "Xazorasp", "Tuproqqal'a",
    ],
    "karakalpakstan": [
        "Nukus shahri", "Nukus tumani", "Kegeyli", "Chimboy", "Qorao'zak",
        "Taxtako'pir", "Xo'jayli", "Shumanay", "Qonliko'l", "Taxiatosh",
        "Qo'ng'irot", "Mo'ynoq", "Amudaryo", "To'rtko'l",
        "Ellikqal'a", "Beruniy", "Bo'zatov",
    ],
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