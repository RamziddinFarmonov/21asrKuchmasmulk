"""
handlers/admin/main.py
======================
Admin panel asosiy menyu, statistika,
ro'yxat ko'rish, o'chirish, tahrirlash handlerlari.
"""
import logging
from datetime import datetime

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

from .utils import (
    is_admin, logger,
    get_admin_main_menu, get_admin_kochmas_menu, get_admin_ijara_menu,
    get_cancel_admin,
    kochmas_detail_kb, ijara_detail_kb, confirm_delete_kb,
    db_get_all_kochmas, db_get_all_ijara,
    format_kochmas_text, format_ijara_text,
    AdminEditKochmas, AdminEditIjara,
)
from utils.constants import format_price, get_region_name_by_code, get_property_type_name_by_code, format_area

router = Router()

# ============================================================================
# KIRISH VA ASOSIY MENYU
# ============================================================================

@router.message(Command("admin"))
async def admin_command(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        await message.answer("❌ Sizda admin huquqi yo'q.")
        return
    await state.clear()
    await message.answer(
        f"👑 <b>ADMIN PANEL</b>\n\nXush kelibsiz, {message.from_user.first_name}!\n\nBo'limni tanlang:",
        reply_markup=get_admin_main_menu(), parse_mode="HTML"
    )


@router.message(F.text == "🔙 Admin menyu")
async def back_to_admin_menu(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    await state.clear()
    await message.answer("👑 Admin panel:", reply_markup=get_admin_main_menu())


@router.message(F.text == "🔙 Asosiy menyuga qaytish")
async def back_to_main(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    await state.clear()
    from utils.keyboards import get_main_menu
    await message.answer("🏠 Asosiy menyu:", reply_markup=get_main_menu())


# ============================================================================
# STATISTIKA
# ============================================================================

@router.message(F.text == "📊 Statistika")
async def admin_statistics(message: Message):
    if not is_admin(message.from_user.id):
        return
    from database.db_manager import db
    try:
        stats = db.get_statistics()
        text = (
            "📊 <b>BOT STATISTIKASI</b>\n\n"
            f"🏠 Ko'chmas mulk (faol): <b>{stats.get('kochmas_mulk', 0)}</b> ta\n"
            f"📋 Ijara (faol): <b>{stats.get('ijara', 0)}</b> ta\n"
            f"📌 Jami faol: <b>{stats.get('total', 0)}</b> ta\n\n"
            f"📅 {datetime.now().strftime('%d.%m.%Y %H:%M')}"
        )
    except Exception as e:
        text = f"❌ Xato: {e}"
    await message.answer(text, reply_markup=get_admin_main_menu(), parse_mode="HTML")


# ============================================================================
# KO'CHMAS MULK — BO'LIM
# ============================================================================

@router.message(F.text == "🏠 Ko'chmas mulk (Admin)")
async def admin_kochmas_section(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    await state.clear()
    await message.answer("🏠 Ko'chmas mulk boshqaruvi:", reply_markup=get_admin_kochmas_menu())


@router.message(F.text == "📋 Barcha Ko'chmas mulk e'lonlar")
async def admin_list_kochmas(message: Message):
    if not is_admin(message.from_user.id):
        return
    from database.db_manager import db
    # Faqat FAOL e'lonlar
    objects = [o for o in db_get_all_kochmas(db) if o.get('is_active', 1)]
    if not objects:
        await message.answer("📭 Faol Ko'chmas mulk e'lonlari yo'q.", reply_markup=get_admin_kochmas_menu())
        return
    keyboard = []
    for obj in objects:
        prop   = get_property_type_name_by_code(obj.get('property_type', ''))
        rooms  = f"{obj['rooms']}-xona " if obj.get('rooms') else ""
        price  = format_price(obj.get('price', 0))
        region = get_region_name_by_code(obj.get('region', ''))
        label  = f"#{obj['id']} | {rooms}{prop} | {price} | {region}"
        keyboard.append([InlineKeyboardButton(text=label[:64], callback_data=f"akv_kochmas_{obj['id']}")])
    await message.answer(
        f"🏠 <b>BARCHA KO'CHMAS MULK E'LONLAR</b>\n\nFaol: {len(objects)} ta",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard), parse_mode="HTML"
    )


@router.callback_query(F.data.startswith("akv_kochmas_"))
async def admin_view_kochmas(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Ruxsat yo'q", show_alert=True)
        return
    from database.db_manager import db
    try:
        obj_id = int(callback.data.split("_")[-1])
    except (ValueError, IndexError):
        await callback.answer("❌ Xato", show_alert=True)
        return
    obj = db.get_kochmas_mulk_by_id(obj_id)
    if not obj:
        await callback.answer("❌ Topilmadi!", show_alert=True)
        return
    text = format_kochmas_text(obj)
    kb   = kochmas_detail_kb(obj_id)
    try:
        if obj.get('photo_id'):
            await callback.message.delete()
            await callback.bot.send_photo(
                chat_id=callback.message.chat.id,
                photo=obj['photo_id'], caption=text, reply_markup=kb, parse_mode="HTML"
            )
        else:
            await callback.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
    except Exception:
        await callback.message.answer(text, reply_markup=kb, parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data == "akl_kochmas")
async def adm_back_kochmas_list(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Ruxsat yo'q", show_alert=True)
        return
    try:
        await callback.message.delete()
    except Exception:
        pass
    await admin_list_kochmas(callback.message)
    await callback.answer()


# ============================================================================
# KO'CHMAS — O'CHIRISH
# ============================================================================

@router.callback_query(F.data.startswith("akd_kochmas_"))
async def admin_delete_kochmas_ask(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Ruxsat yo'q", show_alert=True)
        return
    try:
        obj_id = int(callback.data.split("_")[-1])
    except (ValueError, IndexError):
        await callback.answer("❌ Xato", show_alert=True)
        return
    await callback.message.answer(
        f"⚠️ <b>#{obj_id} e'lonni o'chirmoqchimisiz?</b>\n\nBu amalni qaytarib bo'lmaydi!",
        reply_markup=confirm_delete_kb("kochmas", obj_id), parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data.startswith("akdc_kochmas_"))
async def admin_delete_kochmas_do(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Ruxsat yo'q", show_alert=True)
        return
    from database.db_manager import db
    try:
        obj_id = int(callback.data.split("_")[-1])
    except (ValueError, IndexError):
        await callback.answer("❌ Xato", show_alert=True)
        return
    try:
        db.delete_kochmas_mulk(obj_id)
        await callback.message.edit_text(
            f"✅ <b>Ko'chmas mulk #{obj_id} o'chirildi!</b>\n\n"
            "E'lon endi barcha bo'limlarda ko'rinmaydi.",
            parse_mode="HTML"
        )
        logger.info(f"Admin {callback.from_user.id}: Ko'chmas #{obj_id} o'chirildi")
    except Exception as e:
        await callback.message.edit_text(f"❌ Xato: {e}")
    await callback.answer()


@router.callback_query(F.data.startswith("akv_kochmas_") & F.data.contains("_") | F.data.startswith("akv_kochmas_"))
async def _noop(callback: CallbackQuery):
    # Bu handler yuqoridagi bilan overlap qilmasligi uchun bo'sh
    pass


# O'chirishni bekor qilish — e'lonni qayta ko'rsatish
@router.callback_query(F.data.startswith("akv_kochmas_"))
async def admin_cancel_delete_kochmas(callback: CallbackQuery):
    # Bu "Bekor" tugmasi: akv_kochmas_ID formatida
    await admin_view_kochmas(callback)


# ============================================================================
# KO'CHMAS — TAHRIRLASH
# ============================================================================

@router.callback_query(F.data.startswith("ake_kochmas_"))
async def admin_edit_kochmas_start(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Ruxsat yo'q", show_alert=True)
        return
    parts  = callback.data.split("_")
    obj_id = int(parts[-1])
    field  = parts[-2]
    await state.update_data(edit_obj_id=obj_id, edit_obj_type="kochmas", edit_field=field)
    await state.set_state(AdminEditKochmas.entering_value)
    prompts = {
        "price":       "💰 Yangi narxni kiriting (so'm):\n<i>Masalan: 350000000</i>",
        "address":     "📍 Yangi manzilni kiriting:",
        "description": "📝 Yangi tavsifni kiriting:",
        "photo":       "📸 Yangi rasmni yuboring:",
        "video":       "🎥 Yangi videoni yuboring:",
    }
    await callback.message.answer(
        f"✏️ <b>Tahrirlash — #{obj_id}</b>\n\n{prompts.get(field, 'Yangi qiymat:')}",
        reply_markup=get_cancel_admin(), parse_mode="HTML"
    )
    await callback.answer()


@router.message(AdminEditKochmas.entering_value)
async def admin_edit_kochmas_save(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    if message.text == "❌ Bekor qilish":
        await state.clear()
        return await message.answer("Bekor qilindi.", reply_markup=get_admin_kochmas_menu())
    from database.db_manager import db
    data   = await state.get_data()
    obj_id = data['edit_obj_id']
    field  = data['edit_field']
    try:
        if field == "price":
            val = float(message.text.replace(" ", "").replace(",", ""))
            db.update_kochmas_mulk(obj_id, {"price": val})
            await message.answer(f"✅ Narx yangilandi: {format_price(val)}", reply_markup=get_admin_kochmas_menu())
        elif field == "address":
            db.update_kochmas_mulk(obj_id, {"address": message.text.strip()})
            await message.answer("✅ Manzil yangilandi!", reply_markup=get_admin_kochmas_menu())
        elif field == "description":
            db.update_kochmas_mulk(obj_id, {"description": message.text.strip()})
            await message.answer("✅ Tavsif yangilandi!", reply_markup=get_admin_kochmas_menu())
        elif field == "photo":
            if not message.photo:
                return await message.answer("❌ Rasm yuboring!")
            db.update_kochmas_mulk(obj_id, {"photo_id": message.photo[-1].file_id})
            await message.answer("✅ Rasm yangilandi!", reply_markup=get_admin_kochmas_menu())
        elif field == "video":
            if not message.video:
                return await message.answer("❌ Video yuboring!")
            db.update_kochmas_mulk(obj_id, {"video_id": message.video.file_id})
            await message.answer("✅ Video yangilandi!", reply_markup=get_admin_kochmas_menu())
        logger.info(f"Admin {message.from_user.id}: Ko'chmas #{obj_id} '{field}' yangilandi")
    except Exception as e:
        await message.answer(f"❌ Xato: {e}", reply_markup=get_admin_kochmas_menu())
    await state.clear()


# ============================================================================
# IJARA — BO'LIM
# ============================================================================

@router.message(F.text == "📋 Ijara (Admin)")
async def admin_ijara_section(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    await state.clear()
    await message.answer("📋 Ijara boshqaruvi:", reply_markup=get_admin_ijara_menu())


@router.message(F.text == "📋 Barcha Ijara e'lonlar")
async def admin_list_ijara(message: Message):
    if not is_admin(message.from_user.id):
        return
    from database.db_manager import db
    # Faqat FAOL e'lonlar
    objects = [o for o in db_get_all_ijara(db) if o.get('is_active', 1)]
    if not objects:
        await message.answer("📭 Faol Ijara e'lonlari yo'q.", reply_markup=get_admin_ijara_menu())
        return
    keyboard = []
    for obj in objects:
        prop   = get_property_type_name_by_code(obj.get('property_type', ''))
        rooms  = f"{obj['rooms']}-xona " if obj.get('rooms') else ""
        price  = format_price(obj.get('monthly_price', 0))
        region = get_region_name_by_code(obj.get('region', ''))
        label  = f"#{obj['id']} | {rooms}{prop} | {price}/oy | {region}"
        keyboard.append([InlineKeyboardButton(text=label[:64], callback_data=f"akv_ijara_{obj['id']}")])
    await message.answer(
        f"📋 <b>BARCHA IJARA E'LONLAR</b>\n\nFaol: {len(objects)} ta",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard), parse_mode="HTML"
    )


@router.callback_query(F.data.startswith("akv_ijara_"))
async def admin_view_ijara(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Ruxsat yo'q", show_alert=True)
        return
    from database.db_manager import db
    try:
        obj_id = int(callback.data.split("_")[-1])
    except (ValueError, IndexError):
        await callback.answer("❌ Xato", show_alert=True)
        return
    obj = db.get_ijara_by_id(obj_id)
    if not obj:
        await callback.answer("❌ Topilmadi!", show_alert=True)
        return
    text = format_ijara_text(obj)
    kb   = ijara_detail_kb(obj_id)
    try:
        if obj.get('photo_id'):
            await callback.message.delete()
            await callback.bot.send_photo(
                chat_id=callback.message.chat.id,
                photo=obj['photo_id'], caption=text, reply_markup=kb, parse_mode="HTML"
            )
        else:
            await callback.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
    except Exception:
        await callback.message.answer(text, reply_markup=kb, parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data == "akl_ijara")
async def adm_back_ijara_list(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Ruxsat yo'q", show_alert=True)
        return
    try:
        await callback.message.delete()
    except Exception:
        pass
    await admin_list_ijara(callback.message)
    await callback.answer()


# ============================================================================
# IJARA — O'CHIRISH
# ============================================================================

@router.callback_query(F.data.startswith("akd_ijara_"))
async def admin_delete_ijara_ask(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Ruxsat yo'q", show_alert=True)
        return
    try:
        obj_id = int(callback.data.split("_")[-1])
    except (ValueError, IndexError):
        await callback.answer("❌ Xato", show_alert=True)
        return
    await callback.message.answer(
        f"⚠️ <b>Ijara #{obj_id} e'lonni o'chirmoqchimisiz?</b>\n\nBu amalni qaytarib bo'lmaydi!",
        reply_markup=confirm_delete_kb("ijara", obj_id), parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data.startswith("akdc_ijara_"))
async def admin_delete_ijara_do(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Ruxsat yo'q", show_alert=True)
        return
    from database.db_manager import db
    try:
        obj_id = int(callback.data.split("_")[-1])
    except (ValueError, IndexError):
        await callback.answer("❌ Xato", show_alert=True)
        return
    try:
        db.delete_ijara(obj_id)
        await callback.message.edit_text(
            f"✅ <b>Ijara #{obj_id} o'chirildi!</b>\n\n"
            "E'lon endi barcha bo'limlarda ko'rinmaydi.",
            parse_mode="HTML"
        )
        logger.info(f"Admin {callback.from_user.id}: Ijara #{obj_id} o'chirildi")
    except Exception as e:
        await callback.message.edit_text(f"❌ Xato: {e}")
    await callback.answer()


# ============================================================================
# IJARA — TAHRIRLASH
# ============================================================================

@router.callback_query(F.data.startswith("ake_ijara_"))
async def admin_edit_ijara_start(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Ruxsat yo'q", show_alert=True)
        return
    parts  = callback.data.split("_")
    obj_id = int(parts[-1])
    field  = parts[-2]
    await state.update_data(edit_obj_id=obj_id, edit_obj_type="ijara", edit_field=field)
    await state.set_state(AdminEditIjara.entering_value)
    prompts = {
        "monthly": "💰 Yangi oylik narxni kiriting (so'm):",
        "price":   "💰 Yangi oylik narxni kiriting (so'm):",
        "address": "📍 Yangi manzilni kiriting:",
        "description": "📝 Yangi tavsifni kiriting:",
        "photo":   "📸 Yangi rasmni yuboring:",
        "video":   "🎥 Yangi videoni yuboring:",
    }
    await callback.message.answer(
        f"✏️ <b>Tahrirlash — #{obj_id}</b>\n\n{prompts.get(field, 'Yangi qiymat:')}",
        reply_markup=get_cancel_admin(), parse_mode="HTML"
    )
    await callback.answer()


@router.message(AdminEditIjara.entering_value)
async def admin_edit_ijara_save(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    if message.text == "❌ Bekor qilish":
        await state.clear()
        return await message.answer("Bekor qilindi.", reply_markup=get_admin_ijara_menu())
    from database.db_manager import db
    data   = await state.get_data()
    obj_id = data['edit_obj_id']
    field  = data['edit_field']
    try:
        if field in ("monthly", "price"):
            val = float(message.text.replace(" ", "").replace(",", ""))
            db.update_ijara(obj_id, {"monthly_price": val})
            await message.answer(f"✅ Oylik narx: {format_price(val)}", reply_markup=get_admin_ijara_menu())
        elif field == "address":
            db.update_ijara(obj_id, {"address": message.text.strip()})
            await message.answer("✅ Manzil yangilandi!", reply_markup=get_admin_ijara_menu())
        elif field == "description":
            db.update_ijara(obj_id, {"description": message.text.strip()})
            await message.answer("✅ Tavsif yangilandi!", reply_markup=get_admin_ijara_menu())
        elif field == "photo":
            if not message.photo:
                return await message.answer("❌ Rasm yuboring!")
            db.update_ijara(obj_id, {"photo_id": message.photo[-1].file_id})
            await message.answer("✅ Rasm yangilandi!", reply_markup=get_admin_ijara_menu())
        elif field == "video":
            if not message.video:
                return await message.answer("❌ Video yuboring!")
            db.update_ijara(obj_id, {"video_id": message.video.file_id})
            await message.answer("✅ Video yangilandi!", reply_markup=get_admin_ijara_menu())
        logger.info(f"Admin {message.from_user.id}: Ijara #{obj_id} '{field}' yangilandi")
    except Exception as e:
        await message.answer(f"❌ Xato: {e}", reply_markup=get_admin_ijara_menu())
    await state.clear()