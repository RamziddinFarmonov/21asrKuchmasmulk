"""
handlers/admin/__init__.py
==========================
Admin panel moduli.

Fayl tuzilmasi:
  utils.py       — umumiy yordamchilar: is_admin, klaviaturalar, FSM States, formatters
  main.py        — asosiy menyu, statistika, ro'yxat, ko'rish, o'chirish, tahrirlash
  search.py      — ID orqali qidirish + filter orqali topish
  add_kochmas.py — Ko'chmas mulk e'loni qo'shish (FSM)
  add_ijara.py   — Ijara e'loni qo'shish (FSM)

main.py da routerlarni ro'yxatdan o'tkazish tartibi MUHIM:
  admin_router ni BIRINCHI qo'shing (boshqa routerlardan oldin).

Misol (main.py):
    from handlers.admin import admin_router
    dp.include_router(admin_router)
"""
from aiogram import Router

from .main       import router as _main_router
from .search     import router as _search_router
from .add_kochmas import router as _add_kochmas_router
from .add_ijara  import router as _add_ijara_router

# Barcha admin routerlarni bitta router ostida jamlash
admin_router = Router()
admin_router.include_router(_main_router)
admin_router.include_router(_search_router)
admin_router.include_router(_add_kochmas_router)
admin_router.include_router(_add_ijara_router)

__all__ = ["admin_router"]