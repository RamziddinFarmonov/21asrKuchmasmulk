"""
E-Auksion.uz V2 - Yangi konfiguratsiya
"""

# API endpoints
API_BASE_URL = "https://e-auksion.uz/api/front"
API_IMAGES_URL = "https://newfiles.e-auksion.uz/files-worker/api/v1/images"

# API headers
API_HEADERS = {
    "accept": "application/json, text/plain, */*",
    "content-type": "application/json",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
}

# Pagination
ITEMS_PER_PAGE = 10
MAX_IMAGES_PER_LOT = 20

# Cache vaqti (soniyalarda)
CACHE_TTL = 300  # 5 daqiqa (faqat yaqinlashayotgan lotlar uchun)

# Format
DATE_FORMAT = "%d.%m.%Y %H:%M"
CURRENCY_FORMAT = "{:,.0f} UZS"

# Emojis
EMOJI_BACK = "🔙"
EMOJI_FAVORITE = "⭐"
EMOJI_UNFAVORITE = "🗑"
EMOJI_SEARCH = "🔍"
EMOJI_INFO = "ℹ️"
EMOJI_APPLY = "📤"
EMOJI_IMAGES = "📸"
EMOJI_ADMIN = "👨‍💼"

# Admin sozlamalari (sizning admin ID'ingiz)
ADMIN_USER_IDS = []  # .env dan olinadi

# Ariza matni
APPLICATION_TEMPLATE = """
🆕 <b>YANGI ARIZA!</b>

👤 <b>Foydalanuvchi:</b>
├─ ID: {user_id}
├─ Ism: {full_name}
└─ Username: @{username}

📦 <b>Lot:</b>
├─ ID: {lot_id}
├─ Nomi: {lot_name}
├─ Narx: {lot_price}
└─ Link: {lot_link}

📅 <b>Sana:</b> {date}

💬 <b>Izoh:</b>
{comment}
"""

# Success messages
MSG_APPLICATION_SENT = """
✅ <b>Arizangiz muvaffaqiyatli yuborildi!</b>

Tez orada administrator siz bilan bog'lanadi.

📦 Lot: {lot_name}
💰 Narx: {lot_price}

Rahmat! 🙏
"""

# Error messages
MSG_NO_LOTS = "❌ Bu kategoriyada hozircha lotlar yo'q."
MSG_LOT_NOT_FOUND = "❌ Lot topilmadi yoki o'chirilgan."
MSG_ERROR = "❌ Xatolik yuz berdi. Keyinroq urinib ko'ring."