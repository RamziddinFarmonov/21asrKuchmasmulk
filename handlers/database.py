"""
UMUMIY DATABASE - TOZA VERSIYA
✅ type maydoni HAR DOIM 'sale' yoki 'rent' bo'ladi
✅ Bo'sh joylar avtomatik tozalanadi
✅ Hech qanday qo'shimcha funksiyalar yo'q
"""
import sqlite3
from contextlib import contextmanager

class Database:
    def __init__(self, db_path='objects.db'):
        self.db_path = db_path
        self._create_table()
    
    @contextmanager
    def get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()
    
    def _create_table(self):
        with self.get_connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS objects (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    type TEXT NOT NULL CHECK(type IN ('sale', 'rent')),
                    mulk_turi TEXT NOT NULL,
                    joylashuv TEXT NOT NULL,
                    narx TEXT NOT NULL,
                    izoh TEXT,
                    media TEXT,
                    viloyat TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
    
    def insert_object(self, data):
        # ✅ MUHIM: type ni HAR DOIM aniq 'sale' yoki 'rent' qilish
        obj_type = 'sale' if data['type'].strip().lower() in ['sale', 'sotish', 'sotuv'] else 'rent'
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO objects (type, mulk_turi, joylashuv, narx, izoh, media, viloyat)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                obj_type,  # ✅ HAR DOIM 'sale' yoki 'rent'
                data['mulk_turi'].strip(),
                data['joylashuv'].strip(),
                data['narx'].strip(),
                data.get('izoh', '').strip(),
                data.get('media', '').strip(),
                data.get('viloyat', '').strip()
            ))
            return cursor.lastrowid
    
    def search_objects(self, obj_type, mulk_turi, viloyat=None):
        # ✅ MUHIM: type ni aniq 'sale' yoki 'rent' qilish
        obj_type = 'sale' if obj_type.strip().lower() in ['sale', 'sotish', 'sotuv'] else 'rent'
        mulk_turi = mulk_turi.strip()
        viloyat = viloyat.strip() if viloyat else None
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            if viloyat:
                cursor.execute("""
                    SELECT * FROM objects 
                    WHERE type = ? AND mulk_turi = ? AND viloyat = ?
                    ORDER BY id DESC
                """, (obj_type, mulk_turi, viloyat))
            else:
                cursor.execute("""
                    SELECT * FROM objects 
                    WHERE type = ? AND mulk_turi = ?
                    ORDER BY id DESC
                """, (obj_type, mulk_turi))
            return [dict(row) for row in cursor.fetchall()]

db = Database()