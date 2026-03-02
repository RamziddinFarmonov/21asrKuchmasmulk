"""
Auksion uchun Database modellari
YANGILANGAN: UserApplication (Mening arizalarim) qo'shildi
"""
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class LotImage:
    file_hash: str
    file_name: Optional[str] = None
    url: Optional[str] = None

    def get_url(self) -> str:
        from .config import API_IMAGES_URL
        return f"{API_IMAGES_URL}?file_hash={self.file_hash}"


@dataclass
class Lot:
    id: int
    name: str
    lot_number: str
    start_price: float
    current_price: float
    min_increment: float
    status: str
    category: str

    auction_start: Optional[datetime] = None
    auction_end: Optional[datetime] = None
    created_at: Optional[datetime] = None

    description: Optional[str] = None
    location: Optional[str] = None
    images: List[LotImage] = field(default_factory=list)

    bids_count: int = 0
    participants_count: int = 0
    views_count: int = 0

    estimated_value: Optional[float] = None
    documents: List[str] = field(default_factory=list)
    properties: Dict[str, Any] = field(default_factory=dict)
    winner_id: Optional[int] = None
    is_sold: bool = False

    @staticmethod
    def from_api_data(data: dict) -> 'Lot':
        from .utils import parse_date

        lot = Lot(
            id=data.get('id', 0),
            name=data.get('name', ''),
            lot_number=data.get('lot_number', ''),
            start_price=float(data.get('start_price', 0)),
            current_price=float(data.get('current_price', data.get('start_price', 0))),
            min_increment=float(data.get('step_summa', data.get('min_increment', 0))),
            status=(
                data.get('lot_statuses_name', {}).get('name_uz', 'upcoming')
                if isinstance(data.get('lot_statuses_name'), dict)
                else data.get('status', 'upcoming')
            ),
            category=(
                data.get('confiscant_categories_name', {}).get('name_uz', 'other')
                if isinstance(data.get('confiscant_categories_name'), dict)
                else data.get('category', 'other')
            ),
            auction_start=parse_date(data.get('start_time_str', data.get('auction_date_str'))),
            description=data.get('additional_info', data.get('description', '')),
            location=data.get('joylashgan_manzil', data.get('location', '')),
            bids_count=data.get('bids_count', 0),
            participants_count=data.get('participants_count', 0),
            estimated_value=(
                float(data.get('baholangan_narx', data.get('estimated_value', 0)))
                if data.get('baholangan_narx') or data.get('estimated_value') else None
            ),
        )

        # Properties
        if 'confiscant_details_list' in data and isinstance(data['confiscant_details_list'], list):
            properties = {}
            for detail in data['confiscant_details_list']:
                if isinstance(detail, dict):
                    name_dict = detail.get('name', {})
                    prop_name = (
                        name_dict.get('name_uz', '') if isinstance(name_dict, dict)
                        else str(detail.get('name', ''))
                    )
                    value = detail.get('detail_value_string', detail.get('detail_value', ''))
                    if prop_name and value and str(value).strip() not in ['', '-', 'null', 'None']:
                        if 'maydoni' in prop_name.lower():
                            properties['area'] = value
                        elif 'qurilgan yili' in prop_name.lower():
                            properties['year_built'] = value
                        elif 'balansda saqlovchi' in prop_name.lower() and 'nomi' in prop_name.lower():
                            properties['balance_holder'] = value
                        elif 'viloyat' in prop_name.lower():
                            properties['region'] = value
                        elif 'tuman' in prop_name.lower():
                            properties['district'] = value
                        else:
                            properties[prop_name[:50]] = str(value)[:200]
            lot.properties = properties

        # Joylashuv
        if not lot.location:
            region = data.get('region_name', {}).get('name_uz', '') if isinstance(data.get('region_name'), dict) else ''
            area   = data.get('area_name', {}).get('name_uz', '') if isinstance(data.get('area_name'), dict) else ''
            address = data.get('joylashgan_manzil', '')
            parts = [p for p in [region, area, address] if p]
            if parts:
                lot.location = ", ".join(parts)

        # Rasmlar
        if 'confiscant_images_list' in data and isinstance(data['confiscant_images_list'], list):
            for img in data['confiscant_images_list']:
                if isinstance(img, dict) and img.get('file_hash'):
                    lot.images.append(LotImage(
                        file_hash=img['file_hash'],
                        file_name=img.get('description', img.get('image_positions_name', ''))
                    ))

        return lot


# ============================================================================
# YANGI: Foydalanuvchi arizasi
# ============================================================================

@dataclass
class UserApplication:
    """
    Foydalanuvchi yuborgan ariza.
    storage ga saqlanadi → "Mening arizalarim" bo'limida ko'rinadi.
    """
    user_id: int
    lot_id: int
    lot_name: str
    lot_price: float        # Ariza vaqtidagi narx
    current_price: float    # Joriy narx (yangilanib turadi)
    name: str
    phone: str
    applied_at: datetime
    status: str = "pending"  # pending | contacted | done | cancelled

    def price_changed(self) -> bool:
        return abs(self.current_price - self.lot_price) > 0.01

    def price_diff(self) -> float:
        return self.current_price - self.lot_price


@dataclass
class UserBid:
    user_id: int
    lot_id: int
    amount: float
    timestamp: datetime
    position: int = 0


@dataclass
class UserFavorite:
    user_id: int
    lot_id: int
    added_at: datetime
    notify_enabled: bool = True


@dataclass
class UserNotification:
    user_id: int
    lot_id: int
    notify_start: bool = True
    notify_end: bool = True
    notify_outbid: bool = True
    notify_winner: bool = True


# ============================================================================
# STORAGE
# ============================================================================

class MemoryStorage:

    def __init__(self):
        self.lots: Dict[int, Lot] = {}
        self.user_bids: Dict[int, List[UserBid]] = {}
        self.user_favorites: Dict[int, List[UserFavorite]] = {}
        self.user_notifications: Dict[int, Dict[int, UserNotification]] = {}
        self.user_applications: Dict[int, List[UserApplication]] = {}
        self.cache: Dict[str, Any] = {}
        self.cache_timestamps: Dict[str, datetime] = {}

    # Lot
    def save_lot(self, lot: Lot):
        self.lots[lot.id] = lot

    def get_lot(self, lot_id: int) -> Optional[Lot]:
        return self.lots.get(lot_id)

    def get_lots_by_status(self, status: str) -> List[Lot]:
        return [l for l in self.lots.values() if l.status == status]

    # Bid
    def add_bid(self, bid: UserBid):
        self.user_bids.setdefault(bid.user_id, []).append(bid)

    def get_user_bids(self, user_id: int) -> List[UserBid]:
        return self.user_bids.get(user_id, [])

    # Favorite
    def add_favorite(self, favorite: UserFavorite):
        favs = self.user_favorites.setdefault(favorite.user_id, [])
        if not any(f.lot_id == favorite.lot_id for f in favs):
            favs.append(favorite)

    def remove_favorite(self, user_id: int, lot_id: int):
        if user_id in self.user_favorites:
            self.user_favorites[user_id] = [f for f in self.user_favorites[user_id] if f.lot_id != lot_id]

    def get_user_favorites(self, user_id: int) -> List[UserFavorite]:
        return self.user_favorites.get(user_id, [])

    def is_favorite(self, user_id: int, lot_id: int) -> bool:
        return any(f.lot_id == lot_id for f in self.get_user_favorites(user_id))

    # Application
    def add_application(self, application: UserApplication):
        apps = self.user_applications.setdefault(application.user_id, [])
        for i, app in enumerate(apps):
            if app.lot_id == application.lot_id:
                apps[i] = application
                return
        apps.append(application)

    def get_user_applications(self, user_id: int) -> List[UserApplication]:
        apps = self.user_applications.get(user_id, [])
        return sorted(apps, key=lambda a: a.applied_at, reverse=True)

    def get_application(self, user_id: int, lot_id: int) -> Optional[UserApplication]:
        for app in self.user_applications.get(user_id, []):
            if app.lot_id == lot_id:
                return app
        return None

    def update_application_price(self, lot_id: int, new_price: float):
        for apps in self.user_applications.values():
            for app in apps:
                if app.lot_id == lot_id:
                    app.current_price = new_price

    def get_all_applications_for_lot(self, lot_id: int) -> List[UserApplication]:
        result = []
        for apps in self.user_applications.values():
            result.extend(app for app in apps if app.lot_id == lot_id)
        return result

    # Notification
    def save_notification(self, notification: UserNotification):
        self.user_notifications.setdefault(notification.user_id, {})[notification.lot_id] = notification

    def get_notification(self, user_id: int, lot_id: int) -> Optional[UserNotification]:
        return self.user_notifications.get(user_id, {}).get(lot_id)

    # Cache
    def cache_set(self, key: str, value: Any, ttl: int = 300):
        self.cache[key] = value
        self.cache_timestamps[key] = datetime.now()

    def cache_get(self, key: str, ttl: int = 300) -> Optional[Any]:
        if key not in self.cache:
            return None
        elapsed = (datetime.now() - self.cache_timestamps[key]).total_seconds()
        if elapsed > ttl:
            del self.cache[key]
            del self.cache_timestamps[key]
            return None
        return self.cache[key]


storage = MemoryStorage()