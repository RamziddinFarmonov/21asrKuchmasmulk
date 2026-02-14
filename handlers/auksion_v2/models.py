"""
Auksion uchun Database modellari
"""
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field
from datetime import datetime
import json


@dataclass
class LotImage:
    """Lot rasmi"""
    file_hash: str
    file_name: Optional[str] = None
    url: Optional[str] = None
    
    def get_url(self) -> str:
        """Rasm URL'ini olish"""
        from .config import API_IMAGES_URL
        return f"{API_IMAGES_URL}?file_hash={self.file_hash}"


@dataclass
class Lot:
    """Auksion lot modeli"""
    id: int
    name: str
    lot_number: str
    start_price: float
    current_price: float
    min_increment: float
    status: str
    category: str
    
    # Sanalar
    auction_start: Optional[datetime] = None
    auction_end: Optional[datetime] = None
    created_at: Optional[datetime] = None
    
    # Qo'shimcha ma'lumotlar
    description: Optional[str] = None
    location: Optional[str] = None
    images: List[LotImage] = field(default_factory=list)
    
    # Statistika
    bids_count: int = 0
    participants_count: int = 0
    views_count: int = 0
    
    # Baho va hujjatlar
    estimated_value: Optional[float] = None
    documents: List[str] = field(default_factory=list)
    
    # Qo'shimcha
    properties: Dict[str, Any] = field(default_factory=dict)
    winner_id: Optional[int] = None
    is_sold: bool = False
    
    def to_dict(self) -> dict:
        """Dict formatiga o'tkazish"""
        return {
            'id': self.id,
            'name': self.name,
            'lot_number': self.lot_number,
            'start_price': self.start_price,
            'current_price': self.current_price,
            'min_increment': self.min_increment,
            'status': self.status,
            'category': self.category,
            'auction_start': self.auction_start.isoformat() if self.auction_start else None,
            'auction_end': self.auction_end.isoformat() if self.auction_end else None,
            'description': self.description,
            'location': self.location,
            'bids_count': self.bids_count,
            'participants_count': self.participants_count,
            'views_count': self.views_count,
            'estimated_value': self.estimated_value,
            'properties': self.properties,
            'winner_id': self.winner_id,
            'is_sold': self.is_sold,
        }
    
    @staticmethod
    def from_api_data(data: dict) -> 'Lot':
        """API javobidan Lot obyektini yaratish - TO'LIQ VERSIYA"""
        from .utils import parse_date
        
        # Asosiy lot yaratish
        lot = Lot(
            id=data.get('id', 0),
            name=data.get('name', ''),
            lot_number=data.get('lot_number', ''),
            start_price=float(data.get('start_price', 0)),
            current_price=float(data.get('current_price', data.get('start_price', 0))),
            min_increment=float(data.get('step_summa', data.get('min_increment', 0))),
            status=data.get('lot_statuses_name', {}).get('name_uz', 'upcoming') if isinstance(data.get('lot_statuses_name'), dict) else data.get('status', 'upcoming'),
            category=data.get('confiscant_categories_name', {}).get('name_uz', 'other') if isinstance(data.get('confiscant_categories_name'), dict) else data.get('category', 'other'),
            auction_start=parse_date(data.get('start_time_str', data.get('auction_date_str'))),
            description=data.get('additional_info', data.get('description', '')),
            location=data.get('joylashgan_manzil', data.get('location', '')),
            bids_count=data.get('bids_count', 0),
            participants_count=data.get('participants_count', 0),
            estimated_value=float(data.get('baholangan_narx', data.get('estimated_value', 0))) if data.get('baholangan_narx') or data.get('estimated_value') else None,
        )
        
        # Properties - confiscant_details_list dan
        if 'confiscant_details_list' in data and isinstance(data['confiscant_details_list'], list):
            properties = {}
            for detail in data['confiscant_details_list']:
                if isinstance(detail, dict):
                    name_dict = detail.get('name', {})
                    name = name_dict.get('name_uz', '') if isinstance(name_dict, dict) else str(detail.get('name', ''))
                    value = detail.get('detail_value_string', detail.get('detail_value', ''))
                    
                    if name and value and str(value).strip() not in ['', '-', 'null', 'None']:
                        # Maxsus xususiyatlar
                        if 'maydoni' in name.lower():
                            properties['area'] = value
                        elif 'qurilgan yili' in name.lower() or 'year' in name.lower():
                            properties['year_built'] = value
                        elif 'balansda saqlovchi' in name.lower() and 'nomi' in name.lower():
                            properties['balance_holder'] = value
                        elif 'viloyat' in name.lower() or 'region' in name.lower():
                            properties['region'] = value
                        elif 'tuman' in name.lower() or 'district' in name.lower():
                            properties['district'] = value
                        else:
                            # Boshqa barcha xususiyatlar
                            short_name = name[:50] if len(name) > 50 else name
                            properties[short_name] = str(value)[:200] if len(str(value)) > 200 else str(value)
            
            lot.properties = properties
        
        # Joylashuv - to'ldirish
        if not lot.location:
            region = data.get('region_name', {}).get('name_uz', '') if isinstance(data.get('region_name'), dict) else ''
            area = data.get('area_name', {}).get('name_uz', '') if isinstance(data.get('area_name'), dict) else ''
            address = data.get('joylashgan_manzil', '')
            
            parts = [p for p in [region, area, address] if p]
            if parts:
                lot.location = ", ".join(parts)
        
        # RASMLAR - confiscant_images_list dan!
        if 'confiscant_images_list' in data and isinstance(data['confiscant_images_list'], list):
            for img_data in data['confiscant_images_list']:
                if isinstance(img_data, dict):
                    file_hash = img_data.get('file_hash')
                    if file_hash:
                        image = LotImage(
                            file_hash=file_hash,
                            file_name=img_data.get('description', img_data.get('image_positions_name', ''))
                        )
                        lot.images.append(image)
        
        return lot


@dataclass
class UserBid:
    """Foydalanuvchi taklifi"""
    user_id: int
    lot_id: int
    amount: float
    timestamp: datetime
    position: int = 0  # Holatdagi o'rni (1, 2, 3...)
    
    def to_dict(self) -> dict:
        return {
            'user_id': self.user_id,
            'lot_id': self.lot_id,
            'amount': self.amount,
            'timestamp': self.timestamp.isoformat(),
            'position': self.position,
        }


@dataclass
class UserFavorite:
    """Foydalanuvchi sevimlilari"""
    user_id: int
    lot_id: int
    added_at: datetime
    notify_enabled: bool = True
    
    def to_dict(self) -> dict:
        return {
            'user_id': self.user_id,
            'lot_id': self.lot_id,
            'added_at': self.added_at.isoformat(),
            'notify_enabled': self.notify_enabled,
        }


@dataclass
class UserNotification:
    """Foydalanuvchi bildirish sozlamalari"""
    user_id: int
    lot_id: int
    notify_start: bool = True
    notify_end: bool = True
    notify_outbid: bool = True
    notify_winner: bool = True
    
    def to_dict(self) -> dict:
        return {
            'user_id': self.user_id,
            'lot_id': self.lot_id,
            'notify_start': self.notify_start,
            'notify_end': self.notify_end,
            'notify_outbid': self.notify_outbid,
            'notify_winner': self.notify_winner,
        }


# In-memory storage (production uchun database kerak)
class MemoryStorage:
    """Xotira asosida saqlash (development uchun)"""
    
    def __init__(self):
        self.lots: Dict[int, Lot] = {}
        self.user_bids: Dict[int, List[UserBid]] = {}
        self.user_favorites: Dict[int, List[UserFavorite]] = {}
        self.user_notifications: Dict[int, Dict[int, UserNotification]] = {}
        self.cache: Dict[str, Any] = {}
        self.cache_timestamps: Dict[str, datetime] = {}
    
    # Lot operatsiyalari
    def save_lot(self, lot: Lot):
        """Lotni saqlash"""
        self.lots[lot.id] = lot
    
    def get_lot(self, lot_id: int) -> Optional[Lot]:
        """Lotni olish"""
        return self.lots.get(lot_id)
    
    def get_lots_by_status(self, status: str) -> List[Lot]:
        """Status bo'yicha lotlar"""
        return [lot for lot in self.lots.values() if lot.status == status]
    
    # Bid operatsiyalari
    def add_bid(self, bid: UserBid):
        """Taklif qo'shish"""
        if bid.user_id not in self.user_bids:
            self.user_bids[bid.user_id] = []
        self.user_bids[bid.user_id].append(bid)
    
    def get_user_bids(self, user_id: int) -> List[UserBid]:
        """Foydalanuvchi takliflari"""
        return self.user_bids.get(user_id, [])
    
    def get_lot_bids(self, lot_id: int) -> List[UserBid]:
        """Lot bo'yicha takliflar"""
        all_bids = []
        for bids in self.user_bids.values():
            all_bids.extend([b for b in bids if b.lot_id == lot_id])
        return sorted(all_bids, key=lambda x: x.amount, reverse=True)
    
    # Favorite operatsiyalari
    def add_favorite(self, favorite: UserFavorite):
        """Sevimliga qo'shish"""
        if favorite.user_id not in self.user_favorites:
            self.user_favorites[favorite.user_id] = []
        
        # Dublikat tekshirish
        existing = [f for f in self.user_favorites[favorite.user_id] if f.lot_id == favorite.lot_id]
        if not existing:
            self.user_favorites[favorite.user_id].append(favorite)
    
    def remove_favorite(self, user_id: int, lot_id: int):
        """Sevimlilardan o'chirish"""
        if user_id in self.user_favorites:
            self.user_favorites[user_id] = [
                f for f in self.user_favorites[user_id] if f.lot_id != lot_id
            ]
    
    def get_user_favorites(self, user_id: int) -> List[UserFavorite]:
        """Foydalanuvchi sevimlilari"""
        return self.user_favorites.get(user_id, [])
    
    def is_favorite(self, user_id: int, lot_id: int) -> bool:
        """Sevimli ekanligini tekshirish"""
        favorites = self.get_user_favorites(user_id)
        return any(f.lot_id == lot_id for f in favorites)
    
    # Notification operatsiyalari
    def save_notification(self, notification: UserNotification):
        """Bildirishnoma sozlamalarini saqlash"""
        if notification.user_id not in self.user_notifications:
            self.user_notifications[notification.user_id] = {}
        self.user_notifications[notification.user_id][notification.lot_id] = notification
    
    def get_notification(self, user_id: int, lot_id: int) -> Optional[UserNotification]:
        """Bildirishnoma sozlamalarini olish"""
        return self.user_notifications.get(user_id, {}).get(lot_id)
    
    # Cache operatsiyalari
    def cache_set(self, key: str, value: Any, ttl: int = 300):
        """Keshga saqlash"""
        self.cache[key] = value
        self.cache_timestamps[key] = datetime.now()
    
    def cache_get(self, key: str, ttl: int = 300) -> Optional[Any]:
        """Keshdan olish"""
        if key not in self.cache:
            return None
        
        timestamp = self.cache_timestamps.get(key)
        if timestamp:
            elapsed = (datetime.now() - timestamp).total_seconds()
            if elapsed > ttl:
                del self.cache[key]
                del self.cache_timestamps[key]
                return None
        
        return self.cache.get(key)


# Global storage instance
storage = MemoryStorage()