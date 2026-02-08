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
async def callback_subcategory(callback: CallbackQuery):
    """
    Sub-kategoriya tanlandi
    Lotlarni ko'rsatish
    """
    parts = callback.data.split(":")
    main_cat = parts[2]
    sub_cat = parts[3]
    
    if main_cat not in SUB_CATEGORIES:
        await callback.answer("❌ Kategoriya topilmadi", show_alert=True)
        return
    
    if sub_cat not in SUB_CATEGORIES[main_cat]:
        await callback.answer("❌ Bo'lim topilmadi", show_alert=True)
        return
    
    await callback.message.edit_text("⏳ Lotlar yuklanmoqda...")
    
    try:
        # API dan lotlarni olish
        filter_data = CATEGORY_FILTERS.get(sub_cat)
        
        if not filter_data:
            logger.warning(f"Filter topilmadi: {sub_cat}")
            await callback.message.edit_text(
                MSG_NO_LOTS,
                reply_markup=get_subcategory_keyboard(main_cat)
            )
            await callback.answer()
            return
        
        # REAL API format bilan so'rov
        lots = await api_client.get_lots_by_category(
            groups_id=filter_data["groups_id"],
            categories_id=filter_data["categories_id"],
            page=1
        )
        
        if not lots:
            breadcrumb = get_breadcrumb(main_cat, sub_cat)
            await callback.message.edit_text(
                f"📂 <b>{breadcrumb}</b>\n\n{MSG_NO_LOTS}",
                reply_markup=get_subcategory_keyboard(main_cat)
            )
            await callback.answer()
            return
        
        # Sahifalash
        page_lots, total_pages, _, _ = paginate_list(lots, 1, ITEMS_PER_PAGE)
        
        # Matn
        breadcrumb = get_breadcrumb(main_cat, sub_cat)
        text = f"📂 <b>{breadcrumb}</b>\n\n"
        text += f"📦 Jami: {len(lots)} ta lot\n\n"
        text += "Lotni tanlang:"
        
        # Keyboard
        keyboard = get_lots_list_keyboard(page_lots, main_cat, sub_cat, 1, total_pages)
        
        await callback.message.edit_text(text, reply_markup=keyboard)
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Sub-kategoriya {sub_cat} uchun xato: {e}")
        await callback.message.edit_text(
            MSG_ERROR,
            reply_markup=get_back_to_main_keyboard()
        )
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
    
    # Lotlarni olish
    lots = await api_client.get_lots_by_category(
        category_id=filter_data.get("category_id"),
        sub_category_id=filter_data.get("sub_category_id"),
        page=page
    )
    
    if not lots:
        await callback.answer("Bu sahifada lotlar yo'q", show_alert=True)
        return
    
    # Sahifalash
    page_lots, total_pages, _, _ = paginate_list(lots, page, ITEMS_PER_PAGE)
    
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
    
    await callback.message.edit_text("⏳ Ma'lumot yuklanmoqda...")
    
    try:
        # API dan batafsil ma'lumot
        lot = await api_client.get_lot_detail(lot_id)
        
        if not lot:
            await callback.message.edit_text(
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
        
        await callback.message.edit_text(text, reply_markup=keyboard)
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
# ARIZA YUBORISH
# ============================================================================

@router.callback_query(F.data.startswith("auk2:apply:"))
async def callback_apply_start(callback: CallbackQuery, state: FSMContext):
    """Ariza yuborishni boshlash"""
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
    await state.set_state(AuksionStatesV2.application_comment)
    
    await callback.message.edit_text(
        "📝 <b>ARIZA YUBORISH</b>\n\n"
        f"📦 Lot: {lot.name}\n"
        f"💰 Narx: {format_price(lot.current_price)}\n\n"
        "Iltimos, qo'shimcha izoh yozing yoki \"yo'q\" deb yuboring:",
        reply_markup=get_back_to_main_keyboard()
    )
    await callback.answer()


@router.message(AuksionStatesV2.application_comment)
async def process_application_comment(message: Message, state: FSMContext):
    """Ariza izohini qayta ishlash"""
    data = await state.get_data()
    lot_id = data.get("apply_lot_id")
    main_cat = data.get("apply_main_cat")
    sub_cat = data.get("apply_sub_cat")
    
    if not lot_id:
        await message.answer("❌ Xatolik yuz berdi. Qaytadan urinib ko'ring.")
        await state.clear()
        return
    
    lot = storage.get_lot(lot_id)
    if not lot:
        await message.answer("❌ Lot topilmadi.")
        await state.clear()
        return
    
    # Izohni saqlash
    comment = message.text.strip()
    if comment.lower() == "yo'q":
        comment = "—"
    
    await state.update_data(apply_comment=comment)
    
    # Tasdiqlash
    text = (
        "✅ <b>ARIZANI TASDIQLASH</b>\n\n"
        f"📦 Lot: {lot.name}\n"
        f"💰 Narx: {format_price(lot.current_price)}\n"
        f"💬 Izoh: {comment}\n\n"
        "Arizani yuborishni tasdiqlaysizmi?"
    )
    
    keyboard = get_application_confirm_keyboard(lot_id, main_cat, sub_cat)
    
    await message.answer(text, reply_markup=keyboard)


@router.callback_query(F.data.startswith("auk2:apply_confirm:"))
async def callback_confirm_application(callback: CallbackQuery, state: FSMContext):
    """Arizani tasdiqlash va yuborish"""
    parts = callback.data.split(":")
    lot_id = int(parts[2])
    main_cat = parts[3]
    sub_cat = parts[4]
    
    data = await state.get_data()
    comment = data.get("apply_comment", "—")
    
    lot = storage.get_lot(lot_id)
    if not lot:
        await callback.answer("❌ Lot topilmadi", show_alert=True)
        await state.clear()
        return
    
    # Foydalanuvchi ma'lumotlari
    user = callback.from_user
    full_name = user.full_name
    username = user.username or "—"
    user_id = user.id
    
    # Admin'larga xabar yuborish
    if ADMIN_IDS:
        admin_text = APPLICATION_TEMPLATE.format(
            user_id=user_id,
            full_name=full_name,
            username=username,
            lot_id=lot.id,
            lot_name=lot.name,
            lot_price=format_price(lot.current_price),
            lot_link=f"https://e-auksion.uz/lot/{lot.id}",
            date=datetime.now().strftime("%d.%m.%Y %H:%M"),
            comment=comment
        )
        
        for admin_id in ADMIN_IDS:
            try:
                await callback.bot.send_message(
                    chat_id=admin_id,
                    text=admin_text
                )
            except Exception as e:
                logger.error(f"Adminga xabar yuborishda xato: {e}")
    
    # Foydalanuvchiga tasdiqlash
    success_text = MSG_APPLICATION_SENT.format(
        lot_name=lot.name,
        lot_price=format_price(lot.current_price)
    )
    
    await callback.message.edit_text(
        success_text,
        reply_markup=get_back_to_main_keyboard()
    )
    
    await state.clear()
    await callback.answer("✅ Ariza yuborildi!", show_alert=True)


# ============================================================================
# QIDIRUV
# ============================================================================

@router.callback_query(F.data == "auk2:search")
async def callback_search_start(callback: CallbackQuery, state: FSMContext):
    """Qidiruvni boshlash"""
    await state.set_state(AuksionStatesV2.searching)
    
    await callback.message.edit_text(
        "🔍 <b>QIDIRUV</b>\n\n"
        "Qidiruv so'zini kiriting\n"
        "(masalan: \"kvartira\", \"Toshkent\", \"yer uchastkasi\"):",
        reply_markup=get_search_keyboard()
    )
    await callback.answer()


@router.message(AuksionStatesV2.searching)
async def process_search_query(message: Message, state: FSMContext):
    """Qidiruv so'zini qayta ishlash"""
    query = message.text.strip()
    
    if len(query) < 3:
        await message.answer("❌ Qidiruv so'zi juda qisqa. Kamida 3 ta harf kiriting.")
        return
    
    await state.clear()
    
    searching_msg = await message.answer("⏳ Qidirilmoqda...")
    
    try:
        # API orqali qidirish
        lots = await api_client.search_lots(query)
        
        if not lots:
            await searching_msg.edit_text(
                f"🔍 <b>QIDIRUV NATIJASI</b>\n\n"
                f"'{query}' bo'yicha hech narsa topilmadi.",
                reply_markup=get_back_to_main_keyboard()
            )
            return
        
        # Sahifalash
        page_lots, total_pages, _, _ = paginate_list(lots, 1, ITEMS_PER_PAGE)
        
        text = f"🔍 <b>QIDIRUV NATIJASI</b>\n\n"
        text += f"Qidiruv: '{query}'\n"
        text += f"📦 Topildi: {len(lots)} ta lot\n\n"
        text += "Lotni tanlang:"
        
        # Qidiruv natijasi uchun maxsus keyboard
        keyboard = get_favorites_keyboard(page_lots, 1, total_pages)
        
        await searching_msg.edit_text(text, reply_markup=keyboard)
        
    except Exception as e:
        logger.error(f"Qidirishda xato: {e}")
        await searching_msg.edit_text(
            MSG_ERROR,
            reply_markup=get_back_to_main_keyboard()
        )


# ============================================================================
# YORDAMCHI HANDLERLAR
# ============================================================================

@router.callback_query(F.data == "noop")
async def callback_noop(callback: CallbackQuery):
    """Hech narsa qilmaydigan callback"""
    await callback.answer()


# Bot to'xtatishda
async def on_shutdown():
    """Bot to'xtatilganda"""
    await api_client.close()
    logger.info("Auksion V2 API session yopildi")