import sqlite3

print("="*60)
print("DEBUG: MA'LUMOTLAR BAZASI HOLATI")
print("="*60)

try:
    conn = sqlite3.connect('objects.db')
    cursor = conn.cursor()
    
    # 1. Jadval mavjudligini tekshirish
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='objects'")
    if not cursor.fetchone():
        print("❌ XATO: 'objects' jadvali mavjud emas!")
        conn.close()
        exit(1)
    
    print("✅ Jadval mavjud")
    
    # 2. Ma'lumotlarni ko'rish
    cursor.execute("SELECT COUNT(*) FROM objects")
    total = cursor.fetchone()[0]
    print(f"\n📊 Jami obyektlar: {total} ta")
    
    if total > 0:
        print("\n📋 Obyektlar (so'nggi 5 ta):")
        cursor.execute("SELECT id, type, mulk_turi, viloyat FROM objects ORDER BY id DESC LIMIT 5")
        for row in cursor.fetchall():
            print(f"  ID={row[0]}, type='{row[1]}', mulk_turi='{row[2]}', viloyat='{row[3]}'")
    
    # 3. Bo'sh joylarni tekshirish
    cursor.execute("""
        SELECT COUNT(*) FROM objects 
        WHERE type LIKE '% ' OR mulk_turi LIKE '% ' OR viloyat LIKE '% '
    """)
    bad_rows = cursor.fetchone()[0]
    
    if bad_rows > 0:
        print(f"\n❌ XATO: {bad_rows} ta obyektda BO'SH JOY mavjud!")
        print("   Bu muammoning asosiy sababi!")
    else:
        print("\n✅ BO'SH JOY YO'Q - Ma'lumotlar toza")
    
    # 4. Type distributsiyasi
    print("\n📊 Type bo'yicha taqsimot:")
    cursor.execute("SELECT type, COUNT(*) FROM objects GROUP BY type")
    for row in cursor.fetchall():
        print(f"  • {row[0]}: {row[1]} ta")
    
    conn.close()
    print("\n✅ TEKSHIRUV TUGADI")
    
except Exception as e:
    print(f"\n❌ XATOLIK: {e}")

input("\nDavom etish uchun Enter tugmasini bosing...")