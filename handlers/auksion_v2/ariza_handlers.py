"""
ARIZA YUBORISH - TO'LIQ QAYTA YOZILGAN (SODDA VA ISHONCHLI)
handlers/auksion_v2/handlers.py oxiriga qo'shing
"""

# ============================================================================
# ARIZA YUBORISH - SODDA VA ISHONCHLI
# ============================================================================

@router.callback_query(F.data.startswith("auk2:apply:"))
async def callback_apply_start(callback: CallbackQuery, state: FSMContext):
    """Ariza yuborishni boshlash"""
    parts = callback.data.split(":")
    lot_id = int(parts[2])
    main_cat = parts[3] if len(parts) > 3 else ""
    sub_cat = parts[4] if len(parts) > 4 else ""
    
    # Lotni storage'dan olish
    lot = storage.get_lot(lot_id)
    if not lot:
        await callback.answer("❌ Lot topilmadi", show_alert=True)
        return
    
    # State'ga saqlash
    await state.update_data(
        apply_lot_id=lot_id,
        apply_lot_name=lot.name,
        apply_lot_price=lot.current_price or lot.start_price,
        apply_main_cat=main_cat,
        apply_sub_cat=sub_cat
    )
    
    # FSM state'ni o'rnatish
    await state.set_state(AuksionStatesV2.application_name)
    
    # Xabar
    await callback.message.answer(
        "📝 <b>ARIZA YUBORISH</b>\n\n"
        f"📦 <b>Lot:</b> {lot.name[:100]}...\n"
        f"💰 <b>Narx:</b> {format_price(lot.current_price or lot.start_price)}\n\n"
        "👤 <b>1/2:</b> Iltimos, <b>ism va familiyangizni</b> kiriting:\n\n"
        "<i>Misol: Abbos Aliyev</i>",
        parse_mode="HTML"
    )
    await callback.answer()


@router.message(AuksionStatesV2.application_name)
async def process_application_name(message: Message, state: FSMContext):
    """Ismni qabul qilish"""
    name = message.text.strip()
    
    # Tekshirish
    if len(name) < 3:
        await message.answer(
            "❌ Ism juda qisqa!\n\n"
            "Iltimos, to'liq ism va familiyangizni kiriting.\n"
            "Misol: Abbos Aliyev"
        )
        return
    
    # Saqlash
    await state.update_data(apply_name=name)
    await state.set_state(AuksionStatesV2.application_phone)
    
    # Telefon so'rash - CONTACT BUTTON
    from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
    
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📱 Telefon raqamni yuborish", request_contact=True)],
            [KeyboardButton(text="✍️ Qo'lda yozish")]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )
    
    await message.answer(
        "📝 <b>ARIZA YUBORISH</b>\n\n"
        "📞 <b>2/2:</b> Telefon raqamingizni yuboring:\n\n"
        "• <b>Tugmani bosib</b> yuborish (tavsiya)\n"
        "• Yoki qo'lda yozish: +998901234567",
        reply_markup=keyboard,
        parse_mode="HTML"
    )


@router.message(AuksionStatesV2.application_phone, F.contact)
async def process_application_phone_contact(message: Message, state: FSMContext):
    """Telefon (contact orqali)"""
    phone = message.contact.phone_number
    
    # + qo'shish (agar yo'q bo'lsa)
    if not phone.startswith('+'):
        phone = '+' + phone
    
    # Ma'lumotlarni olish
    data = await state.get_data()
    lot_id = data.get("apply_lot_id")
    lot_name = data.get("apply_lot_name", "")
    lot_price = data.get("apply_lot_price", 0)
    name = data.get("apply_name", "")
    
    # Admin'ga yuborish
    await send_to_admin(
        bot=message.bot,
        user_id=message.from_user.id,
        username=message.from_user.username,
        name=name,
        phone=phone,
        lot_id=lot_id,
        lot_name=lot_name,
        lot_price=lot_price
    )
    
    # Foydalanuvchiga tasdiqlash
    from aiogram.types import ReplyKeyboardRemove
    
    await message.answer(
        "✅ <b>Arizangiz muvaffaqiyatli yuborildi!</b>\n\n"
        "Tez orada admin siz bilan bog'lanadi.\n\n"
        f"📦 <b>Lot:</b> {lot_name[:100]}...\n"
        f"💰 <b>Narx:</b> {format_price(lot_price)}\n"
        f"👤 <b>Ism:</b> {name}\n"
        f"📞 <b>Telefon:</b> {phone}\n\n"
        "Rahmat! 🙏",
        reply_markup=ReplyKeyboardRemove(),
        parse_mode="HTML"
    )
    
    # State tozalash
    await state.clear()


@router.message(AuksionStatesV2.application_phone, F.text == "✍️ Qo'lda yozish")
async def process_manual_phone_request(message: Message):
    """Qo'lda yozish tugmasi"""
    from aiogram.types import ReplyKeyboardRemove
    
    await message.answer(
        "📞 Telefon raqamingizni qo'lda yozing:\n\n"
        "Format: +998901234567",
        reply_markup=ReplyKeyboardRemove()
    )


@router.message(AuksionStatesV2.application_phone)
async def process_application_phone_text(message: Message, state: FSMContext):
    """Telefon (qo'lda yozilgan)"""
    phone = message.text.strip()
    
    # Tekshirish
    if not (phone.startswith('+998') or phone.startswith('998')):
        await message.answer(
            "❌ Telefon raqam noto'g'ri!\n\n"
            "Format: +998901234567\n"
            "Qaytadan kiriting:"
        )
        return
    
    # + qo'shish
    if not phone.startswith('+'):
        phone = '+' + phone
    
    # Ma'lumotlarni olish
    data = await state.get_data()
    lot_id = data.get("apply_lot_id")
    lot_name = data.get("apply_lot_name", "")
    lot_price = data.get("apply_lot_price", 0)
    name = data.get("apply_name", "")
    
    # Admin'ga yuborish
    await send_to_admin(
        bot=message.bot,
        user_id=message.from_user.id,
        username=message.from_user.username,
        name=name,
        phone=phone,
        lot_id=lot_id,
        lot_name=lot_name,
        lot_price=lot_price
    )
    
    # Foydalanuvchiga tasdiqlash
    from aiogram.types import ReplyKeyboardRemove
    
    await message.answer(
        "✅ <b>Arizangiz muvaffaqiyatli yuborildi!</b>\n\n"
        "Tez orada admin siz bilan bog'lanadi.\n\n"
        f"📦 <b>Lot:</b> {lot_name[:100]}...\n"
        f"💰 <b>Narx:</b> {format_price(lot_price)}\n"
        f"👤 <b>Ism:</b> {name}\n"
        f"📞 <b>Telefon:</b> {phone}\n\n"
        "Rahmat! 🙏",
        reply_markup=ReplyKeyboardRemove(),
        parse_mode="HTML"
    )
    
    # State tozalash
    await state.clear()


async def send_to_admin(bot, user_id, username, name, phone, lot_id, lot_name, lot_price):
    """Admin'ga xabar yuborish"""
    import os
    from datetime import datetime
    
    ADMIN_CHAT_ID = os.getenv("ADMIN_CHAT_ID")
    
    if not ADMIN_CHAT_ID:
        logger.error("ADMIN_CHAT_ID topilmadi!")
        return
    
    # Admin uchun xabar
    admin_text = (
        "🆕 <b>YANGI ARIZA!</b>\n\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        "👤 <b>FOYDALANUVCHI:</b>\n"
        f"├─ <b>ID:</b> <code>{user_id}</code>\n"
        f"├─ <b>Username:</b> @{username or 'yo\'q'}\n"
        f"├─ <b>Ism:</b> {name}\n"
        f"└─ <b>Telefon:</b> <code>{phone}</code>\n\n"
        "📦 <b>LOT MA'LUMOTLARI:</b>\n"
        f"├─ <b>ID:</b> <code>{lot_id}</code>\n"
        f"├─ <b>Nomi:</b> {lot_name[:150]}...\n"
        f"├─ <b>Narx:</b> {format_price(lot_price)}\n"
        f"└─ <b>Link:</b> https://e-auksion.uz/lot/{lot_id}\n\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        f"📅 <b>Sana:</b> {datetime.now().strftime('%d.%m.%Y %H:%M')}\n\n"
        "💬 <i>Admin, iltimos mijoz bilan bog'laning!</i>"
    )
    
    try:
        await bot.send_message(
            chat_id=ADMIN_CHAT_ID,
            text=admin_text,
            parse_mode="HTML"
        )
        logger.info(f"✅ Admin'ga ariza yuborildi: Lot #{lot_id}, User {user_id}")
    except Exception as e:
        logger.error(f"❌ Admin'ga yuborishda xato: {e}")
        logger.error(f"ADMIN_CHAT_ID: {ADMIN_CHAT_ID}")