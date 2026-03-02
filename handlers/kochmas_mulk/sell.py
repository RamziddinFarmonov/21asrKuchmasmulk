"""
Ko'chmas Mulk - Sotish - TO'LIQ TUZATILGAN

TUZATILGAN:
- Bo'sh telefon kiritilsa IndexError - strip() + empty check
- description[:300] tasdiqlashda truncate + '...' qo'shildi
- send_to_admin da description get() bilan xavfsiz olish
"""
import logging
from datetime import datetime

from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

from utils.states import KochmasMulkSellStates
from utils.keyboards import (
    get_regions_keyboard, get_property_types_keyboard,
    get_cancel_button, get_skip_and_cancel,
    get_confirmation_keyboard, get_kochmas_mulk_menu
)
from utils.constants import (
    REGIONS, PROPERTY_TYPES,
    format_price, format_area, format_phone, validate_phone
)
from database.db_manager import db

router = Router()
logger = logging.getLogger(__name__)

ADMIN_CHAT_ID = -1003037718098
ADMIN_PHONE   = "+998910070021"


@router.message(F.text == "📤 Sotish")
async def start_selling(message: Message, state: FSMContext):
    await state.set_state(KochmasMulkSellStates.choosing_region)
    await message.answer(
        "🗺️ <b>Qaysi viloyatda joylashgan?</b>\n\nMulkingiz joylashgan viloyatni tanlang:",
        reply_markup=get_regions_keyboard(), parse_mode="HTML"
    )


@router.message(KochmasMulkSellStates.choosing_region)
async def process_region(message: Message, state: FSMContext):
    if message.text == "🔙 Orqaga":
        await state.clear()
        await message.answer("Ko'chmas mulk bo'limi:", reply_markup=get_kochmas_mulk_menu())
        return
    if message.text not in REGIONS:
        await message.answer("❌ Iltimos, tugmalardan birini tanlang!", reply_markup=get_regions_keyboard())
        return
    await state.update_data(region=REGIONS[message.text], region_name=message.text)
    await state.set_state(KochmasMulkSellStates.choosing_property_type)
    await message.answer(
        "🏠 <b>Mulk turini tanlang:</b>",
        reply_markup=get_property_types_keyboard(), parse_mode="HTML"
    )


@router.message(KochmasMulkSellStates.choosing_property_type)
async def process_property_type(message: Message, state: FSMContext):
    if message.text == "🔙 Orqaga":
        await state.set_state(KochmasMulkSellStates.choosing_region)
        await message.answer("Viloyatni tanlang:", reply_markup=get_regions_keyboard())
        return
    if message.text not in PROPERTY_TYPES:
        await message.answer("❌ Iltimos, tugmalardan birini tanlang!", reply_markup=get_property_types_keyboard())
        return
    await state.update_data(property_type=PROPERTY_TYPES[message.text], property_type_name=message.text)
    await state.set_state(KochmasMulkSellStates.entering_full_name)
    await message.answer(
        "👤 <b>Ism-familiyangiz:</b>\n\n"
        "To'liq ism-familiyangizni kiriting:\n"
        "<i>Masalan: Aliyev Vali Akbarovich</i>",
        reply_markup=get_cancel_button(), parse_mode="HTML"
    )


@router.message(KochmasMulkSellStates.entering_full_name)
async def process_full_name(message: Message, state: FSMContext):
    if message.text == "🔙 Orqaga":
        await state.set_state(KochmasMulkSellStates.choosing_property_type)
        await message.answer("Mulk turini tanlang:", reply_markup=get_property_types_keyboard())
        return
    if message.text == "❌ Bekor qilish":
        await state.clear()
        await message.answer("Bekor qilindi.", reply_markup=get_kochmas_mulk_menu())
        return
    full_name = message.text.strip()
    if len(full_name.split()) < 2:
        await message.answer(
            "❌ To'liq ism-familiya kiriting!\n<i>Masalan: Aliyev Vali</i>", parse_mode="HTML"
        )
        return
    await state.update_data(full_name=full_name)
    await state.set_state(KochmasMulkSellStates.entering_phone)
    await message.answer(
        "📱 <b>Telefon raqamingiz:</b>\n\n"
        "Bog'lanish uchun telefon raqamingizni kiriting:\n"
        "<i>Format: +998 XX XXX XX XX</i>\n\n"
        "⚠️ <i>Bu raqam faqat admin ko'radi</i>",
        reply_markup=get_cancel_button(), parse_mode="HTML"
    )


@router.message(KochmasMulkSellStates.entering_phone)
async def process_phone(message: Message, state: FSMContext):
    if message.text == "🔙 Orqaga":
        await state.set_state(KochmasMulkSellStates.entering_full_name)
        await message.answer("Ism-familiyangizni kiriting:")
        return
    if message.text == "❌ Bekor qilish":
        await state.clear()
        await message.answer("Bekor qilindi.", reply_markup=get_kochmas_mulk_menu())
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
    data = await state.get_data()
    await state.set_state(KochmasMulkSellStates.entering_area)
    if data.get('property_type') == 'land':
        await message.answer(
            "📐 <b>Yer uchastkasi maydoni (sotix):</b>\n\n<i>Masalan: 6</i>",
            reply_markup=get_cancel_button(), parse_mode="HTML"
        )
    else:
        await message.answer(
            "📐 <b>Umumiy maydoni (m²):</b>\n\n<i>Masalan: 65.5</i>",
            reply_markup=get_cancel_button(), parse_mode="HTML"
        )


@router.message(KochmasMulkSellStates.entering_area)
async def process_area(message: Message, state: FSMContext):
    if message.text == "🔙 Orqaga":
        await state.set_state(KochmasMulkSellStates.entering_phone)
        await message.answer("Telefon raqamingizni kiriting:")
        return
    if message.text == "❌ Bekor qilish":
        await state.clear()
        await message.answer("Bekor qilindi.", reply_markup=get_kochmas_mulk_menu())
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
        await state.set_state(KochmasMulkSellStates.entering_rooms)
        await message.answer(
            "🚪 <b>Xonalar soni:</b>\n\n<i>Masalan: 3</i>",
            reply_markup=get_cancel_button(), parse_mode="HTML"
        )
    else:
        await state.set_state(KochmasMulkSellStates.entering_price)
        await message.answer(
            "💰 <b>Narxi (so'm):</b>\n\n<i>Masalan: 500000000</i>",
            reply_markup=get_cancel_button(), parse_mode="HTML"
        )


@router.message(KochmasMulkSellStates.entering_rooms)
async def process_rooms(message: Message, state: FSMContext):
    if message.text == "🔙 Orqaga":
        await state.set_state(KochmasMulkSellStates.entering_area)
        await message.answer("Maydonni kiriting:")
        return
    if message.text == "❌ Bekor qilish":
        await state.clear()
        await message.answer("Bekor qilindi.", reply_markup=get_kochmas_mulk_menu())
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
        await state.set_state(KochmasMulkSellStates.entering_floor)
        await message.answer(
            "🏢 <b>Qaysi qavatda?</b>\n\n<i>Masalan: 5</i>",
            reply_markup=get_cancel_button(), parse_mode="HTML"
        )
    else:
        await state.set_state(KochmasMulkSellStates.entering_price)
        await message.answer(
            "💰 <b>Narxi (so'm):</b>\n\n<i>Masalan: 500000000</i>",
            reply_markup=get_cancel_button(), parse_mode="HTML"
        )


@router.message(KochmasMulkSellStates.entering_floor)
async def process_floor(message: Message, state: FSMContext):
    if message.text == "🔙 Orqaga":
        await state.set_state(KochmasMulkSellStates.entering_rooms)
        await message.answer("Xonalar sonini kiriting:")
        return
    if message.text == "❌ Bekor qilish":
        await state.clear()
        await message.answer("Bekor qilindi.", reply_markup=get_kochmas_mulk_menu())
        return
    try:
        floor = int(message.text.strip())
        if floor <= 0:
            raise ValueError
    except ValueError:
        await message.answer("❌ To'g'ri raqam kiriting!\n<i>Masalan: 5</i>", parse_mode="HTML")
        return
    await state.update_data(floor=floor)
    await state.set_state(KochmasMulkSellStates.entering_total_floors)
    await message.answer(
        "🏢 <b>Binoning jami qavatlar soni:</b>\n\n<i>Masalan: 9</i>",
        reply_markup=get_cancel_button(), parse_mode="HTML"
    )


@router.message(KochmasMulkSellStates.entering_total_floors)
async def process_total_floors(message: Message, state: FSMContext):
    if message.text == "🔙 Orqaga":
        await state.set_state(KochmasMulkSellStates.entering_floor)
        await message.answer("Qavat raqamini kiriting:")
        return
    if message.text == "❌ Bekor qilish":
        await state.clear()
        await message.answer("Bekor qilindi.", reply_markup=get_kochmas_mulk_menu())
        return
    try:
        total_floors = int(message.text.strip())
        if total_floors <= 0:
            raise ValueError
        data  = await state.get_data()
        floor = data.get('floor', 0)
        if floor > total_floors:
            await message.answer(
                f"❌ Xato! Siz {floor}-qavatda deb ko'rsatdingiz,\n"
                f"lekin jami {total_floors} qavat bo'lishi mumkin emas.\n"
                "Iltimos, to'g'ri raqam kiriting:"
            )
            return
    except ValueError:
        await message.answer("❌ To'g'ri raqam kiriting!\n<i>Masalan: 9</i>", parse_mode="HTML")
        return
    await state.update_data(total_floors=total_floors)
    await state.set_state(KochmasMulkSellStates.entering_price)
    await message.answer(
        "💰 <b>Narxi (so'm):</b>\n\n<i>Masalan: 500000000</i>",
        reply_markup=get_cancel_button(), parse_mode="HTML"
    )


@router.message(KochmasMulkSellStates.entering_price)
async def process_price(message: Message, state: FSMContext):
    if message.text == "🔙 Orqaga":
        data = await state.get_data()
        prop = data.get('property_type')
        if prop == 'apartment':
            await state.set_state(KochmasMulkSellStates.entering_total_floors)
            await message.answer("Jami qavatlar sonini kiriting:")
        elif prop == 'house':
            await state.set_state(KochmasMulkSellStates.entering_rooms)
            await message.answer("Xonalar sonini kiriting:")
        else:
            await state.set_state(KochmasMulkSellStates.entering_area)
            await message.answer("Maydonni kiriting:")
        return
    if message.text == "❌ Bekor qilish":
        await state.clear()
        await message.answer("Bekor qilindi.", reply_markup=get_kochmas_mulk_menu())
        return
    try:
        price = float(message.text.replace(" ", "").replace(",", "").strip())
        if price <= 0:
            raise ValueError
    except ValueError:
        await message.answer("❌ To'g'ri narx kiriting!\n<i>Masalan: 500000000</i>", parse_mode="HTML")
        return
    await state.update_data(price=price)
    await state.set_state(KochmasMulkSellStates.entering_address)
    await message.answer(
        "📍 <b>Manzil:</b>\n\n<i>Masalan: Chilonzor tumani, 9-kvartal, 12-uy</i>",
        reply_markup=get_cancel_button(), parse_mode="HTML"
    )


@router.message(KochmasMulkSellStates.entering_address)
async def process_address(message: Message, state: FSMContext):
    if message.text == "🔙 Orqaga":
        await state.set_state(KochmasMulkSellStates.entering_price)
        await message.answer("Narxni kiriting:")
        return
    if message.text == "❌ Bekor qilish":
        await state.clear()
        await message.answer("Bekor qilindi.", reply_markup=get_kochmas_mulk_menu())
        return
    address = message.text.strip()
    if len(address) < 5:
        await message.answer("❌ Manzil juda qisqa! To'liq manzil kiriting.")
        return
    await state.update_data(address=address)
    await state.set_state(KochmasMulkSellStates.entering_description)
    await message.answer(
        "📝 <b>Qo'shimcha ma'lumot:</b>\n\n"
        "Ta'mirlash holati, jihozlar, atrofi...\n\n"
        "<i>Ixtiyoriy. O'tkazib yuborishingiz mumkin.</i>",
        reply_markup=get_skip_and_cancel(), parse_mode="HTML"
    )


@router.message(KochmasMulkSellStates.entering_description)
async def process_description(message: Message, state: FSMContext):
    if message.text == "🔙 Orqaga":
        await state.set_state(KochmasMulkSellStates.entering_address)
        await message.answer("Manzilni kiriting:")
        return
    if message.text == "❌ Bekor qilish":
        await state.clear()
        await message.answer("Bekor qilindi.", reply_markup=get_kochmas_mulk_menu())
        return
    if message.text != "⏭️ O'tkazib yuborish":
        await state.update_data(description=message.text.strip())
    await state.set_state(KochmasMulkSellStates.uploading_photo)
    await message.answer(
        "📸 <b>Rasm yuklang:</b>\n\n<i>Ixtiyoriy. O'tkazib yuborishingiz mumkin.</i>",
        reply_markup=get_skip_and_cancel(), parse_mode="HTML"
    )


@router.message(KochmasMulkSellStates.uploading_photo, F.photo)
async def process_photo(message: Message, state: FSMContext):
    await state.update_data(photo_id=message.photo[-1].file_id)
    await state.set_state(KochmasMulkSellStates.uploading_video)
    await message.answer(
        "🎥 <b>Video yuklang:</b>\n\n<i>Ixtiyoriy. O'tkazib yuborishingiz mumkin.</i>",
        reply_markup=get_skip_and_cancel(), parse_mode="HTML"
    )


@router.message(KochmasMulkSellStates.uploading_photo)
async def process_photo_skip(message: Message, state: FSMContext):
    if message.text == "⏭️ O'tkazib yuborish":
        await state.set_state(KochmasMulkSellStates.uploading_video)
        await message.answer(
            "🎥 <b>Video yuklang:</b>\n\n<i>Ixtiyoriy. O'tkazib yuborishingiz mumkin.</i>",
            reply_markup=get_skip_and_cancel(), parse_mode="HTML"
        )
    elif message.text == "❌ Bekor qilish":
        await state.clear()
        await message.answer("Bekor qilindi.", reply_markup=get_kochmas_mulk_menu())
    else:
        await message.answer("❌ Rasm yuboring yoki o'tkazib yuboring!", reply_markup=get_skip_and_cancel())


@router.message(KochmasMulkSellStates.uploading_video, F.video)
async def process_video(message: Message, state: FSMContext):
    await state.update_data(video_id=message.video.file_id)
    await show_confirmation(message, state)


@router.message(KochmasMulkSellStates.uploading_video)
async def process_video_skip(message: Message, state: FSMContext):
    if message.text == "⏭️ O'tkazib yuborish":
        await show_confirmation(message, state)
    elif message.text == "❌ Bekor qilish":
        await state.clear()
        await message.answer("Bekor qilindi.", reply_markup=get_kochmas_mulk_menu())
    else:
        await message.answer("❌ Video yuboring yoki o'tkazib yuboring!", reply_markup=get_skip_and_cancel())


async def show_confirmation(message: Message, state: FSMContext):
    data = await state.get_data()
    text  = "📋 <b>E'lon ma'lumotlari:</b>\n\n"
    text += f"🗺️ <b>Viloyat:</b> {data.get('region_name')}\n"
    text += f"🏠 <b>Tur:</b> {data.get('property_type_name')}\n"
    text += f"👤 <b>Ism-familiya:</b> {data.get('full_name')}\n"
    text += f"📐 <b>Maydon:</b> {format_area(data.get('area', 0))}\n"
    if data.get('rooms'):
        text += f"🚪 <b>Xonalar:</b> {data.get('rooms')} ta\n"
    if data.get('floor'):
        text += f"🏢 <b>Qavat:</b> {data.get('floor')}/{data.get('total_floors')}\n"
    text += f"💰 <b>Narx:</b> {format_price(data.get('price', 0))}\n"
    text += f"📍 <b>Manzil:</b> {data.get('address')}\n"
    if data.get('description'):
        desc = data['description']
        text += f"\n📝 <b>Tavsif:</b>\n{desc[:300]}{'...' if len(desc) > 300 else ''}\n"
    text += f"\n📸 Rasm: {'✅' if data.get('photo_id') else '❌'}"
    text += f" | 🎥 Video: {'✅' if data.get('video_id') else '❌'}"
    text += "\n\n❓ <b>E'lonni chop etamizmi?</b>"
    await state.set_state(KochmasMulkSellStates.confirmation)
    await message.answer(text, reply_markup=get_confirmation_keyboard(), parse_mode="HTML")


@router.message(KochmasMulkSellStates.confirmation)
async def process_confirmation(message: Message, state: FSMContext):
    if message.text == "✅ Ha, e'lon berish":
        data       = await state.get_data()
        user_phone = data.get('phone')
        object_data = {
            'user_id':       message.from_user.id,
            'username':      message.from_user.username,
            'full_name':     data['full_name'],
            'phone':         ADMIN_PHONE,
            'region':        data['region'],
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
        }
        try:
            object_id = db.add_kochmas_mulk(object_data)
            await _send_to_admin(message.bot, data, object_id, user_phone, message.from_user.id)
            await message.answer(
                "✅ <b>E'loningiz muvaffaqiyatli chop etildi!</b>\n\n"
                "Xaridorlar admin orqali siz bilan bog'lanishadi.\n\n"
                f"📞 <b>Aloqa:</b> {ADMIN_PHONE}",
                reply_markup=get_kochmas_mulk_menu(), parse_mode="HTML"
            )
            logger.info(f"✅ Yangi e'lon: ID={object_id}, User={message.from_user.id}")
        except Exception as e:
            logger.error(f"❌ Xatolik: {e}", exc_info=True)
            await message.answer(
                "❌ Xatolik yuz berdi. Iltimos, qaytadan urinib ko'ring.",
                reply_markup=get_kochmas_mulk_menu()
            )
        await state.clear()
    elif message.text == "❌ Bekor qilish":
        await state.clear()
        await message.answer("Bekor qilindi.", reply_markup=get_kochmas_mulk_menu())


async def _send_to_admin(bot, data: dict, object_id: int, user_phone: str, user_id: int):
    text  = "🆕 <b>YANGI E'LON — Ko'chmas Mulk</b>\n\n"
    text += f"🆔 <b>ID:</b> #{object_id}\n\n"
    text += "👤 <b>SOTUVCHI:</b>\n"
    text += f"├─ <b>Ism:</b> {data.get('full_name')}\n"
    text += f"├─ <b>Telefon:</b> <code>{user_phone}</code>\n"
    text += f"└─ <b>User ID:</b> <code>{user_id}</code>\n\n"
    text += "🏠 <b>MULK:</b>\n"
    text += f"├─ <b>Tur:</b> {data.get('property_type_name')}\n"
    text += f"├─ <b>Viloyat:</b> {data.get('region_name')}\n"
    text += f"├─ <b>Maydon:</b> {format_area(data.get('area', 0))}\n"
    if data.get('rooms'):
        text += f"├─ <b>Xonalar:</b> {data.get('rooms')} ta\n"
    if data.get('floor'):
        text += f"├─ <b>Qavat:</b> {data.get('floor')}/{data.get('total_floors')}\n"
    text += f"├─ <b>Narx:</b> {format_price(data.get('price', 0))}\n"
    text += f"└─ <b>Manzil:</b> {data.get('address')}\n\n"
    if data.get('description'):
        text += f"📝 <b>Tavsif:</b>\n{data['description'][:300]}\n\n"
    text += f"📅 {datetime.now().strftime('%d.%m.%Y %H:%M')}\n\n"
    text += "💬 <b>Mijoz bilan bog'laning!</b>"
    try:
        if data.get('photo_id'):
            await bot.send_photo(ADMIN_CHAT_ID, data['photo_id'], caption=text, parse_mode="HTML")
            if data.get('video_id'):
                await bot.send_video(ADMIN_CHAT_ID, data['video_id'], caption=f"🎥 Video — E'lon #{object_id}")
        else:
            await bot.send_message(ADMIN_CHAT_ID, text, parse_mode="HTML")
            if data.get('video_id'):
                await bot.send_video(ADMIN_CHAT_ID, data['video_id'], caption=f"🎥 Video — E'lon #{object_id}")
        logger.info(f"✅ Admin'ga yuborildi: #{object_id}")
    except Exception as e:
        logger.error(f"❌ Admin'ga yuborishda xato: {e}")