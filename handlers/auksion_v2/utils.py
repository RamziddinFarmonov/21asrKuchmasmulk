"""
Auksion V2 - Yordamchi funksiyalar
"""
from datetime import datetime, timedelta
from typing import Optional, List, Tuple
import re

from .config import DATE_FORMAT, CURRENCY_FORMAT


def parse_date(date_str: Optional[str]) -> Optional[datetime]:
    """
    Sana satrini datetime ga o'tkazish
    
    Args:
        date_str: Sana satri (masalan: "05.02.2026 14:30")
    
    Returns:
        datetime obyekti yoki None
    """
    if not date_str:
        return None
    
    # Turli formatlarni sinash
    formats = [
        "%d.%m.%Y %H:%M",
        "%d.%m.%Y %H:%M:%S",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%dT%H:%M:%S",
        "%d.%m.%Y",
    ]
    
    for fmt in formats:
        try:
            return datetime.strptime(date_str.strip(), fmt)
        except ValueError:
            continue
    
    return None


def format_date(dt: Optional[datetime]) -> str:
    """
    Datetime ni formatlash
    
    Args:
        dt: datetime obyekti
    
    Returns:
        Formatlangan sana satri
    """
    if not dt:
        return "—"
    
    return dt.strftime(DATE_FORMAT)


def format_price(price: float) -> str:
    """
    Narxni formatlash
    
    Args:
        price: Narx
    
    Returns:
        Formatlangan narx (masalan: "1,500,000 UZS")
    """
    if price == 0:
        return "—"
    
    return CURRENCY_FORMAT.format(price)


def format_lot_detail(lot) -> str:
    """
    Lotni batafsil formatlash - TO'LIQ MA'LUMOT
    
    Args:
        lot: Lot obyekti
    
    Returns:
        Formatlangan matn
    """
    text = f"<b>{lot.name}</b>\n\n"
    
    # Lot raqami
    if lot.lot_number:
        text += f"📦 <b>Lot:</b> #{lot.lot_number}\n\n"
    
    # Joylashuv (agar mavjud bo'lsa)
    if lot.location:
        text += f"📍 <b>Joylashuv:</b> {lot.location}\n\n"
    
    # Narx ma'lumotlari
    text += "💰 <b>NARX MA'LUMOTLARI:</b>\n"
    
    if lot.start_price and lot.start_price > 0:
        text += f"├─ Boshlang'ich: {format_price(lot.start_price)}\n"
    
    if lot.current_price and lot.current_price > 0:
        text += f"├─ Joriy narx: <b>{format_price(lot.current_price)}</b>\n"
    else:
        text += f"├─ Joriy narx: {format_price(lot.start_price)}\n"
    
    if lot.min_increment and lot.min_increment > 0:
        text += f"├─ Minimal oshirish: {format_price(lot.min_increment)}\n"
    
    if lot.estimated_value and lot.estimated_value > 0:
        text += f"└─ Baho: {format_price(lot.estimated_value)}\n"
    
    text += "\n"
    
    # Vaqt ma'lumotlari (agar mavjud bo'lsa)
    if lot.auction_start:
        text += "⏰ <b>VAQT:</b>\n"
        text += f"└─ Boshlanish: {format_date(lot.auction_start)}\n\n"
    
    # Tavsif
    if lot.description:
        text += "📋 <b>TAVSIF:</b>\n"
        
        # Tavsifni tozalash va qisqartirish
        clean_desc = clean_text(lot.description)
        
        if len(clean_desc) > 500:
            # Uzun tavsif - birinchi 500 belgi
            text += f"{clean_desc[:500]}...\n\n"
        else:
            text += f"{clean_desc}\n\n"
    
    # Xususiyatlar (properties)
    if lot.properties and isinstance(lot.properties, dict):
        text += "📝 <b>XUSUSIYATLAR:</b>\n"
        
        # Muhim xususiyatlar
        important_keys = [
            'area', 'rooms', 'floor', 'total_floors', 
            'address', 'region', 'district', 'cadastral_number',
            'purpose', 'year_built', 'condition', 'size'
        ]
        
        shown = 0
        for key in important_keys:
            if key in lot.properties and lot.properties[key]:
                value = lot.properties[key]
                # Key'ni o'zbekchaga
                key_uz = {
                    'area': 'Maydoni',
                    'rooms': 'Xonalar',
                    'floor': 'Qavat',
                    'total_floors': 'Jami qavatlar',
                    'address': 'Manzil',
                    'region': 'Viloyat',
                    'district': 'Tuman',
                    'cadastral_number': 'Kadastr raqami',
                    'purpose': 'Maqsadi',
                    'year_built': 'Qurilgan yili',
                    'condition': 'Holati',
                    'size': 'Hajmi'
                }.get(key, key.title())
                
                text += f"• {key_uz}: {value}\n"
                shown += 1
        
        # Qolgan xususiyatlar (agar ko'p bo'lsa)
        if shown == 0:
            # Agar important_keys topilmasa, birinchi 5 tasini ko'rsatish
            for key, value in list(lot.properties.items())[:5]:
                if value:
                    text += f"• {key}: {value}\n"
        
        text += "\n"
    
    # Rasmlar soni
    if lot.images and len(lot.images) > 0:
        text += f"📸 <b>RASMLAR:</b> {len(lot.images)} ta\n\n"
    else:
        text += "📸 <b>RASMLAR:</b> Mavjud emas\n\n"
    
    # Qo'shimcha ma'lumot (agar bo'sh joylar bo'lsa)
    if not lot.location and not lot.description and not lot.properties:
        text += "ℹ️ <i>To'liq ma'lumot uchun rasmiy saytga tashrif buyuring:</i>\n"
        text += f"https://e-auksion.uz/lot/{lot.id}\n"
    
    return text


def paginate_list(items: List, page: int, per_page: int = 10) -> Tuple[List, int, bool, bool]:
    """
    Ro'yxatni sahifalash
    
    Args:
        items: Elementlar ro'yxati
        page: Joriy sahifa
        per_page: Sahifadagi elementlar soni
    
    Returns:
        (sahifa_elementlari, jami_sahifalar, oldingi_bor, keyingi_bor)
    """
    total = len(items)
    total_pages = (total + per_page - 1) // per_page
    
    start = (page - 1) * per_page
    end = start + per_page
    
    page_items = items[start:end]
    has_prev = page > 1
    has_next = page < total_pages
    
    return page_items, total_pages, has_prev, has_next


def clean_text(text: str) -> str:
    """
    Matnni tozalash (HTML teglar, ortiqcha bo'sh joylar)
    
    Args:
        text: Asl matn
    
    Returns:
        Tozalangan matn
    """
    # HTML teglarni olib tashlash
    text = re.sub(r'<[^>]+>', '', text)
    
    # Ortiqcha bo'sh joylarni olib tashlash
    text = re.sub(r'\s+', ' ', text)
    
    return text.strip()


def validate_price_input(text: str) -> Optional[float]:
    """
    Narx kiritishni tekshirish
    
    Args:
        text: Foydalanuvchi kiritgan matn
    
    Returns:
        Narx yoki None
    """
    # Faqat raqamlarni qoldirish
    cleaned = re.sub(r'[^\d.]', '', text)
    
    try:
        return float(cleaned)
    except ValueError:
        return None