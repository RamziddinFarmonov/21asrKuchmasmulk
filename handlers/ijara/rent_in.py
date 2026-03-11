"""
Ijara - Ijaraga Olish - TO'LIQ TUZATILGAN

TUZATILGAN:
- split("_")[2] -> split("_")[-1] (IndexError xavfi)
- fav_ijara va apply_ijara callbacklarda xuddi shu muammo tuzatildi
- ADMIN_PHONE globals() da qidirilardi - to'g'ridan-to'g'ri konstant qilindi
- send_object() funksiyasi import yo'q holda mavjud edi - o'chirildi
"""
import logging

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.fsm.context import FSMContext

from utils.states import IjaraRentInStates
from utils.keyboards import (
    get_regions_keyboard, get_districts_keyboard, get_rental_types_keyboard,
    get_ijara_menu
)
from utils.constants import (
    REGIONS, DISTRICTS, RENTAL_TYPES,
    format_price, format_area,
    get_region_name_by_code, get_property_type_name_by_code
)
from database.db_manager import db

router = Router()
logger = logging.getLogger(__name__)

ADMIN_PHONE   = "+998 91 007 00 21"
ADMIN_CHAT_ID = -1003037718098


@router.message(F.text == "📥 Ijaraga olish")
async def start_rent_in(message: Message, state: FSMContext):
    await state.set_state(IjaraRentInStates.choosing_region)
    await message.answer(
        "🗺️ <b>Qaysi viloyat?</b>",
        reply_markup=get_regions_keyboard(), parse_mode="HTML"
    )


@router.message(IjaraRentInStates.choosing_region)
async def process_region(message: Message, state: FSMContext):
    if message.text == "🔙 Orqaga":
        await state.clear()
        await message.answer("Ijara bo'limi:", reply_markup=get_ijara_menu())
        return
    if message.text not in REGIONS:
        await message.answer("❌ Tugmalardan tanlang!", reply_markup=get_regions_keyboard())
        return
    region_code = REGIONS[message.text]
    await state.update_data(region=region_code, region_name=message.text)
    await state.set_state(IjaraRentInStates.choosing_district)
    await message.answer(
        "🏘️ <b>Qaysi tumandan qidiryapsiz?</b>\n\nTumanni tanlang yoki o'tkazib yuboring:",
        reply_markup=get_districts_keyboard(region_code), parse_mode="HTML"
    )


@router.message(IjaraRentInStates.choosing_district)
async def process_district_rent_in(message: Message, state: FSMContext):
    if message.text == "🔙 Orqaga":
        await state.set_state(IjaraRentInStates.choosing_region)
        await message.answer("Viloyatni tanlang:", reply_markup=get_regions_keyboard())
        return
    data = await state.get_data()
    region_code = data.get('region', '')
    districts = DISTRICTS.get(region_code, [])

    if message.text == "⏭ O'tkazib yuborish":
        await state.update_data(district=None, district_name=None)
    elif message.text in districts:
        await state.update_data(district=message.text, district_name=message.text)
    else:
        await message.answer(
            "❌ Iltimos, tugmalardan birini tanlang!",
            reply_markup=get_districts_keyboard(region_code)
        )
        return

    await state.set_state(IjaraRentInStates.choosing_property_type)
    await message.answer(
        "🏠 <b>Ijara turi:</b>",
        reply_markup=get_rental_types_keyboard(), parse_mode="HTML"
    )


@router.message(IjaraRentInStates.choosing_property_type)
async def process_property_type(message: Message, state: FSMContext):
    if message.text == "🔙 Orqaga":
        data = await state.get_data()
        await state.set_state(IjaraRentInStates.choosing_district)
        await message.answer(
            "🏘️ Tumanni tanlang:",
            reply_markup=get_districts_keyboard(data.get('region', ''))
        )
        return
    if message.text not in RENTAL_TYPES:
        await message.answer("❌ Tugmalardan tanlang!", reply_markup=get_rental_types_keyboard())
        return

    await state.update_data(
        property_type=RENTAL_TYPES[message.text],
        property_type_name=message.text
    )
    data = await state.get_data()

    objects = db.get_ijara_list(
        region=data['region'],
        district=data.get('district'),
        property_type=data['property_type'],
        action_type='rent_out'
    )
    await state.clear()

    if not objects:
        await message.answer(
            f"😔 <b>{data['region_name']} — {data['property_type_name']}</b>\n\n"
            "Hozircha e'lonlar yo'q.\nTez orada yangi e'lonlar qo'shiladi!",
            reply_markup=get_ijara_menu(), parse_mode="HTML"
        )
        return

    keyboard = []
    for obj in objects[:50]:
        rooms = f"{obj['rooms']}-xona " if obj.get('rooms') else ""
        prop  = get_property_type_name_by_code(obj.get('property_type', ''))
        price = format_price(obj.get('monthly_price', 0))
        area  = format_area(obj.get('area', 0)) if obj.get('area') else ""
        label = f"📋 {rooms}{prop} | {price}/oy"
        if area:
            label += f" | {area}"
        keyboard.append([InlineKeyboardButton(
            text=label, callback_data=f"ijara_view_{obj['id']}"
        )])
    keyboard.append([InlineKeyboardButton(text="🔙 Orqaga", callback_data="ijara_back")])

    await message.answer(
        f"📋 <b>{data['region_name']}"
        + (f" | {data['district_name']}" if data.get('district_name') else "")
        + f" — {data['property_type_name']}</b>\n\n"
        f"Topildi: <b>{len(objects)}</b> ta e'lon\n\n"
        "Batafsil ko'rish uchun tanlang:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard),
        parse_mode="HTML"
    )


# ============================================================================
# E'LON BATAFSIL
# ============================================================================

@router.callback_query(F.data.startswith("ijara_view_"))
async def callback_view_ijara(callback: CallbackQuery):
    try:
        obj_id = int(callback.data.split("_")[-1])
    except (ValueError, IndexError):
        await callback.answer("❌ Xato", show_alert=True)
        return

    obj = db.get_ijara_by_id(obj_id)
    if not obj:
        await callback.answer("❌ E'lon topilmadi!", show_alert=True)
        return

    text  = f"📋 <b>{get_property_type_name_by_code(obj.get('property_type', ''))}</b>\n\n"
    text += f"🗺️ <b>Viloyat:</b> {get_region_name_by_code(obj.get('region', ''))}\n"
    text += f"🏘️ <b>Tuman:</b> {obj.get('district') or '—'}\n"
    text += f"📐 <b>Maydon:</b> {format_area(obj.get('area', 0))}\n"
    if obj.get('rooms'):
        text += f"🚪 <b>Xonalar:</b> {obj['rooms']} ta\n"
    if obj.get('floor'):
        text += f"🏢 <b>Qavat:</b> {obj['floor']}/{obj.get('total_floors', '?')}\n"
    text += f"💰 <b>Oylik:</b> {format_price(obj.get('monthly_price', 0))}/oy\n"
    if obj.get('min_rental_period'):
        text += f"📅 <b>Min. muddat:</b> {obj['min_rental_period']}\n"
    text += f"📍 <b>Manzil:</b> {obj.get('address', '—')}\n"
    if obj.get('description'):
        text += f"\n📝 <b>Tavsif:</b>\n{obj['description'][:300]}\n"
    text += f"\n📞 <b>Bog'lanish:</b> {ADMIN_PHONE}"
    text += f"\n\n🆔 E'lon #{obj['id']}"

    is_fav = db.is_favorite(callback.from_user.id, obj_id, 'ijara')
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📤 Ariza yuborish", callback_data=f"apply_ijara_{obj_id}")],
        [InlineKeyboardButton(
            text="❤️ Sevimlilardan o'chirish" if is_fav else "🤍 Sevimlilarga qo'shish",
            callback_data=f"fav_ijara_{obj_id}"
        )],
        [InlineKeyboardButton(text="🔙 Orqaga", callback_data="ijara_back")]
    ])

    try:
        if obj.get('photo_id'):
            await callback.message.delete()
            await callback.bot.send_photo(
                chat_id=callback.message.chat.id,
                photo=obj['photo_id'], caption=text, reply_markup=kb, parse_mode="HTML"
            )
            if obj.get('video_id'):
                await callback.bot.send_video(
                    chat_id=callback.message.chat.id,
                    video=obj['video_id'], caption=f"🎥 Video — E'lon #{obj_id}"
                )
        elif obj.get('video_id'):
            await callback.message.delete()
            await callback.bot.send_video(
                chat_id=callback.message.chat.id,
                video=obj['video_id'], caption=text, reply_markup=kb, parse_mode="HTML"
            )
        else:
            await callback.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
    except Exception:
        await callback.message.answer(text, reply_markup=kb, parse_mode="HTML")

    await callback.answer()


@router.callback_query(F.data == "ijara_back")
async def callback_ijara_back(callback: CallbackQuery):
    try:
        await callback.message.delete()
    except Exception:
        pass
    await callback.message.answer("Ijara bo'limi:", reply_markup=get_ijara_menu())
    await callback.answer()


# ============================================================================
# SEVIMLILAR
# ============================================================================

@router.message(F.text == "❤️ Sevimlilar")
async def show_ijara_favorites(message: Message):
    objects = db.get_user_favorites(message.from_user.id, 'ijara')
    if not objects:
        await message.answer(
            "💔 <b>Sevimlilar bo'sh</b>\n\nHali sevimli e'lonlar yo'q.",
            reply_markup=get_ijara_menu(), parse_mode="HTML"
        )
        return
    keyboard = []
    for obj in objects:
        rooms = f"{obj['rooms']}-xona " if obj.get('rooms') else ""
        prop  = get_property_type_name_by_code(obj.get('property_type', ''))
        price = format_price(obj.get('monthly_price', 0))
        keyboard.append([InlineKeyboardButton(
            text=f"📋 {rooms}{prop} | {price}/oy",
            callback_data=f"ijara_view_{obj['id']}"
        )])
    keyboard.append([InlineKeyboardButton(text="🔙 Orqaga", callback_data="ijara_back")])
    await message.answer(
        f"❤️ <b>SEVIMLI IJARA E'LONLAR</b>\n\nJami: {len(objects)} ta\n",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard), parse_mode="HTML"
    )


@router.callback_query(F.data.startswith("fav_ijara_"))
async def callback_toggle_fav_ijara(callback: CallbackQuery):
    try:
        obj_id = int(callback.data.split("_")[-1])
    except (ValueError, IndexError):
        await callback.answer("❌ Xato", show_alert=True)
        return
    user_id = callback.from_user.id
    is_fav  = db.is_favorite(user_id, obj_id, 'ijara')
    if is_fav:
        db.remove_favorite(user_id, obj_id, 'ijara')
        await callback.answer("💔 Sevimlilardan o'chirildi")
    else:
        db.add_favorite(user_id, obj_id, 'ijara')
        await callback.answer("❤️ Sevimlilarga qo'shildi")
    await callback_view_ijara(callback)