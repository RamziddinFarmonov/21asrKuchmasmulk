import requests
import os
import json
import re

BASE_URL = "https://e-auksion.uz/api/front"
IMAGES_DIR = "lots"

os.makedirs(IMAGES_DIR, exist_ok=True)

session = requests.Session()
HEADERS = {
    "accept": "application/json, text/plain, */*",
    "content-type": "application/json",
    "user-agent": "Mozilla/5.0",
}
session.headers.update(HEADERS)

# Windows uchun xavfsiz papka nomi
def safe_name(name: str) -> str:
    return re.sub(r'[\\/*?:"<>|]', "_", name)

# Lotlar ro'yxatini olish
list_payload = {
    "sort_type": 1,
    "current_page": 1,
    "per_page": 10,
    "dynamic_filters": [],
    "zz_md5": "002dbae2d22e633767809edb7732a868"
}

rows = session.post(f"{BASE_URL}/lots", json=list_payload).json().get("rows", [])

if not rows:
    print("❌ Lotlar topilmadi")
    exit()

for lot in rows:
    lot_id = lot["id"]
    lot_name = lot.get("name", "Noma'lum")
    lot_folder = os.path.join(IMAGES_DIR, f"lot{lot_id}")
    os.makedirs(lot_folder, exist_ok=True)
    print(f"\n📂 Lot: {lot_id} — {lot_name}")

    # 1️⃣ Eng asosiy lot ma'lumotlari
    main_info = {
        "id": lot_id,
        "name": lot_name,
        "lot_number": lot.get("lot_number"),
        "start_price": lot.get("start_price"),
        "auction_date_str": lot.get("auction_date_str"),
        "file_hash": lot.get("file_hash")
    }

    # JSON saqlash
    json_path = os.path.join(lot_folder, "info.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(main_info, f, ensure_ascii=False, indent=2)
    print(f"📄 Lot info saqlandi: {json_path}")

    # 2️⃣ Rasmlar papkasi
    images_folder = os.path.join(lot_folder, "images")
    os.makedirs(images_folder, exist_ok=True)

    # Batafsil lot ma'lumotlarini olish (gallery + images)
    detail_data = session.get(f"{BASE_URL}/lot-info?lot_id={lot_id}&lang=uz").json()
    images = detail_data.get("images", []) + detail_data.get("gallery", [])

    # Main image agar mavjud bo'lsa
    if lot.get("file_hash"):
        images.append({"file_hash": lot["file_hash"], "file_name": "main_image"})

    # Rasmlarni yuklash
    for idx, img in enumerate(images, start=1):
        file_hash = img.get("file_hash")
        if not file_hash:
            continue
        filename = img.get("file_name") or f"image_{idx}"
        filename = safe_name(filename)

        url = f"https://newfiles.e-auksion.uz/files-worker/api/v1/images?file_hash={file_hash}"
        try:
            resp = session.get(url, timeout=20)
            if resp.status_code == 200:
                ext = "jpg"
                content_type = resp.headers.get("content-type", "")
                if "png" in content_type:
                    ext = "png"
                file_path = os.path.join(images_folder, f"{filename}.{ext}")
                with open(file_path, "wb") as f:
                    f.write(resp.content)
                print(f"✅ Rasm yuklandi: {file_path}")
            else:
                print(f"❌ Rasm yuklanmadi: {url} - Status {resp.status_code}")
        except Exception as e:
            print(f"❌ Xato rasm yuklashda: {url} - {e}")
