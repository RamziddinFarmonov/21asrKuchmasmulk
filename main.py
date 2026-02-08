import asyncio
import logging



from os import getenv

from dotenv import load_dotenv
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from handlers.auksion_v2.handlers import router as auksion_v2_router

# Handlerlarni import qilish
from handlers.common import router as common_router
from handlers.kochmas_mulk_sotish import router as kochmas_sotish_router
from handlers.kochmas_mulk_sotib_olish import router as kochmas_sotib_olish_router
from handlers.ijaraga_berish import router as ijaraga_berish_router
from handlers.ijaralar_olish import router as ijaralar_olish_router
from handlers.admin import router as admin_router

load_dotenv()
TOKEN = getenv("BOT_TOKEN")
ADMIN_CHAT_ID = int(getenv("ADMIN_CHAT_ID", 0))  # xavfsizlik uchun default

logging.basicConfig(level=logging.INFO)

bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher(storage=MemoryStorage())

# Routerlarni qo‘shish
dp.include_router(common_router)
dp.include_router(kochmas_sotish_router)
dp.include_router(kochmas_sotib_olish_router)
dp.include_router(ijaraga_berish_router)
dp.include_router(ijaralar_olish_router)
dp.include_router(admin_router)
dp.include_router(auksion_v2_router)

async def main():
    print("Bot ishga tushmoqda...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())