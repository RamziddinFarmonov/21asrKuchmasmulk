"""
Auksion V2 - Asosiy Handlers
YANGILANGAN:
  - Lot batafsil ma'lumotlari qaytdi (narx, tavsif, xususiyatlar)
  - Rasm + caption, keyin to'liq matn
  - "Mening arizalarim" bo'limi
  - Narx kuzatish
"""
import logging
import os
from datetime import datetime

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InputMediaPhoto
from aiogram.fsm.context import FSMContext
from aiogram.filters import Command

from .categories import MAIN_CATEGORIES, SUB_CATEGORIES, CATEGORY_FILTERS, get_breadcrumb
from .config import ITEMS_PER_PAGE, MSG_LOT_NOT_FOUND, MSG_ERROR
from .models import Lot, UserFavorite, UserApplication, storage
from .api import api_client
from .utils import format_price, paginate_list, clean_text
from .keyboards import (
    get_auksion_main_keyboard,
    get_subcategory_keyboard,
    get_lots_list_keyboard,
    get_lot_detail_keyboard,
    get_image_navigation_keyboard,
    get_favorites_keyboard,
    get_back_to_main_keyboard,
    get_my_applications_keyboard,
)
from .states import AuksionStatesV2

logger = logging.getLogger(__name__)
router = Router(name="auksion_v2")

ADMIN_IDS = os.getenv("ADMIN_USER_IDS", "").split(",")
ADMIN_IDS = [int(i.strip()) for i in ADMIN_IDS if i.strip().isdigit()]


# ============================================================================
# ASOSIY MENYU
# ============================================================================

@router.message(Command("auksion"))
async def cmd_auksion(message: Message):
    await _show_main_menu(message)


@router.callback_query(F.data == "auk2:menu")
async def callback_auksion_menu(callback: CallbackQuery):
    await callback.message.edit_text(
        "🏛 <b>E-AUKSION || Lotlar - Yangi lotlar</b>\n\nKategoriyani tanlang:",
        reply_markup=get_auksion_main_keyboard(),
        parse_mode="HTML"
    )
    await callback.answer()


async def _show_main_menu(message: Message):
    await message.answer(
        "🏛 <b>E-AUKSION || Lotlar - Yangi lotlar</b>\n\nKategoriyani tanlang:",
        reply_markup=get_auksion_main_keyboard(),
        parse_mode="HTML"
    )

# Alias — handlers.common da shu nom bilan import qilinadi
show_auksion_main_menu = _show_main_menu


# ============================================================================
# KATEGORIYALAR
# ============================================================================

@router.callback_query(F.data.startswith("auk2:cat:"))
async def callback_main_category(callback: CallbackQuery):
    main_cat = callback.data.split(":")[-1]
    if main_cat not in MAIN_CATEGORIES:
        await callback.answer("Kategoriya topilmadi", show_alert=True)
        return
    breadcrumb = get_breadcrumb(main_cat)
    await callback.message.edit_text(
        f"📂 <b>{breadcrumb}</b>\n\nBo'limni tanlang:",
        reply_markup=get_subcategory_keyboard(main_cat),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data.startswith("auk2:sub:"))
async def callback_show_subcategory(callback: CallbackQuery):
    parts = callback.data.split(":")
    main_cat, sub_cat = parts[2], parts[3]
    from .region_filter import get_region_filter_keyboard
    breadcrumb = get_breadcrumb(main_cat, sub_cat)
    await callback.message.edit_text(
        f"📂 <b>{breadcrumb}</b>\n\n📍 <b>Viloyatni tanlang:</b>\n\n"
        "<i>Sizning viloyatingizdagi lotlarni ko'rsatamiz</i>",
        reply_markup=get_region_filter_keyboard(main_cat, sub_cat),
        parse_mode="HTML"
    )
    await callback.answer()


# ============================================================================
# SAHIFALASH
# ============================================================================

@router.callback_query(F.data.startswith("auk2:page:"))
async def callback_lots_page(callback: CallbackQuery):
    parts = callback.data.split(":")
    main_cat, sub_cat, page = parts[2], parts[3], int(parts[4])
    filter_data = CATEGORY_FILTERS.get(sub_cat)
    if not filter_data:
        await callback.answer("Xato", show_alert=True)
        return
    await callback.message.edit_text("⏳ Yuklanmoqda...")
    lots = await api_client.get_lots_by_category(
        groups_id=filter_data["groups_id"],
        categories_id=filter_data["categories_id"],
        page=page
    )
    if not lots:
        await callback.answer("Bu sahifada lotlar yo'q", show_alert=True)
        return
    breadcrumb = get_breadcrumb(main_cat, sub_cat)
    await callback.message.edit_text(
        f"📂 <b>{breadcrumb}</b>\n\n📄 Sahifa: {page} | 📦 {len(lots)} ta lot\n\nLotni tanlang:",
        reply_markup=get_lots_list_keyboard(lots, main_cat, sub_cat, page, 999),
        parse_mode="HTML"
    )
    await callback.answer()


# ============================================================================
# LOT BATAFSIL — RASM + TO'LIQ MA'LUMOT
# ============================================================================

@router.callback_query(F.data.startswith("auk2:view:"))
async def callback_view_lot(callback: CallbackQuery):
    parts = callback.data.split(":")
    lot_id = int(parts[2])
    main_cat = parts[3] if len(parts) > 3 else "kochmas_mulk"
    sub_cat  = parts[4] if len(parts) > 4 else "kop_qavatli"

    try:
        loading_msg = await callback.message.edit_text("⏳ Ma'lumot yuklanmoqda...")
    except Exception:
        try:
            await callback.message.delete()
        except Exception:
            pass
        loading_msg = await callback.message.answer("⏳ Ma'lumot yuklanmoqda...")

    try:
        lot = await api_client.get_lot_detail(lot_id)
        if not lot:
            await loading_msg.edit_text(MSG_LOT_NOT_FOUND, reply_markup=get_back_to_main_keyboard())
            await callback.answer()
            return

        breadcrumb = get_breadcrumb(main_cat, sub_cat)
        full_text  = f"📂 <b>{breadcrumb}</b>\n\n" + _build_full_detail(lot)
        keyboard   = get_lot_detail_keyboard(lot, callback.from_user.id, main_cat, sub_cat)

        if lot.images:
            caption = _build_short_caption(lot, breadcrumb)
            try:
                await loading_msg.delete()
            except Exception:
                pass
            # Rasm yuborish
            try:
                await callback.message.answer_photo(
                    photo=lot.images[0].get_url(),
                    caption=caption,
                    parse_mode="HTML"
                )
            except Exception as img_err:
                logger.warning(f"Rasm yuklanmadi: {img_err}")
            # Batafsil matn (keyboard shu yerda)
            await callback.message.answer(full_text, reply_markup=keyboard, parse_mode="HTML")
        else:
            await loading_msg.edit_text(full_text, reply_markup=keyboard, parse_mode="HTML")

        await callback.answer()

    except Exception as e:
        logger.error(f"Lot {lot_id} ko'rishda xato: {e}", exc_info=True)
        try:
            await loading_msg.edit_text(MSG_ERROR, reply_markup=get_back_to_main_keyboard())
        except Exception:
            pass
        await callback.answer()


def _build_short_caption(lot: Lot, breadcrumb: str) -> str:
    """Rasm uchun qisqa caption (max 1024 belgi)"""
    lines = [f"📂 <b>{breadcrumb}</b>\n"]
    name = lot.name[:100] + ("..." if len(lot.name) > 100 else "")
    lines.append(f"<b>{name}</b>")
    lines.append("")
    if lot.lot_number:
        lines.append(f"📦 Lot: <code>#{lot.lot_number}</code>")
    if lot.location:
        lines.append(f"📍 {lot.location[:80]}")
    price = lot.current_price or lot.start_price
    if price:
        lines.append(f"💰 Narx: <b>{format_price(price)}</b>")
    if lot.images and len(lot.images) > 1:
        lines.append(f"\n📸 Jami {len(lot.images)} ta rasm")
    caption = "\n".join(lines)
    return caption[:1020] + "..." if len(caption) > 1020 else caption


def _build_full_detail(lot: Lot) -> str:
    """Lotning TO'LIQ batafsil matni"""
    text = f"<b>{lot.name}</b>\n\n"

    if lot.lot_number:
        text += f"📦 <b>Lot raqami:</b> <code>#{lot.lot_number}</code>\n\n"

    if lot.location:
        text += f"📍 <b>Joylashuv:</b> {lot.location}\n\n"

    # Narx bloki
    text += "💰 <b>NARX MA'LUMOTLARI:</b>\n"
    if lot.start_price and lot.start_price > 0:
        text += f"├─ Boshlang'ich narx: {format_price(lot.start_price)}\n"
    price = lot.current_price or lot.start_price
    text += f"├─ Joriy narx: <b>{format_price(price)}</b>\n"
    if lot.min_increment and lot.min_increment > 0:
        text += f"├─ Minimal oshirish: {format_price(lot.min_increment)}\n"
    if lot.estimated_value and lot.estimated_value > 0:
        text += f"└─ Baholangan qiymati: {format_price(lot.estimated_value)}\n"
    text += "\n"

    # Vaqt
    if lot.auction_start:
        text += "⏰ <b>VAQT:</b>\n"
        text += f"└─ Boshlanish: {lot.auction_start.strftime('%d.%m.%Y %H:%M')}\n\n"

    # Tavsif
    if lot.description:
        clean = clean_text(lot.description)
        if clean:
            text += "📋 <b>TAVSIF:</b>\n"
            text += (clean[:600] + "...\n\n") if len(clean) > 600 else (clean + "\n\n")

    # Xususiyatlar
    if lot.properties and isinstance(lot.properties, dict):
        text += "🔍 <b>XUSUSIYATLAR:</b>\n"
        key_labels = {
            'area': 'Maydoni', 'rooms': 'Xonalar soni',
            'floor': 'Qavat', 'total_floors': 'Jami qavatlar',
            'address': 'Manzil', 'region': 'Viloyat',
            'district': 'Tuman', 'cadastral_number': 'Kadastr raqami',
            'purpose': 'Maqsadi', 'year_built': 'Qurilgan yili',
            'condition': 'Holati', 'size': 'Hajmi',
            'balance_holder': 'Balans saqlovchi',
        }
        shown = 0
        for key, label in key_labels.items():
            if key in lot.properties and lot.properties[key]:
                text += f"• {label}: {lot.properties[key]}\n"
                shown += 1
        for key, value in lot.properties.items():
            if key not in key_labels and value and shown < 20:
                text += f"• {key}: {value}\n"
                shown += 1
        text += "\n"

    # Rasmlar
    text += f"📸 <b>Rasmlar:</b> {len(lot.images)} ta\n\n" if lot.images else "📸 <b>Rasmlar:</b> Mavjud emas\n\n"

    text += f"🔗 <a href='https://e-auksion.uz/lot-view?lot_id={lot.id}'>E-auksion.uz da ko'rish</a>"
    return text


# ============================================================================
# RASMLAR GALEREYASI
# ============================================================================

@router.callback_query(F.data.startswith("auk2:images:"))
async def callback_view_images(callback: CallbackQuery):
    parts = callback.data.split(":")
    lot_id  = int(parts[2])
    index   = int(parts[3])
    main_cat = parts[4] if len(parts) > 4 else "kochmas_mulk"
    sub_cat  = parts[5] if len(parts) > 5 else "kop_qavatli"

    lot = storage.get_lot(lot_id)
    if not lot or not lot.images:
        await callback.answer("Rasmlar topilmadi", show_alert=True)
        return
    if index >= len(lot.images):
        await callback.answer("Rasm topilmadi", show_alert=True)
        return

    image     = lot.images[index]
    breadcrumb = get_breadcrumb(main_cat, sub_cat)
    caption   = (
        f"📂 <b>{breadcrumb}</b>\n\n"
        f"📸 <b>Rasm {index + 1}/{len(lot.images)}</b>\n\n"
        f"<b>{lot.name[:80]}</b>\n"
        f"💰 {format_price(lot.current_price or lot.start_price)}"
    )
    keyboard = get_image_navigation_keyboard(lot.id, index, len(lot.images), main_cat, sub_cat)

    try:
        if callback.message.photo:
            await callback.message.edit_media(
                media=InputMediaPhoto(media=image.get_url(), caption=caption, parse_mode="HTML"),
                reply_markup=keyboard
            )
        else:
            try:
                await callback.message.delete()
            except Exception:
                pass
            await callback.message.answer_photo(
                photo=image.get_url(), caption=caption,
                reply_markup=keyboard, parse_mode="HTML"
            )
    except Exception as e:
        logger.error(f"Galereya xato: {e}")
        await callback.message.answer(caption, reply_markup=keyboard, parse_mode="HTML")

    await callback.answer()


# ============================================================================
# SEVIMLILAR
# ============================================================================

@router.callback_query(F.data.startswith("auk2:fav:"))
async def callback_add_favorite(callback: CallbackQuery):
    parts = callback.data.split(":")
    lot_id, main_cat, sub_cat = int(parts[2]), parts[3], parts[4]
    lot = storage.get_lot(lot_id)
    if not lot:
        await callback.answer("Lot topilmadi", show_alert=True)
        return
    storage.add_favorite(UserFavorite(user_id=callback.from_user.id, lot_id=lot_id, added_at=datetime.now()))
    await callback.answer("⭐ Sevimliga qo'shildi!", show_alert=True)
    keyboard = get_lot_detail_keyboard(lot, callback.from_user.id, main_cat, sub_cat)
    if callback.message.photo:
        await callback.message.edit_reply_markup(reply_markup=keyboard)
    else:
        breadcrumb = get_breadcrumb(main_cat, sub_cat)
        await callback.message.edit_text(
            f"📂 <b>{breadcrumb}</b>\n\n" + _build_full_detail(lot),
            reply_markup=keyboard, parse_mode="HTML"
        )


@router.callback_query(F.data.startswith("auk2:unfav:"))
async def callback_remove_favorite(callback: CallbackQuery):
    parts = callback.data.split(":")
    lot_id, main_cat, sub_cat = int(parts[2]), parts[3], parts[4]
    storage.remove_favorite(callback.from_user.id, lot_id)
    await callback.answer("🗑 Sevimlilardan o'chirildi", show_alert=True)
    lot = storage.get_lot(lot_id)
    if lot:
        keyboard = get_lot_detail_keyboard(lot, callback.from_user.id, main_cat, sub_cat)
        if callback.message.photo:
            await callback.message.edit_reply_markup(reply_markup=keyboard)
        else:
            breadcrumb = get_breadcrumb(main_cat, sub_cat)
            await callback.message.edit_text(
                f"📂 <b>{breadcrumb}</b>\n\n" + _build_full_detail(lot),
                reply_markup=keyboard, parse_mode="HTML"
            )


@router.callback_query(F.data == "auk2:favorites")
async def callback_show_favorites(callback: CallbackQuery):
    user_id = callback.from_user.id
    favorites = storage.get_user_favorites(user_id)
    if not favorites:
        await callback.message.edit_text(
            "⭐ <b>SEVIMLILAR</b>\n\nSizda hali sevimli lotlar yo'q.\n\nLotlarni ko'rib, ⭐ ni bosing!",
            reply_markup=get_back_to_main_keyboard(), parse_mode="HTML"
        )
        await callback.answer()
        return
    lots = [storage.get_lot(f.lot_id) for f in favorites]
    lots = [l for l in lots if l]
    if not lots:
        await callback.message.edit_text(
            "⭐ <b>SEVIMLILAR</b>\n\nSevimli lotlar topilmadi.",
            reply_markup=get_back_to_main_keyboard(), parse_mode="HTML"
        )
        await callback.answer()
        return
    page_lots, total_pages, _, _ = paginate_list(lots, 1, ITEMS_PER_PAGE)
    await callback.message.edit_text(
        f"⭐ <b>SEVIMLILAR</b>\n\n📦 Jami: {len(lots)} ta lot\n\nLotni tanlang:",
        reply_markup=get_favorites_keyboard(page_lots, 1, total_pages), parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data.startswith("auk2:view_fav:"))
async def callback_view_favorite_lot(callback: CallbackQuery):
    lot_id = int(callback.data.split(":")[-1])
    lot = storage.get_lot(lot_id) or await api_client.get_lot_detail(lot_id)
    if not lot:
        await callback.answer("Lot topilmadi", show_alert=True)
        return
    keyboard = get_lot_detail_keyboard(lot, callback.from_user.id, "kochmas_mulk", "kop_qavatli")
    if lot.images:
        caption = _build_short_caption(lot, "⭐ Sevimlilar")
        try:
            await callback.message.delete()
        except Exception:
            pass
        await callback.message.answer_photo(photo=lot.images[0].get_url(), caption=caption, parse_mode="HTML")
        await callback.message.answer(
            "⭐ <b>Sevimlilar</b>\n\n" + _build_full_detail(lot),
            reply_markup=keyboard, parse_mode="HTML"
        )
    else:
        await callback.message.edit_text(
            "⭐ <b>Sevimlilar</b>\n\n" + _build_full_detail(lot),
            reply_markup=keyboard, parse_mode="HTML"
        )
    await callback.answer()


# ============================================================================
# MENING ARIZALARIM
# ============================================================================

@router.callback_query(F.data == "auk2:my_applications")
async def callback_my_applications(callback: CallbackQuery):
    user_id = callback.from_user.id
    applications = storage.get_user_applications(user_id)

    if not applications:
        await callback.message.edit_text(
            "📋 <b>MENING ARIZALARIM</b>\n\n"
            "Siz hali hech qanday ariza yubormagansiz.\n\n"
            "Lotni tanlang va <b>🙋 Qiziqdim</b> tugmasini bosing!",
            reply_markup=get_back_to_main_keyboard(), parse_mode="HTML"
        )
        await callback.answer()
        return

    await callback.message.edit_text(
        f"📋 <b>MENING ARIZALARIM</b>\n\nJami: {len(applications)} ta ariza\n\nLotni tanlang:",
        reply_markup=get_my_applications_keyboard(applications),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data.startswith("auk2:app_detail:"))
async def callback_application_detail(callback: CallbackQuery):
    lot_id  = int(callback.data.split(":")[-1])
    user_id = callback.from_user.id
    app = storage.get_application(user_id, lot_id)
    if not app:
        await callback.answer("Ariza topilmadi", show_alert=True)
        return

    await callback.message.edit_text("⏳ Joriy narx tekshirilmoqda...")

    # API dan joriy narxni olish
    lot = await api_client.get_lot_detail(lot_id)
    if lot:
        app.current_price = lot.current_price or lot.start_price
        storage.update_application_price(lot_id, app.current_price)

    # Narx o'zgarishi
    if app.price_changed():
        diff = app.price_diff()
        if diff > 0:
            price_block = (
                f"\n📈 <b>Narx OSHDI!</b>\n"
                f"├─ Ariza vaqtida: {format_price(app.lot_price)}\n"
                f"├─ Hozir: <b>{format_price(app.current_price)}</b>\n"
                f"└─ Farq: <b>+{format_price(diff)}</b>\n"
            )
        else:
            price_block = (
                f"\n📉 <b>Narx TUSHDI!</b>\n"
                f"├─ Ariza vaqtida: {format_price(app.lot_price)}\n"
                f"├─ Hozir: <b>{format_price(app.current_price)}</b>\n"
                f"└─ Farq: <b>{format_price(diff)}</b>\n"
            )
    else:
        price_block = f"\n💰 <b>Narx:</b> {format_price(app.current_price)}\n<i>(O'zgarmagan)</i>\n"

    status_map = {
        "pending":   "🕐 Kutilmoqda",
        "contacted": "📞 Admin bog'landi",
        "done":      "✅ Yakunlandi",
        "cancelled": "❌ Bekor qilindi",
    }

    text = (
        "📋 <b>ARIZA TAFSILOTI</b>\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        f"📦 <b>Ob'ekt:</b>\n<i>{app.lot_name[:120]}</i>\n"
        f"{price_block}\n"
        f"👤 <b>Ism:</b> {app.name}\n"
        f"📞 <b>Telefon:</b> {app.phone}\n"
        f"📅 <b>Yuborilgan:</b> {app.applied_at.strftime('%d.%m.%Y %H:%M')}\n"
        f"📊 <b>Holat:</b> {status_map.get(app.status, '🕐 Kutilmoqda')}\n\n"
        "━━━━━━━━━━━━━━━━━━━━"
    )

    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🌐 E-auksion.uz da ko'rish", url=f"https://e-auksion.uz/lot-view?lot_id={lot_id}")],
        [InlineKeyboardButton(text="🔄 Narxni yangilash", callback_data=f"auk2:app_detail:{lot_id}")],
        [InlineKeyboardButton(text="🔙 Arizalarim", callback_data="auk2:my_applications")],
    ])

    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()


# ============================================================================
# ARIZA YUBORISH
# ============================================================================

@router.callback_query(F.data.startswith("auk2:apply:"))
async def callback_apply_start(callback: CallbackQuery, state: FSMContext):
    parts   = callback.data.split(":")
    lot_id  = int(parts[2])
    main_cat = parts[3] if len(parts) > 3 else ""
    sub_cat  = parts[4] if len(parts) > 4 else ""

    lot = storage.get_lot(lot_id)
    if not lot:
        await callback.answer("Lot topilmadi", show_alert=True)
        return

    await state.update_data(
        apply_lot_id=lot_id, apply_main_cat=main_cat, apply_sub_cat=sub_cat,
        apply_lot_name=lot.name, apply_lot_price=lot.current_price or lot.start_price,
    )
    await state.set_state(AuksionStatesV2.application_name)

    await callback.message.answer(
        "🏛 <b>AUKSION XIZMATI</b>\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        f"📦 <b>Siz qiziqtirgan ob'ekt:</b>\n<i>{lot.name[:120]}</i>\n\n"
        f"💰 <b>Joriy narx:</b> {format_price(lot.current_price or lot.start_price)}\n\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        "👨‍💼 <b>Hurmatli mijoz!</b>\n\n"
        "Siz ushbu ob'ektga qiziqish bildirdingiz. "
        "Arizangizni qabul qilganimizdan so'ng, "
        "<b>mutaxassis adminimiz</b> siz bilan bog'lanib:\n\n"
        "✅ Ob'ekt haqida to'liq ma'lumot beradi\n"
        "✅ <b>Sizning nomingizdan</b> auksion jarayonida qatnashadi\n"
        "✅ Eng qulay narxda ob'ektni qo'lga kiritishga yordam beradi\n"
        "✅ Barcha hujjat va rasmiyatchilikni hal qiladi\n\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        "📝 <b>1/2 — Ism va familiyangizni yozing:</b>\n\n"
        "<i>Misol: Abbos Aliyev</i>",
        parse_mode="HTML"
    )
    await callback.answer()


@router.message(AuksionStatesV2.application_name)
async def process_application_name(message: Message, state: FSMContext):
    name = message.text.strip()
    if len(name) < 3:
        await message.answer(
            "❌ Ism juda qisqa!\n\nTo'liq ism va familiyangizni kiriting.\n<i>Misol: Abbos Aliyev</i>",
            parse_mode="HTML"
        )
        return
    await state.update_data(apply_name=name)
    await state.set_state(AuksionStatesV2.application_phone)

    from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
    await message.answer(
        f"✅ Rahmat, <b>{name}</b>!\n\n"
        "📞 <b>2/2 — Telefon raqamingizni yuboring:</b>\n\n"
        "• Tugmani bosib yuborish <i>(tavsiya)</i>\n"
        "• Yoki qo'lda: <code>+998901234567</code>",
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="📱 Telefon raqamni yuborish", request_contact=True)],
                [KeyboardButton(text="✏️ Qo'lda yozish")]
            ],
            resize_keyboard=True, one_time_keyboard=True
        ),
        parse_mode="HTML"
    )


@router.message(AuksionStatesV2.application_phone, F.contact)
async def process_phone_contact(message: Message, state: FSMContext):
    phone = message.contact.phone_number
    if not phone.startswith('+'):
        phone = '+' + phone
    await _finish_application(message, state, phone)


@router.message(AuksionStatesV2.application_phone, F.text == "✏️ Qo'lda yozish")
async def process_manual_phone_request(message: Message):
    from aiogram.types import ReplyKeyboardRemove
    await message.answer(
        "📞 Telefon raqamingizni kiriting:\n\n<code>+998901234567</code>",
        reply_markup=ReplyKeyboardRemove(), parse_mode="HTML"
    )


@router.message(AuksionStatesV2.application_phone)
async def process_phone_text(message: Message, state: FSMContext):
    phone = message.text.strip()
    if not (phone.startswith('+998') or phone.startswith('998')):
        await message.answer(
            "❌ Noto'g'ri format!\n\nFormat: <code>+998901234567</code>\n\nQaytadan kiriting:",
            parse_mode="HTML"
        )
        return
    if not phone.startswith('+'):
        phone = '+' + phone
    await _finish_application(message, state, phone)


async def _finish_application(message: Message, state: FSMContext, phone: str):
    from aiogram.types import ReplyKeyboardRemove

    data      = await state.get_data()
    lot_id    = data.get("apply_lot_id")
    lot_name  = data.get("apply_lot_name", "")
    lot_price = data.get("apply_lot_price", 0)
    name      = data.get("apply_name", "")

    # Arizani storage ga saqlash
    storage.add_application(UserApplication(
        user_id=message.from_user.id, lot_id=lot_id,
        lot_name=lot_name, lot_price=lot_price, current_price=lot_price,
        name=name, phone=phone, applied_at=datetime.now(), status="pending",
    ))

    await message.answer(
        "✅ <b>Arizangiz muvaffaqiyatli qabul qilindi!</b>\n\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        f"📦 <b>Ob'ekt:</b> {lot_name[:100]}\n"
        f"💰 <b>Narx:</b> {format_price(lot_price)}\n"
        f"👤 <b>Ism:</b> {name}\n"
        f"📞 <b>Telefon:</b> {phone}\n\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        "🕐 Adminimiz <b>1-2 soat ichida</b> siz bilan bog'lanadi.\n\n"
        "📋 Arizangizni <b>«Mening arizalarim»</b> bo'limida kuzatishingiz mumkin.\n\n"
        "🙏 <b>Ishonchingiz uchun rahmat!</b>",
        reply_markup=ReplyKeyboardRemove(), parse_mode="HTML"
    )

    await _send_to_admin(
        bot=message.bot, user_id=message.from_user.id, username=message.from_user.username,
        name=name, phone=phone, lot_id=lot_id, lot_name=lot_name, lot_price=lot_price
    )
    await state.clear()


async def _send_to_admin(bot, user_id, username, name, phone, lot_id, lot_name, lot_price):
    ADMIN_CHAT_ID = os.getenv("ADMIN_CHAT_ID")
    if not ADMIN_CHAT_ID:
        logger.error("ADMIN_CHAT_ID topilmadi!")
        return
    try:
        await bot.send_message(
            chat_id=ADMIN_CHAT_ID,
            text=(
                "🆕 <b>YANGI ARIZA KELDI!</b>\n"
                "━━━━━━━━━━━━━━━━━━━━\n\n"
                "👤 <b>MIJOZ:</b>\n"
                f"├─ ID: <code>{user_id}</code>\n"
                f"├─ Username: @{username or '—'}\n"
                f"├─ Ism: {name}\n"
                f"└─ Telefon: <code>{phone}</code>\n\n"
                "📦 <b>OB'EKT:</b>\n"
                f"├─ Lot ID: <code>{lot_id}</code>\n"
                f"├─ Nomi: {lot_name[:150]}\n"
                f"├─ Narx: {format_price(lot_price)}\n"
                f"└─ Havola: https://e-auksion.uz/lot-view?lot_id={lot_id}\n\n"
                "━━━━━━━━━━━━━━━━━━━━\n"
                f"📅 {datetime.now().strftime('%d.%m.%Y %H:%M')}\n\n"
                "💬 <i>Iltimos, mijoz bilan tezroq bog'laning!</i>"
            ),
            parse_mode="HTML"
        )
        logger.info(f"Ariza yuborildi: Lot #{lot_id}, User {user_id}")
    except Exception as e:
        logger.error(f"Admin'ga yuborishda xato: {e}")


@router.callback_query(F.data == "auk2:apply_cancel")
async def callback_cancel_application(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("❌ Ariza bekor qilindi.", reply_markup=get_back_to_main_keyboard())
    await callback.answer()

# ============================================================================
# ASOSIY MENYUGA QAYTISH (inline "Bosh menyu" tugmasi)
# ============================================================================

@router.callback_query(F.data == "main_menu")
async def callback_to_main_menu(callback: CallbackQuery, state: FSMContext):
    """Inline 'Bosh menyu' tugmasi - asosiy menyuga qaytish"""
    await state.clear()
    try:
        from utils.keyboards import get_main_menu
        await callback.message.answer("🏠 Asosiy menyu:", reply_markup=get_main_menu())
        await callback.message.delete()
    except Exception:
        await callback.message.edit_text(
            "🏠 Asosiy menyuga qaytish uchun /start bosing",
            reply_markup=None
        )
    await callback.answer()


@router.callback_query(F.data == "noop")
async def callback_noop(callback: CallbackQuery):
    """Hech narsa qilmaydigan callback (sahifa ko'rsatkichi uchun)"""
    await callback.answer()