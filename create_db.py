import sqlite3

# Yangi toza ma'lumotlar bazasini yaratish
conn = sqlite3.connect('objects.db')
cursor = conn.cursor()

# Jadvalni yaratish
cursor.execute("""
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

conn.commit()
conn.close()

print("✅ MA'LUMOTLAR BAZASI MUVAFFAQIYATLI YARATILDI!")
print("✅ Jadval strukturasi toza va to'g'ri.")