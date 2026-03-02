"""
Ijara - Mening E'lonlarim
FAQAT Ijara e'lonlari ko'rsatiladi (ko'chmas mulk aralashtirilmaydi)
"""
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext

router = Router()


@router.message(F.text == "📊 Mening e'lonlarim")
async def ijara_my_objects_menu(message: Message, state: FSMContext = None):
    """Ijara bo'limidagi mening e'lonlarim - FAQAT Ijara"""
    if state:
        await state.clear()

    from database.db_manager import db
    from utils.constants import format_price, format_area, get_property_type_name_by_code, get_region_name_by_code
    from utils.keyboards import get_ijara_menu

    user_id = message.from_user.id
    objects = db.get_user_ijara(user_id) or []

    if not objects:
        await message.answer(
            "📊 <b>MENING IJARA E'LONLARIM</b>\n\n"
            "📭 Sizda hali ijara e'loni yo'q.\n\n"
            "📤 <b>Ijaraga berish</b> tugmasi orqali e'lon bering!",
            reply_markup=get_ijara_menu(),
            parse_mode="HTML"
        )
        return

    keyboard = []
    for obj in objects:
        prop   = get_property_type_name_by_code(obj.get('property_type', ''))
        rooms  = f"{obj['rooms']}-xona " if obj.get('rooms') else ""
        price  = format_price(obj.get('monthly_price', 0))
        region = get_region_name_by_code(obj.get('region', ''))
        area   = format_area(obj.get('area', 0)) if obj.get('area') else ""

        label = f"📋 {rooms}{prop} | {price}/oy"
        if area:
            label += f" | {area}"
        label += f" | {region}"

        keyboard.append([InlineKeyboardButton(
            text=label[:64],
            callback_data=f"ijara_myobj_{obj['id']}"
        )])

    keyboard.append([InlineKeyboardButton(text="🔙 Orqaga", callback_data="ijara_myobj_menu_back")])

    await message.answer(
        f"📊 <b>MENING IJARA E'LONLARIM</b>\n\n"
        f"Jami: <b>{len(objects)}</b> ta e'lon\n\n"
        "Batafsil ko'rish uchun e'lonni tanlang 👇",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard),
        parse_mode="HTML"
    )


@router.callback_query(F.data.startswith("ijara_myobj_") & ~F.data.in_({"ijara_myobj_menu_back"}))
async def view_ijara_my_detail(callback: CallbackQuery):
    from database.db_manager import db
    from utils.constants import format_price, format_area, get_property_type_name_by_code, get_region_name_by_code

    try:
        obj_id = int(callback.data.split("_")[-1])
    except (ValueError, IndexError):
        await callback.answer("❌ Xato", show_alert=True)
        return

    obj = db.get_ijara_by_id(obj_id)
    if not obj:
        await callback.answer("❌ E'lon topilmadi!", show_alert=True)
        return

    text = (
        f"📋 <b>{get_property_type_name_by_code(obj.get('property_type', ''))} — Ijara</b>\n\n"
        f"🆔 E'lon #{obj['id']}\n"
        f"📅 {obj.get('created_at', '')}\n\n"
        f"🗺️ <b>Viloyat:</b> {get_region_name_by_code(obj.get('region', ''))}\n"
        f"📐 <b>Maydon:</b> {format_area(obj.get('area', 0))}\n"
    )
    if obj.get('rooms'):
        text += f"🚪 <b>Xonalar:</b> {obj['rooms']} ta\n"
    if obj.get('floor'):
        text += f"🏢 <b>Qavat:</b> {obj['floor']}/{obj.get('total_floors', '?')}\n"
    text += f"💰 <b>Oylik narx:</b> {format_price(obj.get('monthly_price', 0))}/oy\n"
    if obj.get('min_rental_period'):
        text += f"📅 <b>Min. muddat:</b> {obj['min_rental_period']}\n"
    text += f"📍 <b>Manzil:</b> {obj.get('address', '—')}\n"
    if obj.get('description'):
        text += f"\n📝 <b>Tavsif:</b>\n{obj['description'][:300]}\n"
    text += (
        f"\n📸 Rasm: {'✅' if obj.get('photo_id') else '❌'} | "
        f"🎥 Video: {'✅' if obj.get('video_id') else '❌'}\n"
        "\n⚠️ <i>O'zgartirish uchun admin bilan bog'laning</i>"
    )

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Mening e'lonlarim", callback_data="ijara_myobj_menu_back")]
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
                    video=obj['video_id'], caption=f"🎥 Video #{obj['id']}"
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


@router.callback_query(F.data == "ijara_myobj_menu_back")
async def back_ijara_my_objects(callback: CallbackQuery):
    try:
        await callback.message.delete()
    except Exception:
        pass
    await ijara_my_objects_menu(callback.message)
    await callback.answer()