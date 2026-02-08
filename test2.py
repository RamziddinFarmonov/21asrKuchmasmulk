"""
Auksion moduli uchun test
"""
import asyncio
import sys
import os

# Parent directory'ni path'ga qo'shish
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from handlers.auksion_v2.api import api_client
from handlers.auksion_v2.models import Lot, storage
from handlers.auksion_v2.utils import format_lot_short, format_lot_detail, format_price


async def test_api():
    """API ni test qilish"""
    print("=" * 60)
    print("E-AUKSION.UZ API TEST")
    print("=" * 60)
    
    try:
        # 1. Jonli auksionlar
        print("\n🔴 JONLI AUKSIONLAR:")
        print("-" * 60)
        live_lots = await api_client.get_live_lots(page=1)
        
        if live_lots:
            print(f"✅ {len(live_lots)} ta jonli auksion topildi\n")
            for i, lot in enumerate(live_lots[:3], 1):
                print(f"{i}. {lot.name}")
                print(f"   💰 Narx: {format_price(lot.current_price)}")
                print(f"   📦 Lot #: {lot.lot_number}")
                print()
        else:
            print("❌ Jonli auksionlar topilmadi\n")
        
        # 2. Yaqinlashayotgan
        print("\n⏰ YAQINLASHAYOTGAN AUKSIONLAR:")
        print("-" * 60)
        upcoming_lots = await api_client.get_upcoming_lots(page=1)
        
        if upcoming_lots:
            print(f"✅ {len(upcoming_lots)} ta yaqinlashayotgan auksion topildi\n")
            for i, lot in enumerate(upcoming_lots[:3], 1):
                print(f"{i}. {lot.name}")
                print(f"   💰 Boshlang'ich narx: {format_price(lot.start_price)}")
                print(f"   📦 Lot #: {lot.lot_number}")
                print()
        else:
            print("❌ Yaqinlashayotgan auksionlar topilmadi\n")
        
        # 3. Batafsil ma'lumot
        if live_lots:
            print("\n📋 BATAFSIL MA'LUMOT:")
            print("-" * 60)
            test_lot_id = live_lots[0].id
            lot_detail = await api_client.get_lot_detail(test_lot_id)
            
            if lot_detail:
                print(f"✅ Lot #{lot_detail.lot_number} batafsil ma'lumoti:\n")
                print(format_lot_detail(lot_detail))
                print(f"\n📸 Rasmlar: {len(lot_detail.images)} ta")
            else:
                print(f"❌ Lot {test_lot_id} topilmadi")
        
        # 4. Qidiruv
        print("\n\n🔍 QIDIRUV TESTI:")
        print("-" * 60)
        search_results = await api_client.search_lots(query="ko'chmas")
        
        if search_results:
            print(f"✅ 'ko'chmas' so'zi bo'yicha {len(search_results)} ta natija topildi\n")
            for i, lot in enumerate(search_results[:3], 1):
                print(f"{i}. {lot.name[:50]}...")
                print(f"   💰 {format_price(lot.current_price)}")
                print()
        else:
            print("❌ Qidiruv natijalari yo'q\n")
        
        # 5. Storage test
        print("\n💾 STORAGE TESTI:")
        print("-" * 60)
        
        if live_lots:
            test_lot = live_lots[0]
            storage.save_lot(test_lot)
            retrieved = storage.get_lot(test_lot.id)
            
            if retrieved:
                print(f"✅ Lot saqlandi va muvaffaqiyatli olindi")
                print(f"   ID: {retrieved.id}")
                print(f"   Nomi: {retrieved.name}")
            else:
                print("❌ Lotni qayta olishda xato")
        
        print("\n" + "=" * 60)
        print("✅ BARCHA TESTLAR MUVAFFAQIYATLI O'TDI!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ XATOLIK: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Session yopish
        await api_client.close()


async def test_models():
    """Modellarni test qilish"""
    print("\n\n" + "=" * 60)
    print("MODELS TEST")
    print("=" * 60)
    
    from datetime import datetime
    from handlers.auksion_v2.models import Lot, UserBid, UserFavorite, storage
    
    # Test lot yaratish
    test_lot = Lot(
        id=99999,
        name="Test Ko'chmas Mulk",
        lot_number="TEST-001",
        start_price=500000000,
        current_price=550000000,
        min_increment=5000000,
        status="live",
        category="real_estate",
        bids_count=5,
        participants_count=3,
    )
    
    print("\n1. Lot yaratish va saqlash:")
    storage.save_lot(test_lot)
    retrieved = storage.get_lot(test_lot.id)
    print(f"   ✅ Lot saqlandi: {retrieved.name}")
    
    print("\n2. Taklif qo'shish:")
    bid1 = UserBid(
        user_id=12345,
        lot_id=test_lot.id,
        amount=560000000,
        timestamp=datetime.now(),
    )
    storage.add_bid(bid1)
    user_bids = storage.get_user_bids(12345)
    print(f"   ✅ Taklif qo'shildi: {len(user_bids)} ta taklif")
    
    print("\n3. Sevimliga qo'shish:")
    fav = UserFavorite(
        user_id=12345,
        lot_id=test_lot.id,
        added_at=datetime.now(),
    )
    storage.add_favorite(fav)
    is_fav = storage.is_favorite(12345, test_lot.id)
    print(f"   ✅ Sevimli: {is_fav}")
    
    print("\n4. Sevimlilardan o'chirish:")
    storage.remove_favorite(12345, test_lot.id)
    is_fav_after = storage.is_favorite(12345, test_lot.id)
    print(f"   ✅ O'chirildi. Hozir sevimli: {is_fav_after}")
    
    print("\n" + "=" * 60)


async def test_utils():
    """Utils funksiyalarni test qilish"""
    print("\n\n" + "=" * 60)
    print("UTILS TEST")
    print("=" * 60)
    
    from datetime import datetime, timedelta
    from handlers.auksion_v2.utils import (
        format_price,
        format_date,
        format_time_remaining,
        validate_price_input,
        calculate_bid_suggestions,
    )
    
    print("\n1. Narx formatlash:")
    print(f"   1500000 -> {format_price(1500000)}")
    print(f"   1000000000 -> {format_price(1000000000)}")
    
    print("\n2. Sana formatlash:")
    now = datetime.now()
    print(f"   Hozir: {format_date(now)}")
    
    print("\n3. Qolgan vaqt:")
    future = now + timedelta(hours=2, minutes=30, seconds=45)
    print(f"   2:30:45 dan keyin: {format_time_remaining(future)}")
    
    print("\n4. Narx validatsiya:")
    test_inputs = ["1500000", "1,500,000", "1.5m", "abc", ""]
    for inp in test_inputs:
        result = validate_price_input(inp)
        print(f"   '{inp}' -> {result}")
    
    print("\n5. Taklif variantlari:")
    suggestions = calculate_bid_suggestions(1000000, 50000)
    for label, amount in suggestions:
        print(f"   {label}: {format_price(amount)}")
    
    print("\n" + "=" * 60)


async def main():
    """Barcha testlarni ishga tushirish"""
    print("\n\n")
    print("█" * 60)
    print("█  AUKSION MODULI - TO'LIQ TEST DASTURI")
    print("█" * 60)
    
    try:
        # 1. API test
        await test_api()
        
        # 2. Models test
        await test_models()
        
        # 3. Utils test
        await test_utils()
        
        print("\n\n" + "█" * 60)
        print("█  ✅ BARCHA TESTLAR YAKUNLANDI!")
        print("█" * 60)
        print()
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Test to'xtatildi (Ctrl+C)")
    except Exception as e:
        print(f"\n\n❌ Umumiy xato: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    # Windows uchun event loop policy
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    
    asyncio.run(main())