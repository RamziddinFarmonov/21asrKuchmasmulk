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
# ============================================================================
# TUMANLAR — To'liq ro'yxat (txt fayldan, 209 ta tuman/shahar)
# Viloyat kodi → tumanlar/shaharlar ro'yxati
# ============================================================================
DISTRICTS = {
    "tashkent_city": [
        "Mirobod tumani", "Mirzo Ulug'bek tumani", "Yakkasaroy tumani",
        "Olmazor tumani", "Yunusobod tumani", "Chilonzor tumani",
        "Uchtepa tumani", "Sirg'ali tumani", "Yashnobod tumani",
        "Shayxontohur tumani", "Bektimir tumani", "Yangihayot tumani",
        "Yangi Toshkent shahri",
    ],
    "tashkent_region": [
        "Olmaliq shahri", "Angren shahri", "Bekobod shahri",
        "Ohangaron shahri", "Chirchiq shahri", "Yangiyo'l shahri",
        "Nurafshon shahri", "Oqqo'rg'on tumani", "Ohangaron tumani",
        "Bekobod tumani", "Bo'ka tumani", "Bo'stonliq tumani",
        "Zangiota tumani", "Qibray tumani", "Parkent tumani",
        "Piskent tumani", "Quyichirchiq tumani", "O'rtachirchiq tumani",
        "Chinoz tumani", "Yuqorichirchiq tumani", "Yangiyo'l tumani",
        "Toshkent tumani",
    ],
    "samarkand": [
        "Samarqand shahri", "Kattaqo'rg'on shahri",
        "Samarqand tumani", "Bulung'ur tumani", "Jomboy tumani",
        "Pastdarg'om tumani", "Ishtixon tumani", "Nurobod tumani",
        "Oqdaryo tumani", "Narpay tumani", "Payariq tumani",
        "Kattaqo'rg'on tumani", "Paxtachi tumani", "Tayloq tumani",
        "Urgut tumani", "Qo'shrabot tumani",
    ],
    "fergana": [
        "Farg'ona shahri", "Qo'qon shahri", "Quvasoy shahri", "Marg'ilon shahri",
        "Bag'dod tumani", "Beshariq tumani", "Dang'ara tumani",
        "Yozyovon tumani", "Oltiariq tumani", "Qo'shtepa tumani",
        "Rishton tumani", "So'x tumani", "Toshloq tumani",
        "Uchko'prik tumani", "Farg'ona tumani", "Furqat tumani",
        "O'zbekiston tumani", "Quva tumani", "Buvayda tumani",
    ],
    "andijan": [
        "Andijon shahri", "Xonobod shahri",
        "Andijon tumani", "Asaka tumani", "Baliqchi tumani",
        "Bo'ston tumani", "Buloqboshi tumani", "Jalaquduq tumani",
        "Izboskan tumani", "Qo'rg'ontepa tumani", "Marhamat tumani",
        "Oltinko'l tumani", "Paxtaobod tumani", "Ulug'nor tumani",
        "Xo'jabod tumani", "Shahrixon tumani",
    ],
    "namangan": [
        "Namangan shahri",
        "Kosonsoy tumani", "Norin tumani", "Uchqo'rg'on tumani",
        "Chartoq tumani", "Chust tumani", "To'raqo'rg'on tumani",
        "Pop tumani", "Mingbuloq tumani", "Namangan tumani",
        "Uychi tumani", "Yangiqo'rg'on tumani", "Davlatobod tumani",
        "Yangi Namangan tumani",
    ],
    "bukhara": [
        "Buxoro shahri", "Kogon shahri",
        "Romitan tumani", "Kogon tumani", "G'ijduvon tumani",
        "Buxoro tumani", "Jondor tumani", "Vobkent tumani",
        "Peshko' tumani", "Shofirkon tumani", "Qorako'l tumani",
        "Olot tumani", "Qorovulbozor tumani",
    ],
    "kashkadarya": [
        "Qarshi shahri", "Shahrizabz shahri",
        "Shahrizabz tumani", "Kitob tumani", "Yakkabog' tumani",
        "Chiroqchi tumani", "Qamashi tumani", "G'uzor tumani",
        "Qarshi tumani", "Nishon tumani", "Koson tumani",
        "Kasbi tumani", "Mirishkor tumani", "Muborak tumani",
        "Dehqonobod tumani", "Ko'kdala tumani",
    ],
    "surkhandarya": [
        "Termiz shahri",
        "Oltinsoy tumani", "Angor tumani", "Bandixon tumani",
        "Boysun tumani", "Muzrabot tumani", "Denov tumani",
        "Jarqo'rg'on tumani", "Qumqo'rg'on tumani", "Qiziriq tumani",
        "Sariosiyo tumani", "Termiz tumani", "Uzun tumani",
        "Sherobod tumani", "Sho'rchi tumani",
    ],
    "jizzakh": [
        "Jizzax shahri",
        "Sharof Rashidov tumani", "G'allaorol tumani", "Baxmal tumani",
        "Paxtakor tumani", "Zafarobot tumani", "Do'stlik tumani",
        "Arnasoy tumani", "Mirzacho'l tumani", "Zarbdor tumani",
        "Zomin tumani", "Forish tumani", "Yangiobod tumani",
    ],
    "sirdarya": [
        "Guliston shahri", "Yangiyer shahri", "Shirin shahri",
        "Oqoltin tumani", "Boyovut tumani", "Guliston tumani",
        "Sirdaryo tumani", "Sayxunobod tumani", "Xovos tumani",
        "Mirzaobod tumani", "Sardoba tumani",
    ],
    "navoiy": [
        "Navoiy shahri", "Zarafshon shahri", "Go'zg'on shahri",
        "Karmana tumani", "Qiziltepa tumani", "Konimex tumani",
        "Navbahor tumani", "Nurota tumani", "Xatirchi tumani",
        "Tomdi tumani", "Uchquduq tumani",
    ],
    "khorezm": [
        "Urganch shahri", "Xiva shahri",
        "Urganch tumani", "Xiva tumani", "Xonqa tumani",
        "Shovot tumani", "Bog'dot tumani", "Yangiariq tumani",
        "Yangibozor tumani", "Gurlan tumani",
        "Qo'shko'prik tumani", "Xazorasp tumani", "Tuproqqal'a tumani",
    ],
    "karakalpakstan": [
        "Nukus shahri",
        "Nukus tumani", "Kegeyli tumani", "Chimboy tumani",
        "Qorao'zak tumani", "Taxtako'pir tumani", "Xo'jayli tumani",
        "Shumanay tumani", "Qonliko'l tumani", "Taxiatosh tumani",
        "Qo'ng'irot tumani", "Mo'ynoq tumani", "Amudaryo tumani",
        "To'rtko'l tumani", "Ellikqal'a tumani", "Beruniy tumani",
        "Bo'zatov tumani",
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