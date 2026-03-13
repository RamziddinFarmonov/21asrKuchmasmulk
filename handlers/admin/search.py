"""
handlers/admin/search.py
========================
2 xil qidiruv usuli:
  1. ID orqali qidirish  — /admin_search yoki "🔍 ID orqali qidirish"
  2. Filter orqali topish — viloyat → tuman → tur → natijalar
"""
from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

from .utils import (
    is_admin,
    get_admin_main_menu, get_admin_kochmas_menu, get_admin_ijara_menu, get_cancel_admin,
    kochmas_detail_kb, ijara_detail_kb,
    format_kochmas_text, format_ijara_text,
    AdminSearchState, AdminBrowseKochmas, AdminBrowseIjara,
)
from utils.constants import (
    REGIONS, DISTRICTS, PROPERTY_TYPES, RENTAL_TYPES,
    get_property_type_name_by_code, get_region_name_by_code,
    format_price, format_area,
)
from utils.keyboards import get_regions_keyboard, get_districts_keyboard, get_property_types_keyboard, get_rental_types_keyboard

router = Router()


# ============================================================================
# 1-USUL: ID ORQALI QIDIRISH
# ============================================================================

@router.message(F.text == "🔍 ID orqali qidirish")
async def admin_search_start(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    await state.set_state(AdminSearchState.entering_id)
    await message.answer(
        "🔍 <b>ID ORQALI QIDIRISH</b>\n\n"
        "E'lon ID raqamini kiriting:\n"
        "<i>Masalan: 5 yoki 12</i>\n\n"
        "Tizim avval Ko'chmas mulkdan, keyin Ijaradan qidiradi.",
        reply_markup=get_cancel_admin(), parse_mode="HTML"
    )


@router.message(AdminSearchState.entering_id)
async def admin_search_by_id(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    if message.text == "❌ Bekor qilish":
        await state.clear()
        return await message.answer("Bekor qilindi.", reply_markup=get_admin_main_menu())

    try:
        obj_id = int(message.text.strip())
    except ValueError:
        return await message.answer("❌ Faqat raqam kiriting!\n<i>Masalan: 5</i>", parse_mode="HTML")

    await state.clear()
    from database.db_manager import db

    # Ko'chmas mulkdan qidirish
    obj = db.get_kochmas_mulk_by_id(obj_id)
    if obj:
        text = format_kochmas_text(obj)
        kb   = kochmas_detail_kb(obj_id, from_search=True)
        if obj.get('photo_id'):
            await message.answer_photo(photo=obj['photo_id'], caption=text, reply_markup=kb, parse_mode="HTML")
        else:
            await message.answer(text, reply_markup=kb, parse_mode="HTML")
        return

    # Ijaradan qidirish
    obj = db.get_ijara_by_id(obj_id)
    if obj:
        text = format_ijara_text(obj)
        kb   = ijara_detail_kb(obj_id, from_search=True)
        if obj.get('photo_id'):
            await message.answer_photo(photo=obj['photo_id'], caption=text, reply_markup=kb, parse_mode="HTML")
        else:
            await message.answer(text, reply_markup=kb, parse_mode="HTML")
        return

    await message.answer(
        f"❌ <b>#{obj_id} raqamli e'lon topilmadi.</b>\n\n"
        "Ko'chmas mulk va Ijara jadvallaridan qidirilddi.",
        reply_markup=get_admin_main_menu(), parse_mode="HTML"
    )


@router.callback_query(F.data == "adm_search_back")
async def adm_search_back(callback: CallbackQuery, state: FSMContext):
    try:
        await callback.message.delete()
    except Exception:
        pass
    await state.set_state(AdminSearchState.entering_id)
    await callback.message.answer(
        "🔍 Yana ID kiriting yoki bekor qiling:",
        reply_markup=get_cancel_admin()
    )
    await callback.answer()


# ============================================================================
# 2-USUL: FILTER ORQALI TOPISH — KO'CHMAS MULK
# ============================================================================

@router.message(F.text == "🔍 Filter orqali topish (Ko'chmas)")
async def admin_browse_kochmas_start(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    await state.set_state(AdminBrowseKochmas.choosing_region)
    await message.answer(
        "🗺️ <b>Viloyatni tanlang:</b>",
        reply_markup=get_regions_keyboard(), parse_mode="HTML"
    )


@router.message(AdminBrowseKochmas.choosing_region)
async def abk_region(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    if message.text == "❌ Bekor qilish":
        await state.clear()
        return await message.answer("Bekor.", reply_markup=get_admin_kochmas_menu())
    if message.text not in REGIONS:
        return await message.answer("❌ Tugmadan tanlang!", reply_markup=get_regions_keyboard())
    await state.update_data(region=REGIONS[message.text], region_name=message.text)
    await state.set_state(AdminBrowseKochmas.choosing_district)
    await message.answer(
        "🏘️ <b>Tumanni tanlang:</b>",
        reply_markup=get_districts_keyboard(REGIONS[message.text]), parse_mode="HTML"
    )


@router.message(AdminBrowseKochmas.choosing_district)
async def abk_district(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    if message.text == "❌ Bekor qilish":
        await state.clear()
        return await message.answer("Bekor.", reply_markup=get_admin_kochmas_menu())
    if message.text == "🔙 Orqaga":
        await state.set_state(AdminBrowseKochmas.choosing_region)
        return await message.answer("🗺️ Viloyatni tanlang:", reply_markup=get_regions_keyboard())
    data = await state.get_data()
    region_code = data.get('region', '')
    districts   = DISTRICTS.get(region_code, [])
    if message.text == "⏭ O'tkazib yuborish":
        await state.update_data(district=None)
    elif message.text in districts:
        await state.update_data(district=message.text)
    else:
        return await message.answer("❌ Tugmadan tanlang!", reply_markup=get_districts_keyboard(region_code))
    await state.set_state(AdminBrowseKochmas.choosing_property_type)
    await message.answer("🏠 <b>Mulk turini tanlang:</b>", reply_markup=get_property_types_keyboard(), parse_mode="HTML")


@router.message(AdminBrowseKochmas.choosing_property_type)
async def abk_prop_type(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    if message.text == "❌ Bekor qilish":
        await state.clear()
        return await message.answer("Bekor.", reply_markup=get_admin_kochmas_menu())
    if message.text == "🔙 Orqaga":
        data = await state.get_data()
        await state.set_state(AdminBrowseKochmas.choosing_district)
        return await message.answer("🏘️ Tumanni tanlang:", reply_markup=get_districts_keyboard(data.get('region', '')))
    if message.text not in PROPERTY_TYPES:
        return await message.answer("❌ Tugmadan tanlang!", reply_markup=get_property_types_keyboard())

    data = await state.get_data()
    await state.clear()

    from database.db_manager import db
    # Admin uchun BARCHA e'lonlar (o'chirilganlar ham)
    all_objs = db.get_all_kochmas(limit=500)
    objects  = [
        o for o in all_objs
        if o.get('region') == data['region']
        and o.get('property_type') == PROPERTY_TYPES[message.text]
        and (data.get('district') is None or o.get('district') == data['district'])
    ]

    if not objects:
        await message.answer(
            "😔 Bu filtrlarda e'lon topilmadi.",
            reply_markup=get_admin_kochmas_menu()
        )
        return

    keyboard = []
    for obj in objects[:50]:
        rooms  = f"{obj['rooms']}-xona " if obj.get('rooms') else ""
        price  = format_price(obj.get('price', 0))
        status = "✅" if obj.get('is_active', 1) else "❌"
        label  = f"{status} #{obj['id']} | {rooms}{message.text} | {price}"
        keyboard.append([InlineKeyboardButton(text=label[:64], callback_data=f"akv_kochmas_{obj['id']}")])
    keyboard.append([InlineKeyboardButton(text="🔙 Admin menyu", callback_data="adm_to_kochmas_menu")])

    await message.answer(
        f"🏠 <b>Natijalar:</b> {len(objects)} ta e'lon\n"
        f"(✅ faol, ❌ o'chirilgan)",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard), parse_mode="HTML"
    )


@router.callback_query(F.data == "adm_to_kochmas_menu")
async def adm_to_kochmas_menu(callback: CallbackQuery):
    try:
        await callback.message.delete()
    except Exception:
        pass
    await callback.message.answer("🏠 Ko'chmas mulk boshqaruvi:", reply_markup=get_admin_kochmas_menu())
    await callback.answer()


# ============================================================================
# 2-USUL: FILTER ORQALI TOPISH — IJARA
# ============================================================================

@router.message(F.text == "🔍 Filter orqali topish (Ijara)")
async def admin_browse_ijara_start(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    await state.set_state(AdminBrowseIjara.choosing_region)
    await message.answer(
        "🗺️ <b>Viloyatni tanlang:</b>",
        reply_markup=get_regions_keyboard(), parse_mode="HTML"
    )


@router.message(AdminBrowseIjara.choosing_region)
async def abi_region(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    if message.text == "❌ Bekor qilish":
        await state.clear()
        return await message.answer("Bekor.", reply_markup=get_admin_ijara_menu())
    if message.text not in REGIONS:
        return await message.answer("❌ Tugmadan tanlang!", reply_markup=get_regions_keyboard())
    await state.update_data(region=REGIONS[message.text], region_name=message.text)
    await state.set_state(AdminBrowseIjara.choosing_district)
    await message.answer(
        "🏘️ <b>Tumanni tanlang:</b>",
        reply_markup=get_districts_keyboard(REGIONS[message.text]), parse_mode="HTML"
    )


@router.message(AdminBrowseIjara.choosing_district)
async def abi_district(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    if message.text == "❌ Bekor qilish":
        await state.clear()
        return await message.answer("Bekor.", reply_markup=get_admin_ijara_menu())
    if message.text == "🔙 Orqaga":
        await state.set_state(AdminBrowseIjara.choosing_region)
        return await message.answer("🗺️ Viloyatni tanlang:", reply_markup=get_regions_keyboard())
    data = await state.get_data()
    region_code = data.get('region', '')
    districts   = DISTRICTS.get(region_code, [])
    if message.text == "⏭ O'tkazib yuborish":
        await state.update_data(district=None)
    elif message.text in districts:
        await state.update_data(district=message.text)
    else:
        return await message.answer("❌ Tugmadan tanlang!", reply_markup=get_districts_keyboard(region_code))
    await state.set_state(AdminBrowseIjara.choosing_property_type)
    await message.answer("🏠 <b>Ijara turini tanlang:</b>", reply_markup=get_rental_types_keyboard(), parse_mode="HTML")


@router.message(AdminBrowseIjara.choosing_property_type)
async def abi_prop_type(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    if message.text == "❌ Bekor qilish":
        await state.clear()
        return await message.answer("Bekor.", reply_markup=get_admin_ijara_menu())
    if message.text == "🔙 Orqaga":
        data = await state.get_data()
        await state.set_state(AdminBrowseIjara.choosing_district)
        return await message.answer("🏘️ Tumanni tanlang:", reply_markup=get_districts_keyboard(data.get('region', '')))
    if message.text not in RENTAL_TYPES:
        return await message.answer("❌ Tugmadan tanlang!", reply_markup=get_rental_types_keyboard())

    data = await state.get_data()
    await state.clear()

    from database.db_manager import db
    all_objs = db.get_all_ijara(limit=500)
    objects  = [
        o for o in all_objs
        if o.get('region') == data['region']
        and o.get('property_type') == RENTAL_TYPES[message.text]
        and (data.get('district') is None or o.get('district') == data['district'])
    ]

    if not objects:
        await message.answer("😔 Bu filtrlarda e'lon topilmadi.", reply_markup=get_admin_ijara_menu())
        return

    keyboard = []
    for obj in objects[:50]:
        rooms  = f"{obj['rooms']}-xona " if obj.get('rooms') else ""
        price  = format_price(obj.get('monthly_price', 0))
        status = "✅" if obj.get('is_active', 1) else "❌"
        label  = f"{status} #{obj['id']} | {rooms}{message.text} | {price}/oy"
        keyboard.append([InlineKeyboardButton(text=label[:64], callback_data=f"akv_ijara_{obj['id']}")])
    keyboard.append([InlineKeyboardButton(text="🔙 Admin menyu", callback_data="adm_to_ijara_menu")])

    await message.answer(
        f"📋 <b>Natijalar:</b> {len(objects)} ta e'lon\n"
        f"(✅ faol, ❌ o'chirilgan)",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard), parse_mode="HTML"
    )


@router.callback_query(F.data == "adm_to_ijara_menu")
async def adm_to_ijara_menu(callback: CallbackQuery):
    try:
        await callback.message.delete()
    except Exception:
        pass
    await callback.message.answer("📋 Ijara boshqaruvi:", reply_markup=get_admin_ijara_menu())
    await callback.answer()