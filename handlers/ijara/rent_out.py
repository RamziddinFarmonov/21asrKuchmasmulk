"""
Ijara - Ijaraga Berish - TO'LIQ TUZATILGAN

TUZATILGAN:
- Bo'sh telefon kiritilsa IndexError - strip() + empty check
- description tasdiqlashda truncate + '...' qo'shildi
- process_photo_skip: else bloki yo'q edi - qo'shildi
- price kiritishda replace(",", "") qo'shildi
"""
import logging
from datetime import datetime

from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

from utils.states import IjaraRentOutStates
from utils.keyboards import (
    get_regions_keyboard, get_rental_types_keyboard,
    get_cancel_button, get_skip_and_cancel,
    get_confirmation_keyboard, get_ijara_menu, get_rental_period_keyboard
)
from utils.constants import (
    REGIONS, RENTAL_TYPES, RENTAL_PERIODS,
    format_price, format_area, format_phone, validate_phone
)
from database.db_manager import db

router = Router()
logger = logging.getLogger(__name__)

ADMIN_CHAT_ID = -1003037718098
ADMIN_PHONE   = "+998910070021"


@router.message(F.text == "📤 Ijaraga berish")
async def start_rent_out(message: Message, state: FSMContext):
    await state.set_state(IjaraRentOutStates.choosing_region)
    await message.answer(
        "🗺️ <b>Qaysi viloyatda joylashgan?</b>",
        reply_markup=get_regions_keyboard(), parse_mode="HTML"
    )


@router.message(IjaraRentOutStates.choosing_region)
async def process_region(message: Message, state: FSMContext):
    if message.text == "🔙 Orqaga":
        await state.clear()
        await message.answer("Ijara bo'limi:", reply_markup=get_ijara_menu())
        return
    if message.text not in REGIONS:
        await message.answer("❌ Tugmalardan tanlang!", reply_markup=get_regions_keyboard())
        return
    await state.update_data(region=REGIONS[message.text], region_name=message.text)
    await state.set_state(IjaraRentOutStates.choosing_property_type)
    await message.answer(
        "🏠 <b>Ijara turi:</b>",
        reply_markup=get_rental_types_keyboard(), parse_mode="HTML"
    )


@router.message(IjaraRentOutStates.choosing_property_type)
async def process_property_type(message: Message, state: FSMContext):
    if message.text == "🔙 Orqaga":
        await state.set_state(IjaraRentOutStates.choosing_region)
        await message.answer("Viloyatni tanlang:", reply_markup=get_regions_keyboard())
        return
    if message.text not in RENTAL_TYPES:
        await message.answer("❌ Tugmalardan tanlang!", reply_markup=get_rental_types_keyboard())
        return
    await state.update_data(property_type=RENTAL_TYPES[message.text], property_type_name=message.text)
    await state.set_state(IjaraRentOutStates.entering_full_name)
    await message.answer(
        "👤 <b>Ism-familiyangiz:</b>\n\n<i>Masalan: Aliyev Vali</i>",
        reply_markup=get_cancel_button(), parse_mode="HTML"
    )


@router.message(IjaraRentOutStates.entering_full_name)
async def process_full_name(message: Message, state: FSMContext):
    if message.text == "🔙 Orqaga":
        await state.set_state(IjaraRentOutStates.choosing_property_type)
        await message.answer("Ijara turini tanlang:", reply_markup=get_rental_types_keyboard())
        return
    if message.text == "❌ Bekor qilish":
        await state.clear()
        await message.answer("Bekor qilindi.", reply_markup=get_ijara_menu())
        return
    full_name = message.text.strip()
    if len(full_name.split()) < 2:
        await message.answer(
            "❌ To'liq ism-familiya kiriting!\n<i>Masalan: Aliyev Vali</i>", parse_mode="HTML"
        )
        return
    await state.update_data(full_name=full_name)
    await state.set_state(IjaraRentOutStates.entering_phone)
    await message.answer(
        "📱 <b>Telefon raqam:</b>\n\n<i>Format: +998 XX XXX XX XX</i>",
        reply_markup=get_cancel_button(), parse_mode="HTML"
    )


@router.message(IjaraRentOutStates.entering_phone)
async def process_phone(message: Message, state: FSMContext):
    if message.text == "🔙 Orqaga":
        await state.set_state(IjaraRentOutStates.entering_full_name)
        await message.answer("Ism-familiyangizni kiriting:")
        return
    if message.text == "❌ Bekor qilish":
        await state.clear()
        await message.answer("Bekor qilindi.", reply_markup=get_ijara_menu())
        return
    phone = message.text.replace(" ", "").replace("-", "").strip()
    if not phone:
        await message.answer("❌ Telefon raqam kiriting!")
        return
    if not phone.startswith("+998") and not phone.startswith("998"):
        phone = ("+998" + phone) if not phone.startswith("+") else phone
    if not validate_phone(phone):
        await message.answer("❌ Noto'g'ri format!\n<i>+998 XX XXX XX XX</i>", parse_mode="HTML")
        return
    await state.update_data(phone=format_phone(phone))
    await state.set_state(IjaraRentOutStates.entering_area)
    await message.answer(
        "📐 <b>Maydon (m²):</b>\n\n<i>Masalan: 65.5</i>",
        reply_markup=get_cancel_button(), parse_mode="HTML"
    )


@router.message(IjaraRentOutStates.entering_area)
async def process_area(message: Message, state: FSMContext):
    if message.text == "🔙 Orqaga":
        await state.set_state(IjaraRentOutStates.entering_phone)
        await message.answer("Telefon kiriting:")
        return
    if message.text == "❌ Bekor qilish":
        await state.clear()
        await message.answer("Bekor qilindi.", reply_markup=get_ijara_menu())
        return
    try:
        area = float(message.text.replace(",", ".").strip())
        if area <= 0:
            raise ValueError
    except ValueError:
        await message.answer("❌ To'g'ri raqam kiriting!\n<i>Masalan: 65.5</i>", parse_mode="HTML")
        return
    await state.update_data(area=area)
    data = await state.get_data()
    if data.get('property_type') in ['apartment', 'house']:
        await state.set_state(IjaraRentOutStates.entering_rooms)
        await message.answer(
            "🚪 <b>Xonalar soni:</b>\n\n<i>Masalan: 3</i>",
            reply_markup=get_cancel_button(), parse_mode="HTML"
        )
    else:
        await state.set_state(IjaraRentOutStates.entering_monthly_price)
        await message.answer(
            "💰 <b>Oylik ijara narxi (so'm):</b>\n\n<i>Masalan: 3000000</i>",
            reply_markup=get_cancel_button(), parse_mode="HTML"
        )


@router.message(IjaraRentOutStates.entering_rooms)
async def process_rooms(message: Message, state: FSMContext):
    if message.text == "🔙 Orqaga":
        await state.set_state(IjaraRentOutStates.entering_area)
        await message.answer("Maydonni kiriting:")
        return
    if message.text == "❌ Bekor qilish":
        await state.clear()
        await message.answer("Bekor qilindi.", reply_markup=get_ijara_menu())
        return
    try:
        rooms = int(message.text.strip())
        if rooms <= 0:
            raise ValueError
    except ValueError:
        await message.answer("❌ To'g'ri raqam kiriting!\n<i>Masalan: 3</i>", parse_mode="HTML")
        return
    await state.update_data(rooms=rooms)
    data = await state.get_data()
    if data.get('property_type') == 'apartment':
        await state.set_state(IjaraRentOutStates.entering_floor)
        await message.answer(
            "🏢 <b>Qavat:</b>\n\n<i>Masalan: 5</i>",
            reply_markup=get_cancel_button(), parse_mode="HTML"
        )
    else:
        await state.set_state(IjaraRentOutStates.entering_monthly_price)
        await message.answer(
            "💰 <b>Oylik narx (so'm):</b>\n\n<i>Masalan: 3000000</i>",
            reply_markup=get_cancel_button(), parse_mode="HTML"
        )


@router.message(IjaraRentOutStates.entering_floor)
async def process_floor(message: Message, state: FSMContext):
    if message.text == "🔙 Orqaga":
        await state.set_state(IjaraRentOutStates.entering_rooms)
        await message.answer("Xonalar sonini kiriting:")
        return
    if message.text == "❌ Bekor qilish":
        await state.clear()
        await message.answer("Bekor qilindi.", reply_markup=get_ijara_menu())
        return
    try:
        floor = int(message.text.strip())
        if floor <= 0:
            raise ValueError
    except ValueError:
        await message.answer("❌ To'g'ri raqam kiriting!\n<i>Masalan: 5</i>", parse_mode="HTML")
        return
    await state.update_data(floor=floor)
    await state.set_state(IjaraRentOutStates.entering_total_floors)
    await message.answer(
        "🏢 <b>Jami qavatlar:</b>\n\n<i>Masalan: 9</i>",
        reply_markup=get_cancel_button(), parse_mode="HTML"
    )


@router.message(IjaraRentOutStates.entering_total_floors)
async def process_total_floors(message: Message, state: FSMContext):
    if message.text == "🔙 Orqaga":
        await state.set_state(IjaraRentOutStates.entering_floor)
        await message.answer("Qavat kiriting:")
        return
    if message.text == "❌ Bekor qilish":
        await state.clear()
        await message.answer("Bekor qilindi.", reply_markup=get_ijara_menu())
        return
    try:
        total_floors = int(message.text.strip())
        if total_floors <= 0:
            raise ValueError
        data = await state.get_data()
        if data.get('floor', 0) > total_floors:
            await message.answer("❌ Qavat jami qavatdan katta bo'lmasligi kerak!")
            return
    except ValueError:
        await message.answer("❌ To'g'ri raqam kiriting!\n<i>Masalan: 9</i>", parse_mode="HTML")
        return
    await state.update_data(total_floors=total_floors)
    await state.set_state(IjaraRentOutStates.entering_monthly_price)
    await message.answer(
        "💰 <b>Oylik ijara narxi (so'm):</b>\n\n<i>Masalan: 3000000</i>",
        reply_markup=get_cancel_button(), parse_mode="HTML"
    )


@router.message(IjaraRentOutStates.entering_monthly_price)
async def process_monthly_price(message: Message, state: FSMContext):
    if message.text == "🔙 Orqaga":
        data = await state.get_data()
        prop = data.get('property_type')
        if prop == 'apartment':
            await state.set_state(IjaraRentOutStates.entering_total_floors)
            await message.answer("Jami qavatlar:")
        elif prop == 'house':
            await state.set_state(IjaraRentOutStates.entering_rooms)
            await message.answer("Xonalar:")
        else:
            await state.set_state(IjaraRentOutStates.entering_area)
            await message.answer("Maydon:")
        return
    if message.text == "❌ Bekor qilish":
        await state.clear()
        await message.answer("Bekor qilindi.", reply_markup=get_ijara_menu())
        return
    try:
        price = float(message.text.replace(" ", "").replace(",", "").strip())
        if price <= 0:
            raise ValueError
    except ValueError:
        await message.answer("❌ To'g'ri narx kiriting!\n<i>Masalan: 3000000</i>", parse_mode="HTML")
        return
    await state.update_data(monthly_price=price)
    await state.set_state(IjaraRentOutStates.entering_rental_period)
    await message.answer(
        "📅 <b>Minimal ijara muddati:</b>",
        reply_markup=get_rental_period_keyboard(), parse_mode="HTML"
    )


@router.message(IjaraRentOutStates.entering_rental_period)
async def process_rental_period(message: Message, state: FSMContext):
    if message.text == "🔙 Orqaga":
        await state.set_state(IjaraRentOutStates.entering_monthly_price)
        await message.answer("Oylik narx:")
        return
    if message.text not in RENTAL_PERIODS:
        await message.answer("❌ Tugmalardan tanlang!", reply_markup=get_rental_period_keyboard())
        return
    await state.update_data(min_rental_period=message.text)
    await state.set_state(IjaraRentOutStates.entering_address)
    await message.answer(
        "📍 <b>Aniq manzil:</b>\n\n<i>Masalan: Chilonzor tumani, 9-kvartal</i>",
        reply_markup=get_cancel_button(), parse_mode="HTML"
    )


@router.message(IjaraRentOutStates.entering_address)
async def process_address(message: Message, state: FSMContext):
    if message.text == "🔙 Orqaga":
        await state.set_state(IjaraRentOutStates.entering_rental_period)
        await message.answer("Ijara muddati:", reply_markup=get_rental_period_keyboard())
        return
    if message.text == "❌ Bekor qilish":
        await state.clear()
        await message.answer("Bekor qilindi.", reply_markup=get_ijara_menu())
        return
    address = message.text.strip()
    if len(address) < 5:
        await message.answer("❌ Manzil juda qisqa! To'liq manzil kiriting.")
        return
    await state.update_data(address=address)
    await state.set_state(IjaraRentOutStates.entering_description)
    await message.answer(
        "📝 <b>Qo'shimcha ma'lumot:</b>\n\n<i>Ixtiyoriy.</i>",
        reply_markup=get_skip_and_cancel(), parse_mode="HTML"
    )


@router.message(IjaraRentOutStates.entering_description)
async def process_description(message: Message, state: FSMContext):
    if message.text == "🔙 Orqaga":
        await state.set_state(IjaraRentOutStates.entering_address)
        await message.answer("Manzil:")
        return
    if message.text == "❌ Bekor qilish":
        await state.clear()
        await message.answer("Bekor qilindi.", reply_markup=get_ijara_menu())
        return
    if message.text != "⏭️ O'tkazib yuborish":
        await state.update_data(description=message.text.strip())
    await state.set_state(IjaraRentOutStates.uploading_photo)
    await message.answer(
        "📸 <b>Rasm:</b>\n\n<i>Ixtiyoriy.</i>",
        reply_markup=get_skip_and_cancel(), parse_mode="HTML"
    )


@router.message(IjaraRentOutStates.uploading_photo, F.photo)
async def process_photo(message: Message, state: FSMContext):
    await state.update_data(photo_id=message.photo[-1].file_id)
    await state.set_state(IjaraRentOutStates.uploading_video)
    await message.answer(
        "🎥 <b>Video:</b>\n\n<i>Ixtiyoriy.</i>",
        reply_markup=get_skip_and_cancel(), parse_mode="HTML"
    )


@router.message(IjaraRentOutStates.uploading_photo)
async def process_photo_skip(message: Message, state: FSMContext):
    if message.text == "⏭️ O'tkazib yuborish":
        await state.set_state(IjaraRentOutStates.uploading_video)
        await message.answer(
            "🎥 <b>Video:</b>\n\n<i>Ixtiyoriy.</i>",
            reply_markup=get_skip_and_cancel(), parse_mode="HTML"
        )
    elif message.text == "❌ Bekor qilish":
        await state.clear()
        await message.answer("Bekor qilindi.", reply_markup=get_ijara_menu())
    else:
        await message.answer("❌ Rasm yuboring yoki o'tkazib yuboring!", reply_markup=get_skip_and_cancel())


@router.message(IjaraRentOutStates.uploading_video, F.video)
async def process_video(message: Message, state: FSMContext):
    await state.update_data(video_id=message.video.file_id)
    await show_confirmation(message, state)


@router.message(IjaraRentOutStates.uploading_video)
async def process_video_skip(message: Message, state: FSMContext):
    if message.text == "⏭️ O'tkazib yuborish":
        await show_confirmation(message, state)
    elif message.text == "❌ Bekor qilish":
        await state.clear()
        await message.answer("Bekor qilindi.", reply_markup=get_ijara_menu())
    else:
        await message.answer("❌ Video yuboring yoki o'tkazib yuboring!", reply_markup=get_skip_and_cancel())


async def show_confirmation(message: Message, state: FSMContext):
    data  = await state.get_data()
    text  = "📋 <b>Ijara e'loni:</b>\n\n"
    text += f"🗺️ {data.get('region_name')}\n"
    text += f"🏠 {data.get('property_type_name')}\n"
    text += f"👤 {data.get('full_name')}\n"
    text += f"📐 {format_area(data.get('area', 0))}\n"
    if data.get('rooms'):
        text += f"🚪 Xonalar: {data.get('rooms')}\n"
    if data.get('floor'):
        text += f"🏢 Qavat: {data.get('floor')}/{data.get('total_floors')}\n"
    text += f"💰 Oylik: {format_price(data.get('monthly_price', 0))}\n"
    text += f"📅 Muddat: {data.get('min_rental_period')}\n"
    text += f"📍 {data.get('address')}\n"
    if data.get('description'):
        desc = data['description']
        text += f"\n📝 {desc[:300]}{'...' if len(desc) > 300 else ''}\n"
    text += f"\n📸 {'✅' if data.get('photo_id') else '❌'} | 🎥 {'✅' if data.get('video_id') else '❌'}"
    text += "\n\n❓ E'lonni chop etamizmi?"
    await state.set_state(IjaraRentOutStates.confirmation)
    await message.answer(text, reply_markup=get_confirmation_keyboard(), parse_mode="HTML")


@router.message(IjaraRentOutStates.confirmation)
async def process_confirmation(message: Message, state: FSMContext):
    if message.text == "✅ Ha, e'lon berish":
        data       = await state.get_data()
        user_phone = data.get('phone')
        obj_data   = {
            'user_id':           message.from_user.id,
            'username':          message.from_user.username,
            'full_name':         data['full_name'],
            'phone':             ADMIN_PHONE,
            'region':            data['region'],
            'property_type':     data['property_type'],
            'action_type':       'rent_out',
            'area':              data.get('area'),
            'rooms':             data.get('rooms'),
            'floor':             data.get('floor'),
            'total_floors':      data.get('total_floors'),
            'monthly_price':     data['monthly_price'],
            'min_rental_period': data.get('min_rental_period'),
            'description':       data.get('description'),
            'photo_id':          data.get('photo_id'),
            'video_id':          data.get('video_id'),
            'address':           data['address']
        }
        try:
            obj_id = db.add_ijara(obj_data)
            await _send_to_admin(message.bot, data, obj_id, user_phone, message.from_user.id)
            await message.answer(
                "✅ <b>E'lon chop etildi!</b>\n\n"
                f"📞 Aloqa: {ADMIN_PHONE}",
                reply_markup=get_ijara_menu(), parse_mode="HTML"
            )
            logger.info(f"✅ Yangi ijara: ID={obj_id}, User={message.from_user.id}")
        except Exception as e:
            logger.error(f"❌ Xatolik: {e}", exc_info=True)
            await message.answer("❌ Xatolik!", reply_markup=get_ijara_menu())
        await state.clear()
    elif message.text == "❌ Bekor qilish":
        await state.clear()
        await message.answer("Bekor qilindi.", reply_markup=get_ijara_menu())


async def _send_to_admin(bot, data: dict, obj_id: int, user_phone: str, user_id: int):
    text  = "🆕 <b>YANGI IJARA E'LONI</b>\n\n"
    text += f"🆔 #{obj_id}\n\n"
    text += "👤 <b>IJARAGA BERUVCHI:</b>\n"
    text += f"├─ <b>Ism:</b> {data.get('full_name')}\n"
    text += f"├─ <b>Telefon:</b> <code>{user_phone}</code>\n"
    text += f"└─ <b>ID:</b> <code>{user_id}</code>\n\n"
    text += "🏠 <b>MULK:</b>\n"
    text += f"├─ <b>Tur:</b> {data.get('property_type_name')}\n"
    text += f"├─ <b>Viloyat:</b> {data.get('region_name')}\n"
    text += f"├─ <b>Maydon:</b> {format_area(data.get('area', 0))}\n"
    if data.get('rooms'):
        text += f"├─ <b>Xonalar:</b> {data.get('rooms')}\n"
    if data.get('floor'):
        text += f"├─ <b>Qavat:</b> {data.get('floor')}/{data.get('total_floors')}\n"
    text += f"├─ <b>Oylik:</b> {format_price(data.get('monthly_price', 0))}\n"
    text += f"├─ <b>Muddat:</b> {data.get('min_rental_period')}\n"
    text += f"└─ <b>Manzil:</b> {data.get('address')}\n\n"
    if data.get('description'):
        text += f"📝 {data['description'][:200]}\n\n"
    text += f"📅 {datetime.now().strftime('%d.%m.%Y %H:%M')}\n\n"
    text += "💬 <b>Mijoz bilan bog'laning!</b>"
    try:
        if data.get('photo_id'):
            await bot.send_photo(ADMIN_CHAT_ID, data['photo_id'], caption=text, parse_mode="HTML")
        else:
            await bot.send_message(ADMIN_CHAT_ID, text, parse_mode="HTML")
        if data.get('video_id'):
            await bot.send_video(ADMIN_CHAT_ID, data['video_id'], caption=f"🎥 Video — Ijara #{obj_id}")
        logger.info(f"✅ Admin'ga yuborildi: #{obj_id}")
    except Exception as e:
        logger.error(f"❌ Admin'ga yuborishda xato: {e}")