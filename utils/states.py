"""
FSM States - MUKAMMAL VERSIYA
Barcha states qo'shilgan
"""
from aiogram.fsm.state import State, StatesGroup
 
 
class KochmasMulkSellStates(StatesGroup):
    choosing_region       = State()
    choosing_district     = State()
    choosing_property_type = State()
    entering_full_name    = State()
    entering_phone        = State()
    entering_area         = State()
    entering_rooms        = State()
    entering_price        = State()
    entering_floor        = State()
    entering_total_floors = State()
    entering_address      = State()
    entering_description  = State()
    uploading_photo       = State()
    uploading_video       = State()
    confirmation          = State()
 
 
class KochmasMulkBuyStates(StatesGroup):
    choosing_region       = State()
    choosing_district     = State()
    choosing_property_type = State()
 
 
class IjaraRentOutStates(StatesGroup):
    choosing_region       = State()
    choosing_district     = State()
    choosing_property_type = State()
    entering_full_name    = State()
    entering_phone        = State()
    entering_area         = State()
    entering_rooms        = State()
    entering_monthly_price = State()
    entering_floor        = State()
    entering_total_floors = State()
    entering_rental_period = State()
    entering_address      = State()
    entering_description  = State()
    uploading_photo       = State()
    uploading_video       = State()
    confirmation          = State()
 
 
class IjaraRentInStates(StatesGroup):
    choosing_region       = State()
    choosing_district     = State()
    choosing_property_type = State()
 

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