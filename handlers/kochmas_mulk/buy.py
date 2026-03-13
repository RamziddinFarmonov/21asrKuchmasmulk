"""
Ko'chmas Mulk - Sotib Olish - TO'LIQ TUZATILGAN

TUZATILGAN:
- split("_")[2] -> split("_")[-1] (IndexError xavfi bartaraf)
- apply_ijara_* callback qo'shildi (avval yo'q edi)
- state.clear() natijalardan OLDIN chaqiriladi
- Bo'sh telefon inputida IndexError - tekshiruv qo'shildi
- Ariza yuborilgandan keyin to'g'ri menyuga qaytish (obj_type bo'yicha)
"""
import logging
from datetime import datetime

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext

from utils.states import KochmasMulkBuyStates, ApplicationStates
from utils.keyboards import (
    get_regions_keyboard, get_districts_keyboard, get_property_types_keyboard,
    get_kochmas_mulk_menu, get_ijara_menu,
    get_cancel_button, get_skip_and_cancel
)
from utils.constants import (
    REGIONS, DISTRICTS, PROPERTY_TYPES,
    format_price, format_area,
    get_region_name_by_code, get_property_type_name_by_code,
    validate_phone, format_phone
)
from database.db_manager import db

router = Router()
logger = logging.getLogger(__name__)

ADMIN_PHONE   = "+998 91 007 00 21"
ADMIN_CHAT_ID = -1003037718098


# ============================================================================
# SOTIB OLISH - QIDIRUV
# ============================================================================

@router.message(F.text == "📥 Sotib olish")
async def start_buying(message: Message, state: FSMContext):
    await state.set_state(KochmasMulkBuyStates.choosing_region)
    await message.answer(
        "🗺️ <b>Qaysi viloyatdan qidiryapsiz?</b>",
        reply_markup=get_regions_keyboard(),
        parse_mode="HTML"
    )


@router.message(KochmasMulkBuyStates.choosing_region)
async def process_region_buy(message: Message, state: FSMContext):
    if message.text == "🔙 Orqaga":
        await state.clear()
        await message.answer("Ko'chmas mulk bo'limi:", reply_markup=get_kochmas_mulk_menu())
        return
    if message.text not in REGIONS:
        await message.answer("❌ Tugmalardan tanlang!", reply_markup=get_regions_keyboard())
        return
    region_code = REGIONS[message.text]
    await state.update_data(region=region_code, region_name=message.text)
    await state.set_state(KochmasMulkBuyStates.choosing_district)
    await message.answer(
        "🏘️ <b>Qaysi tumandan qidiryapsiz?</b>\n\nTumanni tanlang yoki o'tkazib yuboring:",
        reply_markup=get_districts_keyboard(region_code), parse_mode="HTML"
    )


@router.message(KochmasMulkBuyStates.choosing_district)
async def process_district_buy(message: Message, state: FSMContext):
    if message.text == "🔙 Orqaga":
        await state.set_state(KochmasMulkBuyStates.choosing_region)
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

    await state.set_state(KochmasMulkBuyStates.choosing_property_type)
    await message.answer(
        "🏠 <b>Qanday mulk qidiryapsiz?</b>",
        reply_markup=get_property_types_keyboard(), parse_mode="HTML"
    )


@router.message(KochmasMulkBuyStates.choosing_property_type)
async def process_property_type_buy(message: Message, state: FSMContext):
    if message.text == "🔙 Orqaga":
        data = await state.get_data()
        await state.set_state(KochmasMulkBuyStates.choosing_district)
        await message.answer(
            "🏘️ Tumanni tanlang:",
            reply_markup=get_districts_keyboard(data.get('region', ''))
        )
        return
    if message.text not in PROPERTY_TYPES:
        await message.answer("❌ Tugmalardan tanlang!", reply_markup=get_property_types_keyboard())
        return

    await state.update_data(
        property_type=PROPERTY_TYPES[message.text],
        property_type_name=message.text
    )
    data = await state.get_data()

    objects = db.get_kochmas_mulk_list(
        region=data['region'],
        district=data.get('district'),
        property_type=data['property_type'],
        action_type='sell',
        limit=50
    )
    await state.clear()

    if not objects:
        await message.answer(
            f"😔 <b>{data['region_name']} — {data['property_type_name']}</b>\n\n"
            "Hozircha e'lonlar yo'q.\nTez orada yangi e'lonlar qo'shiladi!",
            reply_markup=get_kochmas_mulk_menu(),
            parse_mode="HTML"
        )
        return

    keyboard = []
    for obj in objects[:50]:
        rooms = f"{obj['rooms']}-xona " if obj.get('rooms') else ""
        prop  = get_property_type_name_by_code(obj.get('property_type', ''))
        price = format_price(obj.get('price', 0))
        area  = format_area(obj.get('area', 0)) if obj.get('area') else ""
        label = f"🏠 {rooms}{prop} | {price}"
        if area:
            label += f" | {area}"
        keyboard.append([InlineKeyboardButton(
            text=label, callback_data=f"kochmas_view_{obj['id']}"
        )])
    keyboard.append([InlineKeyboardButton(text="🔙 Orqaga", callback_data="kochmas_back")])

    await message.answer(
        f"🏠 <b>{data['region_name']} — {data['property_type_name']}</b>\n\n"
        f"Topildi: <b>{len(objects)}</b> ta e'lon\n\n"
        "Batafsil ko'rish uchun tanlang:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard),
        parse_mode="HTML"
    )


# ============================================================================
# E'LON BATAFSIL
# ============================================================================

@router.callback_query(F.data.startswith("kochmas_view_"))
async def callback_view_object(callback: CallbackQuery):
    try:
        obj_id = int(callback.data.split("_")[-1])
    except (ValueError, IndexError):
        await callback.answer("❌ Xato", show_alert=True)
        return

    obj = db.get_kochmas_mulk_by_id(obj_id)
    if not obj:
        await callback.answer("❌ E'lon topilmadi!", show_alert=True)
        return

    text = f"🏠 <b>{get_property_type_name_by_code(obj.get('property_type', ''))}</b>\n\n"
    text += f"🗺️ <b>Viloyat:</b> {get_region_name_by_code(obj.get('region', ''))}\n"
    text += f"🏘️ <b>Tuman:</b> {obj.get('district') or '—'}\n"
    text += f"📐 <b>Maydon:</b> {format_area(obj.get('area', 0))}\n"
    if obj.get('rooms'):
        text += f"🚪 <b>Xonalar:</b> {obj['rooms']} ta\n"
    if obj.get('floor'):
        text += f"🏢 <b>Qavat:</b> {obj['floor']}/{obj.get('total_floors', '?')}\n"
    text += f"💰 <b>Narx:</b> {format_price(obj.get('price', 0))}\n"
    text += f"📍 <b>Manzil:</b> {obj.get('address', '—')}\n"
    if obj.get('description'):
        text += f"\n📝 <b>Tavsif:</b>\n{obj['description'][:300]}\n"
    text += f"\n📞 <b>Bog'lanish:</b> {ADMIN_PHONE}"
    text += f"\n\n🆔 E'lon #{obj['id']}"

    is_fav = db.is_favorite(callback.from_user.id, obj_id, 'kochmas')
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📤 Ariza yuborish", callback_data=f"apply_kochmas_{obj_id}")],
        [InlineKeyboardButton(
            text="❤️ Sevimlilardan o'chirish" if is_fav else "🤍 Sevimlilarga qo'shish",
            callback_data=f"fav_kochmas_{obj_id}"
        )],
        [InlineKeyboardButton(text="🔙 Orqaga", callback_data="kochmas_back")]
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


@router.callback_query(F.data == "kochmas_back")
async def callback_kochmas_back(callback: CallbackQuery):
    chat_id = callback.message.chat.id
    try:
        await callback.message.delete()
    except Exception:
        pass
    await callback.bot.send_message(
        chat_id=chat_id,
        text="🏠 Ko'chmas mulk bo'limi:",
        reply_markup=get_kochmas_mulk_menu()
    )
    await callback.answer()


# ============================================================================
# SEVIMLILAR
# ============================================================================

@router.message(F.text == "❤️ Sevimlilar")
async def show_kochmas_favorites(message: Message):
    objects = db.get_user_favorites(message.from_user.id, 'kochmas')
    if not objects:
        await message.answer(
            "💔 <b>Sevimlilar bo'sh</b>\n\nHali sevimli e'lonlar yo'q.",
            reply_markup=get_kochmas_mulk_menu(), parse_mode="HTML"
        )
        return
    keyboard = []
    for obj in objects:
        rooms = f"{obj['rooms']}-xona " if obj.get('rooms') else ""
        prop  = get_property_type_name_by_code(obj.get('property_type', ''))
        price = format_price(obj.get('price', 0))
        keyboard.append([InlineKeyboardButton(
            text=f"🏠 {rooms}{prop} | {price}",
            callback_data=f"kochmas_view_{obj['id']}"
        )])
    keyboard.append([InlineKeyboardButton(text="🔙 Orqaga", callback_data="kochmas_back")])
    await message.answer(
        f"❤️ <b>SEVIMLI KO'CHMAS MULKLAR</b>\n\nJami: {len(objects)} ta\n",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard), parse_mode="HTML"
    )


@router.callback_query(F.data.startswith("fav_kochmas_"))
async def callback_toggle_favorite(callback: CallbackQuery):
    try:
        obj_id = int(callback.data.split("_")[-1])
    except (ValueError, IndexError):
        await callback.answer("❌ Xato", show_alert=True)
        return
    user_id = callback.from_user.id
    is_fav  = db.is_favorite(user_id, obj_id, 'kochmas')
    if is_fav:
        db.remove_favorite(user_id, obj_id, 'kochmas')
        await callback.answer("💔 Sevimlilardan o'chirildi")
    else:
        db.add_favorite(user_id, obj_id, 'kochmas')
        await callback.answer("❤️ Sevimlilarga qo'shildi")
    await callback_view_object(callback)


# ============================================================================
# ARIZA YUBORISH - FSM
# ============================================================================

@router.callback_query(F.data.startswith("apply_kochmas_"))
async def callback_apply_kochmas(callback: CallbackQuery, state: FSMContext):
    try:
        obj_id = int(callback.data.split("_")[-1])
    except (ValueError, IndexError):
        await callback.answer("❌ Xato", show_alert=True)
        return
    await state.update_data(apply_object_id=obj_id, apply_object_type='kochmas')
    await state.set_state(ApplicationStates.entering_name)
    await callback.message.answer(
        "📝 <b>ARIZA YUBORISH</b>\n\n"
        "👤 <b>1/3:</b> Ism-familiyangizni kiriting:\n\n"
        "<i>Masalan: Aliyev Vali</i>",
        reply_markup=get_cancel_button(), parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data.startswith("apply_ijara_"))
async def callback_apply_ijara(callback: CallbackQuery, state: FSMContext):
    try:
        obj_id = int(callback.data.split("_")[-1])
    except (ValueError, IndexError):
        await callback.answer("❌ Xato", show_alert=True)
        return
    await state.update_data(apply_object_id=obj_id, apply_object_type='ijara')
    await state.set_state(ApplicationStates.entering_name)
    await callback.message.answer(
        "📝 <b>ARIZA YUBORISH</b>\n\n"
        "👤 <b>1/3:</b> Ism-familiyangizni kiriting:\n\n"
        "<i>Masalan: Aliyev Vali</i>",
        reply_markup=get_cancel_button(), parse_mode="HTML"
    )
    await callback.answer()


@router.message(ApplicationStates.entering_name)
async def process_application_name(message: Message, state: FSMContext):
    if message.text == "❌ Bekor qilish":
        data = await state.get_data()
        obj_type = data.get('apply_object_type', 'kochmas')
        await state.clear()
        await message.answer("Bekor qilindi.",
            reply_markup=get_ijara_menu() if obj_type == 'ijara' else get_kochmas_mulk_menu())
        return
    name = message.text.strip()
    if len(name.split()) < 2:
        await message.answer(
            "❌ To'liq ism-familiya kiriting!\n<i>Masalan: Aliyev Vali</i>",
            parse_mode="HTML"
        )
        return
    await state.update_data(apply_name=name)
    await state.set_state(ApplicationStates.entering_phone)
    await message.answer(
        "📝 <b>ARIZA YUBORISH</b>\n\n"
        "📱 <b>2/3:</b> Telefon raqamingizni kiriting:\n\n"
        "<i>Format: +998 XX XXX XX XX</i>",
        reply_markup=get_cancel_button(), parse_mode="HTML"
    )


@router.message(ApplicationStates.entering_phone)
async def process_application_phone(message: Message, state: FSMContext):
    if message.text == "❌ Bekor qilish":
        data = await state.get_data()
        obj_type = data.get('apply_object_type', 'kochmas')
        await state.clear()
        await message.answer("Bekor qilindi.",
            reply_markup=get_ijara_menu() if obj_type == 'ijara' else get_kochmas_mulk_menu())
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
    await state.update_data(apply_phone=format_phone(phone))
    await state.set_state(ApplicationStates.entering_comment)
    await message.answer(
        "📝 <b>ARIZA YUBORISH</b>\n\n"
        "💬 <b>3/3:</b> Qo'shimcha izoh (ixtiyoriy):\n\n"
        "<i>Masalan: Tezroq javob bering</i>",
        reply_markup=get_skip_and_cancel(), parse_mode="HTML"
    )


@router.message(ApplicationStates.entering_comment)
async def process_application_comment(message: Message, state: FSMContext):
    if message.text == "❌ Bekor qilish":
        data = await state.get_data()
        obj_type = data.get('apply_object_type', 'kochmas')
        await state.clear()
        await message.answer("Bekor qilindi.",
            reply_markup=get_ijara_menu() if obj_type == 'ijara' else get_kochmas_mulk_menu())
        return

    comment  = message.text.strip() if message.text != "⏭️ O'tkazib yuborish" else ""
    data     = await state.get_data()
    obj_id   = data.get('apply_object_id')
    obj_type = data.get('apply_object_type', 'kochmas')

    obj = (
        db.get_kochmas_mulk_by_id(obj_id) if obj_type == 'kochmas'
        else db.get_ijara_by_id(obj_id)
    )
    if not obj:
        await message.answer("❌ E'lon topilmadi!", reply_markup=get_kochmas_mulk_menu())
        await state.clear()
        return

    await _send_application_to_admin(
        bot=message.bot,
        user_id=message.from_user.id,
        username=message.from_user.username,
        name=data.get('apply_name', ''),
        phone=data.get('apply_phone', ''),
        comment=comment,
        obj=obj,
        obj_type=obj_type
    )

    menu = get_ijara_menu() if obj_type == 'ijara' else get_kochmas_mulk_menu()
    await message.answer(
        "✅ <b>Arizangiz yuborildi!</b>\n\n"
        "Tez orada admin siz bilan bog'lanadi.\n\nRahmat! 🙏",
        reply_markup=menu, parse_mode="HTML"
    )
    await state.clear()


async def _send_application_to_admin(bot, user_id, username, name, phone, comment, obj, obj_type):
    text  = "🆕 <b>YANGI ARIZA!</b>\n\n"
    ariza_turi = "Ko'chmas mulk" if obj_type == 'kochmas' else "Ijara"
    text += f"📋 <b>Ariza turi:</b> {ariza_turi}\n\n"
    text += "👤 <b>XARIDOR:</b>\n"
    text += f"├─ <b>Ism:</b> {name}\n"
    text += f"├─ <b>Telefon:</b> <code>{phone}</code>\n"
    text += f"├─ <b>Username:</b> @{username or 'yoq'}\n"
    text += f"└─ <b>User ID:</b> <code>{user_id}</code>\n\n"
    text += "🏠 <b>E'LON:</b>\n"
    text += f"├─ <b>ID:</b> #{obj['id']}\n"
    text += f"├─ <b>Tur:</b> {get_property_type_name_by_code(obj.get('property_type', ''))}\n"
    text += f"├─ <b>Viloyat:</b> {get_region_name_by_code(obj.get('region', ''))}\n"
    if obj_type == 'kochmas':
        text += f"├─ <b>Narx:</b> {format_price(obj.get('price', 0))}\n"
    else:
        text += f"├─ <b>Oylik:</b> {format_price(obj.get('monthly_price', 0))}\n"
    text += f"└─ <b>Manzil:</b> {obj.get('address', '—')}\n\n"
    if comment:
        text += f"💬 <b>Izoh:</b>\n{comment}\n\n"
    text += f"📅 {datetime.now().strftime('%d.%m.%Y %H:%M')}\n\n"
    text += "💼 <b>Mijoz bilan bog'laning!</b>"
    try:
        await bot.send_message(ADMIN_CHAT_ID, text, parse_mode="HTML")
        logger.info(f"✅ Ariza yuborildi: User {user_id}, E'lon #{obj['id']}")
    except Exception as e:
        logger.error(f"❌ Ariza yuborishda xato: {e}")