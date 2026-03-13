"""
handlers/admin/add_kochmas.py
=============================
Admin tomonidan Ko'chmas mulk e'loni qo'shish (to'liq FSM).
"""
from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from .utils import (
    is_admin,
    get_admin_kochmas_menu, get_cancel_admin, get_skip_cancel_admin, get_confirm_admin,
    AdminAddKochmas,
)
from utils.constants import (
    REGIONS, DISTRICTS, PROPERTY_TYPES,
    format_price, format_area,
)
from utils.keyboards import (
    get_regions_keyboard, get_districts_keyboard, get_property_types_keyboard,
)

router = Router()


@router.message(F.text == "➕ Ko'chmas mulk qo'shish")
async def admin_add_kochmas_start(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    await state.set_state(AdminAddKochmas.choosing_region)
    await message.answer("🗺️ <b>Viloyatni tanlang:</b>", reply_markup=get_regions_keyboard(), parse_mode="HTML")


@router.message(AdminAddKochmas.choosing_region)
async def _ak_region(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    if message.text == "❌ Bekor qilish":
        await state.clear()
        return await message.answer("Bekor.", reply_markup=get_admin_kochmas_menu())
    if message.text not in REGIONS:
        return await message.answer("❌ Tugmadan tanlang!", reply_markup=get_regions_keyboard())
    await state.update_data(region=REGIONS[message.text], region_name=message.text)
    await state.set_state(AdminAddKochmas.choosing_district)
    await message.answer(
        "🏘️ <b>Tumanni tanlang (ixtiyoriy):</b>",
        reply_markup=get_districts_keyboard(REGIONS[message.text]), parse_mode="HTML"
    )


@router.message(AdminAddKochmas.choosing_district)
async def _ak_district(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    if message.text == "❌ Bekor qilish":
        await state.clear()
        return await message.answer("Bekor.", reply_markup=get_admin_kochmas_menu())
    if message.text == "🔙 Orqaga":
        await state.set_state(AdminAddKochmas.choosing_region)
        return await message.answer("🗺️ Viloyatni tanlang:", reply_markup=get_regions_keyboard())
    data = await state.get_data()
    region_code = data.get('region', '')
    districts   = DISTRICTS.get(region_code, [])
    if message.text == "⏭ O'tkazib yuborish":
        await state.update_data(district=None, district_name=None)
    elif message.text in districts:
        await state.update_data(district=message.text, district_name=message.text)
    else:
        return await message.answer("❌ Tugmadan tanlang!", reply_markup=get_districts_keyboard(region_code))
    await state.set_state(AdminAddKochmas.choosing_property_type)
    await message.answer("🏠 <b>Mulk turi:</b>", reply_markup=get_property_types_keyboard(), parse_mode="HTML")


@router.message(AdminAddKochmas.choosing_property_type)
async def _ak_prop(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    if message.text == "❌ Bekor qilish":
        await state.clear()
        return await message.answer("Bekor.", reply_markup=get_admin_kochmas_menu())
    if message.text not in PROPERTY_TYPES:
        return await message.answer("❌ Tugmadan tanlang!", reply_markup=get_property_types_keyboard())
    await state.update_data(property_type=PROPERTY_TYPES[message.text], property_type_name=message.text)
    await state.set_state(AdminAddKochmas.entering_full_name)
    await message.answer("👤 <b>Sotuvchi ismi:</b>", reply_markup=get_cancel_admin(), parse_mode="HTML")


@router.message(AdminAddKochmas.entering_full_name)
async def _ak_name(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    if message.text == "❌ Bekor qilish":
        await state.clear()
        return await message.answer("Bekor.", reply_markup=get_admin_kochmas_menu())
    await state.update_data(full_name=message.text.strip())
    await state.set_state(AdminAddKochmas.entering_phone)
    await message.answer("📱 <b>Telefon raqami:</b>", reply_markup=get_cancel_admin(), parse_mode="HTML")


@router.message(AdminAddKochmas.entering_phone)
async def _ak_phone(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    if message.text == "❌ Bekor qilish":
        await state.clear()
        return await message.answer("Bekor.", reply_markup=get_admin_kochmas_menu())
    phone = message.text.replace(" ", "").replace("-", "").strip()
    if not phone.startswith("+998"):
        phone = "+998" + phone.lstrip("998").lstrip("+998")
    await state.update_data(phone=phone)
    await state.set_state(AdminAddKochmas.entering_area)
    await message.answer("📐 <b>Maydon (m²):</b>", reply_markup=get_cancel_admin(), parse_mode="HTML")


@router.message(AdminAddKochmas.entering_area)
async def _ak_area(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    if message.text == "❌ Bekor qilish":
        await state.clear()
        return await message.answer("Bekor.", reply_markup=get_admin_kochmas_menu())
    try:
        area = float(message.text.replace(",", ".").strip())
        if area <= 0:
            raise ValueError
    except ValueError:
        return await message.answer("❌ To'g'ri raqam kiriting!")
    await state.update_data(area=area)
    data = await state.get_data()
    if data.get('property_type') in ['apartment', 'house']:
        await state.set_state(AdminAddKochmas.entering_rooms)
        await message.answer("🚪 <b>Xonalar soni:</b>", reply_markup=get_cancel_admin(), parse_mode="HTML")
    else:
        await state.set_state(AdminAddKochmas.entering_price)
        await message.answer("💰 <b>Narxi (so'm):</b>", reply_markup=get_cancel_admin(), parse_mode="HTML")


@router.message(AdminAddKochmas.entering_rooms)
async def _ak_rooms(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    if message.text == "❌ Bekor qilish":
        await state.clear()
        return await message.answer("Bekor.", reply_markup=get_admin_kochmas_menu())
    try:
        rooms = int(message.text.strip())
        if rooms <= 0:
            raise ValueError
    except ValueError:
        return await message.answer("❌ To'g'ri raqam kiriting!")
    await state.update_data(rooms=rooms)
    data = await state.get_data()
    if data.get('property_type') == 'apartment':
        await state.set_state(AdminAddKochmas.entering_floor)
        await message.answer("🏢 <b>Qavat:</b>", reply_markup=get_cancel_admin(), parse_mode="HTML")
    else:
        await state.set_state(AdminAddKochmas.entering_price)
        await message.answer("💰 <b>Narxi (so'm):</b>", reply_markup=get_cancel_admin(), parse_mode="HTML")


@router.message(AdminAddKochmas.entering_floor)
async def _ak_floor(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    if message.text == "❌ Bekor qilish":
        await state.clear()
        return await message.answer("Bekor.", reply_markup=get_admin_kochmas_menu())
    try:
        floor = int(message.text.strip())
        if floor <= 0:
            raise ValueError
    except ValueError:
        return await message.answer("❌ To'g'ri raqam!")
    await state.update_data(floor=floor)
    await state.set_state(AdminAddKochmas.entering_total_floors)
    await message.answer("🏢 <b>Jami qavatlar soni:</b>", reply_markup=get_cancel_admin(), parse_mode="HTML")


@router.message(AdminAddKochmas.entering_total_floors)
async def _ak_total_floors(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    if message.text == "❌ Bekor qilish":
        await state.clear()
        return await message.answer("Bekor.", reply_markup=get_admin_kochmas_menu())
    try:
        total = int(message.text.strip())
        if total <= 0:
            raise ValueError
        data = await state.get_data()
        if data.get('floor', 0) > total:
            return await message.answer("❌ Qavat jami qavatdan katta bo'lmaydi!")
    except ValueError:
        return await message.answer("❌ To'g'ri raqam!")
    await state.update_data(total_floors=total)
    await state.set_state(AdminAddKochmas.entering_price)
    await message.answer("💰 <b>Narxi (so'm):</b>", reply_markup=get_cancel_admin(), parse_mode="HTML")


@router.message(AdminAddKochmas.entering_price)
async def _ak_price(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    if message.text == "❌ Bekor qilish":
        await state.clear()
        return await message.answer("Bekor.", reply_markup=get_admin_kochmas_menu())
    try:
        price = float(message.text.replace(" ", "").replace(",", "").strip())
        if price <= 0:
            raise ValueError
    except ValueError:
        return await message.answer("❌ To'g'ri narx kiriting!")
    await state.update_data(price=price)
    await state.set_state(AdminAddKochmas.entering_address)
    await message.answer("📍 <b>Manzil:</b>", reply_markup=get_cancel_admin(), parse_mode="HTML")


@router.message(AdminAddKochmas.entering_address)
async def _ak_address(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    if message.text == "❌ Bekor qilish":
        await state.clear()
        return await message.answer("Bekor.", reply_markup=get_admin_kochmas_menu())
    await state.update_data(address=message.text.strip())
    await state.set_state(AdminAddKochmas.entering_description)
    await message.answer("📝 <b>Tavsif (ixtiyoriy):</b>", reply_markup=get_skip_cancel_admin(), parse_mode="HTML")


@router.message(AdminAddKochmas.entering_description)
async def _ak_desc(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    if message.text == "❌ Bekor qilish":
        await state.clear()
        return await message.answer("Bekor.", reply_markup=get_admin_kochmas_menu())
    if message.text != "⏭️ O'tkazib yuborish":
        await state.update_data(description=message.text.strip())
    await state.set_state(AdminAddKochmas.uploading_photo)
    await message.answer("📸 <b>Rasm (ixtiyoriy):</b>", reply_markup=get_skip_cancel_admin(), parse_mode="HTML")


@router.message(AdminAddKochmas.uploading_photo, F.photo)
async def _ak_photo(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    await state.update_data(photo_id=message.photo[-1].file_id)
    await state.set_state(AdminAddKochmas.uploading_video)
    await message.answer("🎥 <b>Video (ixtiyoriy):</b>", reply_markup=get_skip_cancel_admin(), parse_mode="HTML")


@router.message(AdminAddKochmas.uploading_photo)
async def _ak_photo_skip(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    if message.text == "❌ Bekor qilish":
        await state.clear()
        return await message.answer("Bekor.", reply_markup=get_admin_kochmas_menu())
    if message.text != "⏭️ O'tkazib yuborish":
        return await message.answer("❌ Rasm yuboring yoki o'tkazib yuboring!", reply_markup=get_skip_cancel_admin())
    await state.set_state(AdminAddKochmas.uploading_video)
    await message.answer("🎥 <b>Video (ixtiyoriy):</b>", reply_markup=get_skip_cancel_admin(), parse_mode="HTML")


@router.message(AdminAddKochmas.uploading_video, F.video)
async def _ak_video(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    await state.update_data(video_id=message.video.file_id)
    await _ak_show_confirm(message, state)


@router.message(AdminAddKochmas.uploading_video)
async def _ak_video_skip(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    if message.text == "❌ Bekor qilish":
        await state.clear()
        return await message.answer("Bekor.", reply_markup=get_admin_kochmas_menu())
    if message.text != "⏭️ O'tkazib yuborish":
        return await message.answer("❌ Video yuboring yoki o'tkazib yuboring!", reply_markup=get_skip_cancel_admin())
    await _ak_show_confirm(message, state)


async def _ak_show_confirm(message: Message, state: FSMContext):
    data = await state.get_data()
    text = (
        "📋 <b>YANGI E'LON — Ko'chmas Mulk</b>\n\n"
        f"🗺️ {data.get('region_name')}\n"
        f"🏘️ {data.get('district_name') or '—'}\n"
        f"🏠 {data.get('property_type_name')}\n"
        f"👤 {data.get('full_name')} | {data.get('phone')}\n"
        f"📐 {format_area(data.get('area', 0))}\n"
    )
    if data.get('rooms'):
        text += f"🚪 {data['rooms']} xona\n"
    if data.get('floor'):
        text += f"🏢 {data['floor']}/{data.get('total_floors')} qavat\n"
    text += f"💰 {format_price(data.get('price', 0))}\n"
    text += f"📍 {data.get('address')}\n"
    if data.get('description'):
        text += f"📝 {data['description'][:200]}\n"
    text += f"\n📸 {'✅' if data.get('photo_id') else '❌'} | 🎥 {'✅' if data.get('video_id') else '❌'}"
    text += "\n\n❓ Saqlaysizmi?"
    await state.set_state(AdminAddKochmas.confirmation)
    await message.answer(text, reply_markup=get_confirm_admin(), parse_mode="HTML")


@router.message(AdminAddKochmas.confirmation)
async def _ak_confirm(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    if message.text == "❌ Bekor qilish":
        await state.clear()
        return await message.answer("Bekor.", reply_markup=get_admin_kochmas_menu())
    if message.text != "✅ Saqlash":
        return
    from database.db_manager import db
    import logging
    logger = logging.getLogger(__name__)
    data = await state.get_data()
    try:
        obj_id = db.add_kochmas_mulk({
            'user_id':       message.from_user.id,
            'username':      message.from_user.username,
            'full_name':     data.get('full_name', ''),
            'phone':         data.get('phone', ''),
            'region':        data['region'],
            'district':      data.get('district'),
            'property_type': data['property_type'],
            'action_type':   'sell',
            'area':          data.get('area'),
            'rooms':         data.get('rooms'),
            'floor':         data.get('floor'),
            'total_floors':  data.get('total_floors'),
            'price':         data['price'],
            'description':   data.get('description'),
            'photo_id':      data.get('photo_id'),
            'video_id':      data.get('video_id'),
            'address':       data['address']
        })
        await message.answer(
            f"✅ <b>Ko'chmas mulk e'loni qo'shildi!</b>\n🆔 #{obj_id}",
            reply_markup=get_admin_kochmas_menu(), parse_mode="HTML"
        )
        logger.info(f"Admin {message.from_user.id}: Ko'chmas #{obj_id} qo'shdi")
    except Exception as e:
        await message.answer(f"❌ Xato: {e}", reply_markup=get_admin_kochmas_menu())
    await state.clear()