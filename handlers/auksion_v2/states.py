"""
Auksion V2 uchun FSM holatlari
"""
from aiogram.fsm.state import State, StatesGroup


class AuksionStatesV2(StatesGroup):
    """Auksion V2 jarayoni holatlari"""
    
    # Qidiruv
    searching = State()  # Qidiruv so'zini kiritish
    
    # Ariza berish
    application_comment = State()  # Ariza izohini kiritish
    application_confirm = State()  # Arizani tasdiqlash