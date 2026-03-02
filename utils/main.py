"""
21ASR - Ko'chmas Mulk va Ijara Bot
Main Entry Point
"""
import asyncio
import logging
from os import getenv
from dotenv import load_dotenv

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

# Database'ni initialize qilish
from database.db_manager import db

# Handler'larni import qilish
from common import router as common_router
from handlers.kochmas_mulk.main import router as kochmas_main_router
from handlers.kochmas_mulk.sell import router as kochmas_sell_router
from handlers.kochmas_mulk.buy import router as kochmas_buy_router
from handlers.ijara.main import router as ijara_main_router
from handlers.ijara.rent_out import router as ijara_rent_out_router
from handlers.ijara.rent_in import router as ijara_rent_in_router
from handlers.auksion_v2.handlers import router as auksion_v2_router
from handlers.auksion_v2.region_filter import router as auksion_region_router
from handlers.auksion_v2.search import router as auksion_search_router

# .env fayldan o'qish
load_dotenv()
TOKEN = getenv("BOT_TOKEN")
ADMIN_CHAT_ID = int(getenv("ADMIN_CHAT_ID", 0))

# Logging sozlash
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Bot va Dispatcher
bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher(storage=MemoryStorage())

# Router'larni qo'shish (tartib muhim!)
dp.include_router(common_router)
dp.include_router(kochmas_main_router)
dp.include_router(kochmas_sell_router)
dp.include_router(kochmas_buy_router)
dp.include_router(ijara_main_router)
dp.include_router(ijara_rent_out_router)
dp.include_router(ijara_rent_in_router)
dp.include_router(auksion_v2_router)
dp.include_router(auksion_region_router)
dp.include_router(auksion_search_router)


async def main():
    """Bot ishga tushirish"""
    logger.info("=" * 50)
    logger.info("🚀 21ASR Bot ishga tushmoqda...")
    logger.info("=" * 50)
    
    # Database'ni tekshirish
    try:
        stats = db.get_statistics()
        logger.info(f"📊 Database statistika:")
        logger.info(f"   Ko'chmas mulk: {stats['kochmas_mulk']} ta")
        logger.info(f"   Ijara: {stats['ijara']} ta")
        logger.info(f"   Jami: {stats['total']} ta e'lon")
    except Exception as e:
        logger.error(f"❌ Database xatolik: {e}")
    
    logger.info("=" * 50)
    logger.info("✅ Bot muvaffaqiyatli ishga tushdi!")
    logger.info("=" * 50)
    
    # Polling
    await dp.start_polling(bot)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("\n👋 Bot to'xtatildi!")
    except Exception as e:
        logger.error(f"❌ Kritik xatolik: {e}")
