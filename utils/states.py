"""
FSM States - MUKAMMAL VERSIYA
Barcha states qo'shilgan
"""
from aiogram.fsm.state import State, StatesGroup


# ============================================================================
# KO'CHMAS MULK STATES
# ============================================================================

class KochmasMulkSellStates(StatesGroup):
    """Mulk sotish jarayoni"""
    choosing_region = State()
    choosing_property_type = State()
    entering_full_name = State()
    entering_phone = State()
    entering_area = State()
    entering_rooms = State()
    entering_floor = State()
    entering_total_floors = State()
    entering_price = State()
    entering_address = State()
    entering_description = State()
    uploading_photo = State()
    uploading_video = State()
    confirmation = State()


class KochmasMulkBuyStates(StatesGroup):
    """Mulk sotib olish jarayoni"""
    choosing_region = State()
    choosing_property_type = State()
    viewing = State()


# ============================================================================
# IJARA STATES
# ============================================================================

class IjaraRentOutStates(StatesGroup):
    """Ijaraga berish jarayoni"""
    choosing_region = State()
    choosing_property_type = State()
    entering_full_name = State()
    entering_phone = State()
    entering_area = State()
    entering_rooms = State()
    entering_floor = State()
    entering_total_floors = State()
    entering_monthly_price = State()
    entering_rental_period = State()
    entering_address = State()
    entering_description = State()
    uploading_photo = State()
    uploading_video = State()
    confirmation = State()


class IjaraRentInStates(StatesGroup):
    """Ijaraga olish jarayoni"""
    choosing_region = State()
    choosing_property_type = State()
    viewing = State()


# ============================================================================
# ARIZA STATES
# ============================================================================

class ApplicationStates(StatesGroup):
    """Ariza yuborish jarayoni"""
    entering_name = State()
    entering_phone = State()
    entering_comment = State()


# ============================================================================
# AUKSION STATES
# ============================================================================

class AuksionStatesV2(StatesGroup):
    """Auksion jarayoni"""
    searching = State()
    application_name = State()
    application_phone = State()
    application_comment = State()
    application_confirm = State()