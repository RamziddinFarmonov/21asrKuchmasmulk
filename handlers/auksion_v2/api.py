"""
E-Auksion.uz V2 - API Client (REAL FORMAT)
E-auksion.uz formatiga mos
"""
import aiohttp
import logging
import json
from typing import Optional, List, Dict, Any
from datetime import datetime

from .config import API_BASE_URL, API_HEADERS, ITEMS_PER_PAGE
from .models import Lot, LotImage, storage

logger = logging.getLogger(__name__)


class AuksionAPIV2:
    """E-Auksion.uz API client - real format"""
    
    def __init__(self):
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """HTTP session yaratish"""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession(headers=API_HEADERS)
        return self.session
    
    async def close(self):
        """Session yopish"""
        if self.session and not self.session.closed:
            await self.session.close()
    
    async def get_lots_by_category(
        self,
        groups_id: str,
        categories_id: int,
        page: int = 1,
        per_page: int = ITEMS_PER_PAGE,
        region_id: int = None,
    ) -> List[Lot]:
        """
        Kategoriya bo'yicha lotlarni olish (E-auksion.uz format)
        
        Args:
            groups_id: confiscant_groups_id (masalan: "1", "5", "6")
            categories_id: confiscant_categories_id (masalan: 3, 27, 46)
            page: Sahifa raqami
            per_page: Sahifadagi elementlar soni
            region_id: Viloyat ID (agar kerak bo'lsa)
        """
        session = await self._get_session()
        
        # E-auksion.uz REAL format
        payload = {
            "sort_type": 1,
            "confiscant_groups_id": groups_id,
            "confiscant_categories_id": categories_id,
            "regions_id": region_id,  # YANGI - viloyat filtri
            "areas_id": None,
            "auction_type": 0,
            "current_page": page,
            "per_page": per_page,
            "date_from": None,
            "date_to": None,
            "dynamic_filters": [],
            "exec_order_type": 0,
            "filtered_auction_status": 0,
            "finished_auction_status": 0,
            "hashtag": "",
            "is_ownership": -1,
            "is_term_order": -1,
            "lot_number": "",
            "lot_type": 0,
            "mahallas_id": None,
            "orderby_": 0,
            "address": "",
            "zz_md5": "d7431a0a032c91d10d97ceac59425f9d"
        }
        
        logger.info(f"📤 API Request: groups_id={groups_id}, categories_id={categories_id}, region_id={region_id}")
        
        try:
            async with session.post(f"{API_BASE_URL}/lots", json=payload) as response:
                if response.status != 200:
                    logger.error(f"❌ API xatolik: {response.status}")
                    response_text = await response.text()
                    logger.error(f"Response: {response_text[:500]}")
                    return []
                
                data = await response.json()
                rows = data.get("rows", [])
                
                logger.info(f"✅ API Success: {len(rows)} ta lot topildi")
                
                lots = []
                for row in rows:
                    # Faqat aktiv lotlar
                    status = row.get("status", "")
                    if status == "finished" or status == "completed":
                        continue
                    
                    lot = Lot.from_api_data(row)
                    storage.save_lot(lot)
                    lots.append(lot)
                
                logger.info(f"📦 Aktiv lotlar: {len(lots)} ta")
                return lots
                
        except Exception as e:
            logger.error(f"❌ Lotlarni olishda xato: {e}", exc_info=True)
            return []
    
    async def get_lots_by_category_and_region(
        self,
        groups_id: str,
        categories_id: int,
        region_id: int = None,
        page: int = 1
    ) -> List[Lot]:
        """Viloyat bilan filter - sodda wrapper"""
        return await self.get_lots_by_category(
            groups_id=groups_id,
            categories_id=categories_id,
            region_id=region_id,
            page=page
        )
    
    async def get_lot_detail(self, lot_id: int) -> Optional[Lot]:
        """Lot batafsil ma'lumotlarini olish"""
        session = await self._get_session()
        
        try:
            url = f"{API_BASE_URL}/lot-info"
            params = {"lot_id": lot_id, "lang": "uz"}
            
            logger.info(f"📤 Lot detail request: {lot_id}")
            
            async with session.get(url, params=params) as response:
                if response.status != 200:
                    logger.error(f"❌ Lot {lot_id} uchun xatolik: {response.status}")
                    return None
                
                data = await response.json()
                lot = Lot.from_api_data(data)
                
                # Rasmlarni qo'shish
                images_data = data.get("images", []) + data.get("gallery", [])
                
                if data.get("file_hash"):
                    images_data.insert(0, {
                        "file_hash": data["file_hash"],
                        "file_name": "main_image"
                    })
                
                for img_data in images_data:
                    if img_data.get("file_hash"):
                        image = LotImage(
                            file_hash=img_data["file_hash"],
                            file_name=img_data.get("file_name")
                        )
                        lot.images.append(image)
                
                storage.save_lot(lot)
                logger.info(f"✅ Lot {lot_id} detail: {len(lot.images)} ta rasm")
                
                return lot
                
        except Exception as e:
            logger.error(f"❌ Lot {lot_id} ma'lumotlarini olishda xato: {e}")
            return None
    
    async def search_lots(self, query: str) -> List[Lot]:
        """Lotlarni qidirish"""
        session = await self._get_session()
        
        payload = {
            "sort_type": 1,
            "confiscant_groups_id": None,
            "confiscant_categories_id": None,
            "regions_id": None,
            "areas_id": None,
            "auction_type": 0,
            "current_page": 1,
            "per_page": 50,
            "date_from": None,
            "date_to": None,
            "dynamic_filters": [],
            "exec_order_type": 0,
            "filtered_auction_status": 0,
            "finished_auction_status": 0,
            "hashtag": query,  # Search
            "is_ownership": -1,
            "is_term_order": -1,
            "lot_number": "",
            "lot_type": 0,
            "mahallas_id": None,
            "orderby_": 0,
            "address": query,  # Search
            "zz_md5": "d7431a0a032c91d10d97ceac59425f9d"
        }
        
        logger.info(f"🔍 Search request: '{query}'")
        
        try:
            async with session.post(f"{API_BASE_URL}/lots", json=payload) as response:
                if response.status != 200:
                    logger.error(f"❌ Search xatolik: {response.status}")
                    return []
                
                data = await response.json()
                rows = data.get("rows", [])
                
                logger.info(f"✅ Search natija: {len(rows)} ta lot")
                
                lots = []
                for row in rows:
                    status = row.get("status", "")
                    if status == "finished" or status == "completed":
                        continue
                    
                    lot = Lot.from_api_data(row)
                    storage.save_lot(lot)
                    lots.append(lot)
                
                return lots
                
        except Exception as e:
            logger.error(f"❌ Qidirishda xato: {e}")
            return []


# Global API instance
api_client = AuksionAPIV2()