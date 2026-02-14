"""
Auksion V2 - Asosiy Handlers
Hierarchik kategoriyalar bilan
"""
import logging
import os
from datetime import datetime
from typing import Optional

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InputMediaPhoto
from aiogram.fsm.context import FSMContext
from aiogram.filters import Command

from .categories import MAIN_CATEGORIES, SUB_CATEGORIES, CATEGORY_FILTERS, get_breadcrumb
from .config import (
    ITEMS_PER_PAGE,
    MSG_NO_LOTS,
    MSG_LOT_NOT_FOUND,
    MSG_ERROR,
    MSG_APPLICATION_SENT,
    APPLICATION_TEMPLATE,
)
from .models import Lot, UserFavorite, storage
from .api import api_client
from .utils import (
    format_lot_detail,
    format_price,
    paginate_list,
)
from .keyboards import (
    get_auksion_main_keyboard,
    get_subcategory_keyboard,
    get_lots_list_keyboard,
    get_lot_detail_keyboard,
    get_image_navigation_keyboard,
    get_application_confirm_keyboard,
    get_favorites_keyboard,
    get_search_keyboard,
    get_back_to_main_keyboard,
)
from .states import AuksionStatesV2

logger = logging.getLogger(__name__)
router = Router(name="auksion_v2")

# Admin ID'lar (.env dan)
ADMIN_IDS = os.getenv("ADMIN_USER_IDS", "").split(",")
ADMIN_IDS = [int(id.strip()) for id in ADMIN_IDS if id.strip().isdigit()]


# ============================================================================
# ASOSIY MENYU
# ============================================================================

@router.message(Command("auksion"))
async def cmd_auksion(message: Message):
    """
    /auksion komandasi - Auksion menyusini ochish
    """
    await show_auksion_main_menu(message)


@router.callback_query(F.data == "auk2:menu")
async def callback_auksion_menu(callback: CallbackQuery):
    """Auksion asosiy menyusiga qaytish"""
    await callback.message.edit_text(
        "🏛 <b>E-AUKSION || Lotlar - Yangi lotlar</b>\n\n"
        "Kategoriyani tanlang:",
        reply_markup=get_auksion_main_keyboard()
    )
    await callback.answer()


async def show_auksion_main_menu(message: Message):
    """Auksion asosiy menyusini ko'rsatish"""
    await message.answer(
        "🏛 <b>E-AUKSION || Lotlar - Yangi lotlar</b>\n\n"
        "Kategoriyani tanlang:",
        reply_markup=get_auksion_main_keyboard()
    )


# ============================================================================
# KATEGORIYALAR (1-DARAJA)
# ============================================================================

@router.callback_query(F.data.startswith("auk2:cat:"))
async def callback_main_category(callback: CallbackQuery):
    """
    Asosiy kategoriya tanlandi
    Sub-kategoriyalarni ko'rsatish
    """
    main_cat = callback.data.split(":")[-1]
    
    if main_cat not in MAIN_CATEGORIES:
        await callback.answer("❌ Kategoriya topilmadi", show_alert=True)
        return
    
    cat_name = MAIN_CATEGORIES[main_cat]
    breadcrumb = get_breadcrumb(main_cat)
    
    text = f"📂 <b>{breadcrumb}</b>\n\n"
    text += "Bo'limni tanlang:"
    
    keyboard = get_subcategory_keyboard(main_cat)
    
    await callback.message.edit_text(text, reply_markup=keyboard)
    await callback.answer()


# ============================================================================
# SUB-KATEGORIYALAR (2-DARAJA)
# ============================================================================
@router.callback_query(F.data.startswith("auk2:sub:"))
async def callback_show_subcategory(callback: CallbackQuery):
    """Sub-kategoriya -> VILOYAT FILTRIGA YO'NALTIRISH"""
    parts = callback.data.split(":")
    main_cat = parts[2]
    sub_cat = parts[3]
    
    # region_filter.py ga yo'naltirish
    from .region_filter import get_region_filter_keyboard
    from .categories import get_breadcrumb
    
    breadcrumb = get_breadcrumb(main_cat, sub_cat)
    
    text = (
        f"📂 <b>{breadcrumb}</b>\n\n"
        "📍 <b>Viloyatni tanlang:</b>\n\n"
        "<i>Sizning viloyatingizdagi lotlarni ko'rsatamiz</i>"
    )
    
    keyboard = get_region_filter_keyboard(main_cat, sub_cat)
    
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()

# ============================================================================
# SAHIFALASH
# ============================================================================

@router.callback_query(F.data.startswith("auk2:page:"))
async def callback_lots_page(callback: CallbackQuery):
    """Lotlar sahifasini almashtirish"""
    parts = callback.data.split(":")
    main_cat = parts[2]
    sub_cat = parts[3]
    page = int(parts[4])
    
    # Filter data
    filter_data = CATEGORY_FILTERS.get(sub_cat)
    if not filter_data:
        await callback.answer("❌ Xato", show_alert=True)
        return
    
    # YANGI: To'g'ridan-to'g'ri API'dan kerakli sahifani olish
    lots = await api_client.get_lots_by_category(
        groups_id=filter_data["groups_id"],
        categories_id=filter_data["categories_id"],
        page=page  # To'g'ri sahifa raqami
    )
    
    if not lots:
        await callback.answer("Bu sahifada lotlar yo'q", show_alert=True)
        return
    
    # Matn
    breadcrumb = get_breadcrumb(main_cat, sub_cat)
    text = f"📂 <b>{breadcrumb}</b>\n\n"
    text += f"📄 Sahifa: {page}\n"
    text += f"📦 Bu sahifada: {len(lots)} ta lot\n\n"
    text += "Lotni tanlang:"
    
    # Keyboard - lotlarni to'g'ridan-to'g'ri ko'rsatish
    keyboard = get_lots_list_keyboard(lots, main_cat, sub_cat, page, 999)
    
    await callback.message.edit_text(text, reply_markup=keyboard)
    await callback.answer()
    
    # Matn
    breadcrumb = get_breadcrumb(main_cat, sub_cat)
    text = f"📂 <b>{breadcrumb}</b>\n\n"
    text += f"📦 Jami: {len(lots)} ta lot\n\n"
    text += "Lotni tanlang:"
    
    # Keyboard
    keyboard = get_lots_list_keyboard(page_lots, main_cat, sub_cat, page, total_pages)
    
    await callback.message.edit_text(text, reply_markup=keyboard)
    await callback.answer()


# ============================================================================
# LOT BATAFSIL MA'LUMOTLARI
# ============================================================================

@router.callback_query(F.data.startswith("auk2:view:"))
async def callback_view_lot(callback: CallbackQuery):
    """Lotni batafsil ko'rish"""
    parts = callback.data.split(":")
    lot_id = int(parts[2])
    main_cat = parts[3] if len(parts) > 3 else "kochmas_mulk"
    sub_cat = parts[4] if len(parts) > 4 else "kop_qavatli"
    
    # Yuklanish xabari - rasm/matn muammosini hal qilish
    loading_msg = None
    try:
        loading_msg = await callback.message.edit_text("⏳ Ma'lumot yuklanmoqda...")
    except:
        # Agar rasm bo'lsa yoki edit qilib bo'lmasa
        try:
            await callback.message.delete()
        except:
            pass
        loading_msg = await callback.message.answer("⏳ Ma'lumot yuklanmoqda...")
    
    try:
        # API dan batafsil ma'lumot
        lot = await api_client.get_lot_detail(lot_id)
        
        if not lot:
            await loading_msg.edit_text(
                MSG_LOT_NOT_FOUND,
                reply_markup=get_back_to_main_keyboard()
            )
            await callback.answer()
            return
        
        # Breadcrumb
        breadcrumb = get_breadcrumb(main_cat, sub_cat)
        
        # Matn
        text = f"📂 <b>{breadcrumb}</b>\n\n"
        text += format_lot_detail(lot)
        
        # Keyboard
        keyboard = get_lot_detail_keyboard(lot, callback.from_user.id, main_cat, sub_cat)
        
        await loading_msg.edit_text(text, reply_markup=keyboard)
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Lot {lot_id} ma'lumotlarini olishda xato: {e}")
        await callback.message.edit_text(
            MSG_ERROR,
            reply_markup=get_back_to_main_keyboard()
        )
        await callback.answer()


# ============================================================================
# RASMLAR GALEREYASI
# ============================================================================

@router.callback_query(F.data.startswith("auk2:images:"))
async def callback_view_images(callback: CallbackQuery):
    """Lot rasmlarini ko'rish"""
    parts = callback.data.split(":")
    lot_id = int(parts[2])
    index = int(parts[3])
    main_cat = parts[4] if len(parts) > 4 else "kochmas_mulk"
    sub_cat = parts[5] if len(parts) > 5 else "kop_qavatli"
    
    lot = storage.get_lot(lot_id)
    
    if not lot or not lot.images:
        await callback.answer("❌ Rasmlar topilmadi", show_alert=True)
        return
    
    if index >= len(lot.images):
        await callback.answer("❌ Rasm topilmadi", show_alert=True)
        return
    
    # Rasmni ko'rsatish
    await show_lot_image(callback.message, lot, index, main_cat, sub_cat, edit=True)
    await callback.answer()


async def show_lot_image(
    message: Message,
    lot: Lot,
    index: int,
    main_cat: str,
    sub_cat: str,
    edit: bool = False
):
    """
    Lotning rasmini ko'rsatish
    
    Args:
        message: Xabar obyekti
        lot: Lot
        index: Rasm indexi
        main_cat: Asosiy kategoriya
        sub_cat: Sub-kategoriya
        edit: Xabarni tahrirlash (True) yoki yangi yuborish (False)
    """
    if not lot.images or index >= len(lot.images):
        return
    
    image = lot.images[index]
    image_url = image.get_url()
    
    breadcrumb = get_breadcrumb(main_cat, sub_cat)
    
    caption = (
        f"📂 <b>{breadcrumb}</b>\n\n"
        f"📸 <b>Rasm {index + 1}/{len(lot.images)}</b>\n\n"
        f"📦 {lot.name}\n"
        f"💰 {format_price(lot.current_price)}"
    )
    
    keyboard = get_image_navigation_keyboard(lot.id, index, len(lot.images), main_cat, sub_cat)
    
    try:
        if edit and message.photo:
            # Rasmni tahrirlash
            await message.edit_media(
                media=InputMediaPhoto(media=image_url, caption=caption),
                reply_markup=keyboard
            )
        else:
            # Yangi rasm yuborish
            if edit:
                await message.delete()
            
            await message.answer_photo(
                photo=image_url,
                caption=caption,
                reply_markup=keyboard
            )
    except Exception as e:
        logger.error(f"Rasmni yuborishda xato: {e}")
        await message.answer(
            f"❌ Rasmni yuklashda xatolik.\n\n{caption}",
            reply_markup=keyboard
        )


# ============================================================================
# SEVIMLILAR
# ============================================================================

@router.callback_query(F.data.startswith("auk2:fav:"))
async def callback_add_favorite(callback: CallbackQuery):
    """Sevimliga qo'shish"""
    parts = callback.data.split(":")
    lot_id = int(parts[2])
    main_cat = parts[3]
    sub_cat = parts[4]
    
    lot = storage.get_lot(lot_id)
    if not lot:
        await callback.answer("❌ Lot topilmadi", show_alert=True)
        return
    
    # Sevimliga qo'shish
    favorite = UserFavorite(
        user_id=callback.from_user.id,
        lot_id=lot_id,
        added_at=datetime.now()
    )
    storage.add_favorite(favorite)
    
    await callback.answer("⭐ Sevimliga qo'shildi!", show_alert=True)
    
    # Keyboard yangilash
    breadcrumb = get_breadcrumb(main_cat, sub_cat)
    text = f"📂 <b>{breadcrumb}</b>\n\n"
    text += format_lot_detail(lot)
    
    keyboard = get_lot_detail_keyboard(lot, callback.from_user.id, main_cat, sub_cat)
    
    await callback.message.edit_text(text, reply_markup=keyboard)


@router.callback_query(F.data.startswith("auk2:unfav:"))
async def callback_remove_favorite(callback: CallbackQuery):
    """Sevimlilardan o'chirish"""
    parts = callback.data.split(":")
    lot_id = int(parts[2])
    main_cat = parts[3]
    sub_cat = parts[4]
    
    storage.remove_favorite(callback.from_user.id, lot_id)
    
    await callback.answer("🗑 Sevimlilardan o'chirildi", show_alert=True)
    
    # Keyboard yangilash
    lot = storage.get_lot(lot_id)
    if lot:
        breadcrumb = get_breadcrumb(main_cat, sub_cat)
        text = f"📂 <b>{breadcrumb}</b>\n\n"
        text += format_lot_detail(lot)
        
        keyboard = get_lot_detail_keyboard(lot, callback.from_user.id, main_cat, sub_cat)
        await callback.message.edit_text(text, reply_markup=keyboard)


@router.callback_query(F.data == "auk2:favorites")
async def callback_show_favorites(callback: CallbackQuery):
    """Sevimlilarni ko'rsatish"""
    user_id = callback.from_user.id
    favorites = storage.get_user_favorites(user_id)
    
    if not favorites:
        await callback.message.edit_text(
            "⭐ <b>SEVIMLILAR</b>\n\n"
            "Sizda hali sevimli lotlar yo'q.\n\n"
            "Lotlarni ko'rib, sevimliga qo'shing!",
            reply_markup=get_back_to_main_keyboard()
        )
        await callback.answer()
        return
    
    # Sevimli lotlarni olish
    lots = []
    for fav in favorites:
        lot = storage.get_lot(fav.lot_id)
        if lot:
            lots.append(lot)
    
    if not lots:
        await callback.message.edit_text(
            "⭐ <b>SEVIMLILAR</b>\n\n"
            "Sevimli lotlar topilmadi.",
            reply_markup=get_back_to_main_keyboard()
        )
        await callback.answer()
        return
    
    # Sahifalash
    page_lots, total_pages, _, _ = paginate_list(lots, 1, ITEMS_PER_PAGE)
    
    text = f"⭐ <b>SEVIMLILAR</b>\n\n"
    text += f"📦 Jami: {len(lots)} ta lot\n\n"
    text += "Lotni tanlang:"
    
    keyboard = get_favorites_keyboard(page_lots, 1, total_pages)
    
    await callback.message.edit_text(text, reply_markup=keyboard)
    await callback.answer()


@router.callback_query(F.data.startswith("auk2:view_fav:"))
async def callback_view_favorite_lot(callback: CallbackQuery):
    """Sevimli lotni ko'rish"""
    lot_id = int(callback.data.split(":")[-1])
    
    lot = storage.get_lot(lot_id)
    
    if not lot:
        # API dan qayta olishga harakat
        lot = await api_client.get_lot_detail(lot_id)
    
    if not lot:
        await callback.answer("❌ Lot topilmadi", show_alert=True)
        return
    
    # Lotni ko'rsatish (default kategoriya bilan)
    text = "⭐ <b>SEVIMLILAR</b>\n\n"
    text += format_lot_detail(lot)
    
    keyboard = get_lot_detail_keyboard(lot, callback.from_user.id, "kochmas_mulk", "kop_qavatli")
    
    await callback.message.edit_text(text, reply_markup=keyboard)
    await callback.answer()

# ============================================================================
# ARIZA YUBORISH - TO'LIQ TIZIM
# ============================================================================

@router.callback_query(F.data.startswith("auk2:apply:"))
async def callback_apply_start(callback: CallbackQuery, state: FSMContext):
    """Ariza yuborishni boshlash - ISM VA FAMILIYA"""
    parts = callback.data.split(":")
    lot_id = int(parts[2])
    main_cat = parts[3]
    sub_cat = parts[4]
    
    lot = storage.get_lot(lot_id)
    if not lot:
        await callback.answer("❌ Lot topilmadi", show_alert=True)
        return
    
    # State'ga saqlash
    await state.update_data(
        apply_lot_id=lot_id,
        apply_main_cat=main_cat,
        apply_sub_cat=sub_cat
    )
    await state.set_state(AuksionStatesV2.application_name)
    
    await callback.message.answer(
        "📝 <b>ARIZA YUBORISH - 1/3</b>\n\n"
        f"📦 Lot: {lot.name}\n"
        f"💰 Narx: {format_price(lot.current_price or lot.start_price)}\n\n"
        "👤 Iltimos, <b>ism va familiyangizni</b> kiriting:\n\n"
        "Misol: Abbos Aliyev"
    )
    await callback.answer()


@router.message(AuksionStatesV2.application_name)
async def process_application_name(message: Message, state: FSMContext):
    """Ism va familiyani qayta ishlash"""
    name = message.text.strip()
    
    if len(name) < 3:
        await message.answer("❌ Ism juda qisqa. Iltimos, to'liq ism va familiyangizni kiriting.")
        return
    
    # Saqlash
    await state.update_data(apply_name=name)
    await state.set_state(AuksionStatesV2.application_phone)
    
    # Telefon raqam so'rash
    from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
    
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📱 Telefon raqamni yuborish", request_contact=True)]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )
    
    await message.answer(
        "📝 <b>ARIZA YUBORISH - 2/3</b>\n\n"
        "📞 Telefon raqamingizni yuboring:\n\n"
        "• Tugmani bosib yuborish\n"
        "• Yoki qo'lda yozish: +998901234567",
        reply_markup=keyboard
    )


@router.message(AuksionStatesV2.application_phone, F.contact)
async def process_application_phone_contact(message: Message, state: FSMContext):
    """Telefon raqam (contact orqali)"""
    phone = message.contact.phone_number
    
    # Saqlash
    await state.update_data(apply_phone=phone)
    await state.set_state(AuksionStatesV2.application_comment)
    
    # Izoh so'rash
    from aiogram.types import ReplyKeyboardRemove
    
    await message.answer(
        "📝 <b>ARIZA YUBORISH - 3/3</b>\n\n"
        "💬 Qo'shimcha izoh yozing yoki \"yo'q\" deb yuboring:",
        reply_markup=ReplyKeyboardRemove()
    )


@router.message(AuksionStatesV2.application_phone)
async def process_application_phone_text(message: Message, state: FSMContext):
    """Telefon raqam (qo'lda yozilgan)"""
    phone = message.text.strip()
    
    # Telefon raqamni tekshirish
    if not phone.startswith('+') and not phone.startswith('998'):
        await message.answer("❌ Telefon raqam noto'g'ri. +998 bilan boshlang. Misol: +998901234567")
        return
    
    # Saqlash
    await state.update_data(apply_phone=phone)
    await state.set_state(AuksionStatesV2.application_comment)
    
    # Izoh so'rash
    from aiogram.types import ReplyKeyboardRemove
    
    await message.answer(
        "📝 <b>ARIZA YUBORISH - 3/3</b>\n\n"
        "💬 Qo'shimcha izoh yozing yoki \"yo'q\" deb yuboring:",
        reply_markup=ReplyKeyboardRemove()
    )


@router.message(AuksionStatesV2.application_comment)
async def process_application_comment(message: Message, state: FSMContext):
    """Izohni qayta ishlash va tasdiqlash"""
    data = await state.get_data()
    lot_id = data.get("apply_lot_id")
    name = data.get("apply_name")
    phone = data.get("apply_phone")
    
    lot = storage.get_lot(lot_id)
    if not lot:
        await message.answer("❌ Xatolik. Qaytadan boshlang.")
        await state.clear()
        return
    
    # Izoh
    comment = message.text.strip()
    if comment.lower() == "yo'q":
        comment = "—"
    
    await state.update_data(apply_comment=comment)
    
    # Tasdiqlash
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Ha, yuborish", callback_data=f"auk2:apply_send:{lot_id}"),
            InlineKeyboardButton(text="❌ Bekor qilish", callback_data="auk2:apply_cancel")
        ]
    ])
    
    text = (
        "📋 <b>ARIZANI TASDIQLASH</b>\n\n"
        f"📦 <b>Lot:</b> {lot.name}\n"
        f"💰 <b>Narx:</b> {format_price(lot.current_price or lot.start_price)}\n\n"
        f"👤 <b>Ism:</b> {name}\n"
        f"📞 <b>Telefon:</b> {phone}\n"
        f"💬 <b>Izoh:</b> {comment}\n\n"
        "Arizani yuborasizmi?"
    )
    
    await message.answer(text, reply_markup=keyboard)


@router.callback_query(F.data.startswith("auk2:apply_send:"))
async def callback_send_application(callback: CallbackQuery, state: FSMContext):
    """Arizani admin'ga yuborish"""
    import os
    from datetime import datetime
    
    lot_id = int(callback.data.split(":")[-1])
    
    data = await state.get_data()
    name = data.get("apply_name")
    phone = data.get("apply_phone")
    comment = data.get("apply_comment", "—")
    
    lot = storage.get_lot(lot_id)
    if not lot:
        await callback.answer("❌ Xatolik", show_alert=True)
        await state.clear()
        return
    
    # Foydalanuvchi ma'lumotlari
    user = callback.from_user
    
    # Admin'ga xabar
    ADMIN_CHAT_ID = os.getenv("ADMIN_CHAT_ID")
    
    if ADMIN_CHAT_ID:
        admin_text = (
            "🆕 <b>YANGI ARIZA!</b>\n\n"
            "👤 <b>Foydalanuvchi:</b>\n"
            f"├─ ID: {user.id}\n"
            f"├─ Username: @{user.username or '—'}\n"
            f"├─ Ism: {name}\n"
            f"└─ Telefon: {phone}\n\n"
            f"📦 <b>Lot:</b>\n"
            f"├─ ID: {lot.id}\n"
            f"├─ Nomi: {lot.name}\n"
            f"├─ Narx: {format_price(lot.current_price or lot.start_price)}\n"
            f"└─ Link: https://e-auksion.uz/lot/{lot.id}\n\n"
            f"💬 <b>Izoh:</b> {comment}\n\n"
            f"📅 {datetime.now().strftime('%d.%m.%Y %H:%M')}"
        )
        
        try:
            await callback.bot.send_message(
                chat_id=ADMIN_CHAT_ID,
                text=admin_text
            )
            
            # Foydalanuvchiga tasdiqlash
            await callback.message.edit_text(
                "✅ <b>Arizangiz muvaffaqiyatly yuborildi!</b>\n\n"
                "Tez orada admin siz bilan bog'lanadi.\n\n"
                f"📦 Lot: {lot.name}\n"
                f"💰 Narx: {format_price(lot.current_price or lot.start_price)}\n\n"
                "Rahmat! 🙏"
            )
            
            await callback.answer("✅ Yuborildi!", show_alert=True)
            
        except Exception as e:
            logger.error(f"Admin'ga xabar yuborishda xato: {e}")
            await callback.answer("❌ Xatolik yuz berdi. Iltimos, qayta urinib ko'ring.", show_alert=True)
    else:
        await callback.answer("❌ Admin ID topilmadi. .env faylini tekshiring.", show_alert=True)
    
    await state.clear()


@router.callback_query(F.data == "auk2:apply_cancel")
async def callback_cancel_application(callback: CallbackQuery, state: FSMContext):
    """Arizani bekor qilish"""
    await state.clear()
    await callback.message.edit_text("❌ Ariza bekor qilindi.")
    await callback.answer()