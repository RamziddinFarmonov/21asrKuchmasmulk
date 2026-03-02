"""
Database Manager
O'zbekiston Ko'chmas Mulk va Ijara Bot
Barcha ma'lumotlar bazasi operatsiyalari
"""
import sqlite3
import logging
from datetime import datetime
from typing import Optional, List, Dict, Any

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Database bilan ishlash uchun asosiy klass"""
    
    def __init__(self, db_path: str = "objects.db"):
        self.db_path = db_path
        self.init_database()
    
    def get_connection(self):
        """Database connection olish"""
        return sqlite3.connect(self.db_path)
    
    def init_database(self):
        """Database va jadvallarni yaratish"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Ko'chmas mulk jadvali
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS kochmas_mulk (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    username TEXT,
                    full_name TEXT NOT NULL,
                    phone TEXT NOT NULL,
                    region TEXT NOT NULL,
                    property_type TEXT NOT NULL,
                    action_type TEXT NOT NULL,
                    area REAL,
                    rooms INTEGER,
                    floor INTEGER,
                    total_floors INTEGER,
                    price REAL NOT NULL,
                    description TEXT,
                    photo_id TEXT,
                    video_id TEXT,
                    address TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_active BOOLEAN DEFAULT 1
                )
            """)
            
            # Ijara jadvali
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS ijara (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    username TEXT,
                    full_name TEXT NOT NULL,
                    phone TEXT NOT NULL,
                    region TEXT NOT NULL,
                    property_type TEXT NOT NULL,
                    action_type TEXT NOT NULL,
                    area REAL,
                    rooms INTEGER,
                    floor INTEGER,
                    total_floors INTEGER,
                    monthly_price REAL NOT NULL,
                    min_rental_period TEXT,
                    description TEXT,
                    photo_id TEXT,
                    video_id TEXT,
                    address TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_active BOOLEAN DEFAULT 1
                )
            """)

            # Sevimlilar jadvali (favorites)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS favorites (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    object_id INTEGER NOT NULL,
                    object_type TEXT NOT NULL,
                    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(user_id, object_id, object_type)
                )
            """)
            
            conn.commit()
            logger.info("✅ Database initialized successfully")
    
    # ============================================================================
    # KO'CHMAS MULK METODLARI
    # ============================================================================
    
    def add_kochmas_mulk(self, data: Dict[str, Any]) -> int:
        """Yangi ko'chmas mulk qo'shish"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO kochmas_mulk (
                    user_id, username, full_name, phone, region, property_type,
                    action_type, area, rooms, floor, total_floors, price,
                    description, photo_id, video_id, address
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                data['user_id'],
                data.get('username'),
                data['full_name'],
                data['phone'],
                data['region'],
                data['property_type'],
                data['action_type'],
                data.get('area'),
                data.get('rooms'),
                data.get('floor'),
                data.get('total_floors'),
                data['price'],
                data.get('description'),
                data.get('photo_id'),
                data.get('video_id'),
                data.get('address')
            ))
            conn.commit()
            return cursor.lastrowid
    
    def get_kochmas_mulk_list(
        self,
        region: Optional[str] = None,
        property_type: Optional[str] = None,
        action_type: Optional[str] = None,
        limit: int = 10,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Ko'chmas mulk ro'yxatini olish"""
        with self.get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            query = "SELECT * FROM kochmas_mulk WHERE is_active = 1"
            params = []
            
            if region:
                query += " AND region = ?"
                params.append(region)
            
            if property_type:
                query += " AND property_type = ?"
                params.append(property_type)
            
            if action_type:
                query += " AND action_type = ?"
                params.append(action_type)
            
            query += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
            params.extend([limit, offset])
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            return [dict(row) for row in rows]
    
    def get_kochmas_mulk_by_id(self, object_id: int) -> Optional[Dict[str, Any]]:
        """ID bo'yicha ko'chmas mulk olish"""
        with self.get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM kochmas_mulk WHERE id = ?", (object_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def get_user_kochmas_mulk(self, user_id: int) -> List[Dict[str, Any]]:
        """Foydalanuvchining barcha e'lonlari"""
        with self.get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM kochmas_mulk WHERE user_id = ? AND is_active = 1 ORDER BY created_at DESC",
                (user_id,)
            )
            return [dict(row) for row in cursor.fetchall()]
    
    # ============================================================================
    # IJARA METODLARI
    # ============================================================================
    
    def add_ijara(self, data: Dict[str, Any]) -> int:
        """Yangi ijara e'loni qo'shish"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO ijara (
                    user_id, username, full_name, phone, region, property_type,
                    action_type, area, rooms, floor, total_floors, monthly_price,
                    min_rental_period, description, photo_id, video_id, address
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                data['user_id'],
                data.get('username'),
                data['full_name'],
                data['phone'],
                data['region'],
                data['property_type'],
                data['action_type'],
                data.get('area'),
                data.get('rooms'),
                data.get('floor'),
                data.get('total_floors'),
                data['monthly_price'],
                data.get('min_rental_period'),
                data.get('description'),
                data.get('photo_id'),
                data.get('video_id'),
                data.get('address')
            ))
            conn.commit()
            return cursor.lastrowid
    
    def get_ijara_list(
        self,
        region: Optional[str] = None,
        property_type: Optional[str] = None,
        action_type: Optional[str] = None,
        limit: int = 10,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Ijara e'lonlari ro'yxatini olish"""
        with self.get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            query = "SELECT * FROM ijara WHERE is_active = 1"
            params = []
            
            if region:
                query += " AND region = ?"
                params.append(region)
            
            if property_type:
                query += " AND property_type = ?"
                params.append(property_type)
            
            if action_type:
                query += " AND action_type = ?"
                params.append(action_type)
            
            query += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
            params.extend([limit, offset])
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            return [dict(row) for row in rows]
    
    def get_ijara_by_id(self, object_id: int) -> Optional[Dict[str, Any]]:
        """ID bo'yicha ijara e'lonini olish"""
        with self.get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM ijara WHERE id = ?", (object_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def get_all_kochmas(self, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """Admin view: barcha ko'chmas mulk (faol va nofaol)"""
        with self.get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM kochmas_mulk ORDER BY created_at DESC LIMIT ? OFFSET ?", (limit, offset))
            return [dict(r) for r in cursor.fetchall()]

    def get_all_ijara(self, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """Admin view: barcha ijara e'lonlari (faol va nofaol)"""
        with self.get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM ijara ORDER BY created_at DESC LIMIT ? OFFSET ?", (limit, offset))
            return [dict(r) for r in cursor.fetchall()]

    def update_kochmas_mulk(self, object_id: int, data: Dict[str, Any]) -> bool:
        """E'lonni yangilash (admin/edit)"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                fields = []
                params = []
                for k, v in data.items():
                    fields.append(f"{k} = ?")
                    params.append(v)
                params.append(object_id)
                query = f"UPDATE kochmas_mulk SET {', '.join(fields)} WHERE id = ?"
                cursor.execute(query, params)
                conn.commit()
                return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"Error updating kochmas_mulk: {e}")
            return False

    def update_ijara(self, object_id: int, data: Dict[str, Any]) -> bool:
        """Ijara e'lonini yangilash"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                fields = []
                params = []
                for k, v in data.items():
                    fields.append(f"{k} = ?")
                    params.append(v)
                params.append(object_id)
                query = f"UPDATE ijara SET {', '.join(fields)} WHERE id = ?"
                cursor.execute(query, params)
                conn.commit()
                return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"Error updating ijara: {e}")
            return False

    def search_property_by_id(self, object_id: int) -> Optional[Dict[str, Any]]:
        """Qidiruv: berilgan ID bo'yicha ijara yoki ko'chmas mulkni topish"""
        km = self.get_kochmas_mulk_by_id(object_id)
        if km:
            km['__table'] = 'kochmas_mulk'
            return km
        ij = self.get_ijara_by_id(object_id)
        if ij:
            ij['__table'] = 'ijara'
            return ij
        return None

    def get_total_users(self) -> int:
        """Foydalanuvchilar soni (distinct user_id)"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(DISTINCT user_id) FROM (SELECT user_id FROM kochmas_mulk UNION ALL SELECT user_id FROM ijara)")
            return cursor.fetchone()[0]
    
    def get_user_ijara(self, user_id: int) -> List[Dict[str, Any]]:
        """Foydalanuvchining barcha ijara e'lonlari"""
        with self.get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM ijara WHERE user_id = ? AND is_active = 1 ORDER BY created_at DESC",
                (user_id,)
            )
            return [dict(row) for row in cursor.fetchall()]
    
    # ============================================================================
    # UMUMIY METODLAR
    # ============================================================================
    
    def deactivate_object(self, table: str, object_id: int) -> bool:
        """E'lonni o'chirish (deaktivatsiya)"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    f"UPDATE {table} SET is_active = 0 WHERE id = ?",
                    (object_id,)
                )
                conn.commit()
                return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"Error deactivating object: {e}")
            return False
    
    def get_statistics(self) -> Dict[str, int]:
        """Umumiy statistika"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("SELECT COUNT(*) FROM kochmas_mulk WHERE is_active = 1")
            kochmas_count = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM ijara WHERE is_active = 1")
            ijara_count = cursor.fetchone()[0]
            
            return {
                'kochmas_mulk': kochmas_count,
                'ijara': ijara_count,
                'total': kochmas_count + ijara_count
            }
    
    # ==========================================================================
    # Favorites (sevimlilar) methods
    # ==========================================================================
    def add_favorite(self, user_id: int, object_id: int, object_type: str) -> bool:
        """Sevimlilarga e'lon qo'shish"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT OR IGNORE INTO favorites (user_id, object_id, object_type, added_at)
                    VALUES (?, ?, ?, datetime('now'))
                """, (user_id, object_id, object_type))
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Error adding favorite: {e}")
            return False

    def remove_favorite(self, user_id: int, object_id: int, object_type: str) -> bool:
        """Sevimlilardan e'lonni o'chirish"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """DELETE FROM favorites WHERE user_id = ? AND object_id = ? AND object_type = ?""",
                    (user_id, object_id, object_type)
                )
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Error removing favorite: {e}")
            return False

    def is_favorite(self, user_id: int, object_id: int, object_type: str) -> bool:
        """E'lon foydalanuvchi sevimlilarida mavjudligini tekshirish"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """SELECT 1 FROM favorites WHERE user_id = ? AND object_id = ? AND object_type = ?""",
                (user_id, object_id, object_type)
            )
            return cursor.fetchone() is not None

    def get_user_favorites(self, user_id: int, object_type: str) -> List[Dict[str, Any]]:
        """Foydalanuvchining sevimli e'lonlari"""
        with self.get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            if object_type == 'kochmas':
                cursor.execute("""
                    SELECT k.* FROM kochmas_mulk k
                    INNER JOIN favorites f ON k.id = f.object_id
                    WHERE f.user_id = ? AND f.object_type = 'kochmas' AND k.is_active = 1
                    ORDER BY f.added_at DESC
                """, (user_id,))
            else:
                cursor.execute("""
                    SELECT i.* FROM ijara i
                    INNER JOIN favorites f ON i.id = f.object_id
                    WHERE f.user_id = ? AND f.object_type = 'ijara' AND i.is_active = 1
                    ORDER BY f.added_at DESC
                """, (user_id,))
            rows = cursor.fetchall()
            return [dict(row) for row in rows]


# Global database instance
db = DatabaseManager()
