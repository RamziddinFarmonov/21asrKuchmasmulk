"""
Auksion V2 uchun FSM holatlari
"""
from aiogram.fsm.state import State, StatesGroup


class AuksionStatesV2(StatesGroup):
    """Auksion V2 jarayoni holatlari"""
    
    # Qidiruv
    searching = State()  # Qidiruv so'zini kiritish
    
    # Ariza berish - TO'LIQ
    application_name = State()  # Ism va familiya
    application_phone = State()  # Telefon raqam
    application_comment = State()  # Qo'shimcha izoh
    application_confirm = State()  # Tasdiqlash