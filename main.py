"""
21ASR - Ko'chmas Mulk va Ijara Bot
Main Entry Point

PROYEKT STRUKTURASI:
21asr/
├── main.py                          <- BU FAYL
├── .env
├── database/db_manager.py
├── utils/constants.py, keyboards.py, states.py
└── handlers/
    ├── common.py     (yoki root papkada common.py)
    ├── admin/
    │   ├── __init__.py
    │   └── admin_panel.py
    ├── kochmas_mulk/
    │   ├── __init__.py
    │   ├── main.py
    │   ├── my_objects.py
    │   ├── sell.py
    │   └── buy.py
    └── ijara/
        ├── __init__.py
        ├── main.py
        ├── my_objects.py
        ├── rent_out.py
        └── rent_in.py
"""
import asyncio
import logging
from os import getenv
from dotenv import load_dotenv

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from database.db_manager import db

load_dotenv()
TOKEN         = getenv("BOT_TOKEN")
ADMIN_CHAT_ID = int(getenv("ADMIN_CHAT_ID", 0))

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp  = Dispatcher(storage=MemoryStorage())


def _include_routers():
    # ── Admin ──────────────────────────────────────────────────────────────
    from handlers.admin import admin_router
    dp.include_router(admin_router)

    # ── Common (handlers/common.py yoki root common.py) ───────────────────
    try:
        from handlers.common import router as common_router
        logger.info("common: handlers/common.py")
    except ModuleNotFoundError:
        from common import router as common_router
        logger.info("common: root/common.py")
    dp.include_router(common_router)

    # ── Ko'chmas mulk ─────────────────────────────────────────────────────
    from handlers.kochmas_mulk.main       import router as km_main
    from handlers.kochmas_mulk.my_objects import router as km_myobj
    from handlers.kochmas_mulk.sell       import router as km_sell
    from handlers.kochmas_mulk.buy        import router as km_buy
    dp.include_router(km_main)
    dp.include_router(km_myobj)
    dp.include_router(km_sell)
    dp.include_router(km_buy)

    # ── Ijara ─────────────────────────────────────────────────────────────
    from handlers.ijara.main       import router as ij_main
    from handlers.ijara.my_objects import router as ij_myobj
    from handlers.ijara.rent_out   import router as ij_rent_out
    from handlers.ijara.rent_in    import router as ij_rent_in
    from handlers.auksion_v2.handlers import router as auksion_v2
    from handlers.auksion_v2.region_filter import router as auksion_region
    from handlers.auksion_v2.search import router as auksion_search
    dp.include_router(ij_main)
    dp.include_router(ij_myobj)
    dp.include_router(ij_rent_out)
    dp.include_router(ij_rent_in)
    dp.include_router(auksion_v2)
    dp.include_router(auksion_region)
    dp.include_router(auksion_search)


async def main():
    logger.info("=" * 50)
    logger.info("🚀 21ASR Bot ishga tushmoqda...")

    _include_routers()

    try:
        stats = db.get_statistics()
        logger.info(
            f"📊 Ko'chmas mulk={stats.get('kochmas_mulk',0)}, "
            f"Ijara={stats.get('ijara',0)}"
        )
    except Exception as e:
        logger.error(f"❌ Database xatolik: {e}")

    logger.info("✅ Bot muvaffaqiyatli ishga tushdi!")
    logger.info("=" * 50)
    await dp.start_polling(bot)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("\n👋 Bot to'xtatildi!")
    except Exception as e:
        logger.error(f"❌ Kritik xatolik: {e}")