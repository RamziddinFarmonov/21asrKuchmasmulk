from utils.keyboards import (
    get_main_menu, get_back_button, get_cancel_button, get_skip_and_cancel,
    get_kochmas_mulk_menu, get_property_types_keyboard, get_regions_keyboard,
    get_ijara_menu, get_rental_types_keyboard, get_rental_period_keyboard,
    get_object_actions_keyboard, get_pagination_keyboard, get_my_objects_keyboard
)

# call functions
kb1 = get_main_menu()
kb2 = get_back_button()
kb3 = get_cancel_button()
kb4 = get_skip_and_cancel()
kb5 = get_kochmas_mulk_menu()
kb6 = get_property_types_keyboard()
kb7 = get_regions_keyboard()
kb8 = get_ijara_menu()
kb9 = get_rental_types_keyboard()
kb10 = get_rental_period_keyboard()

kb11 = get_object_actions_keyboard(1, 'kochmas')
kb12 = get_pagination_keyboard(1, 5, 'pref')
kb13 = get_my_objects_keyboard(True)

print(type(kb1), type(kb11), type(kb12), type(kb13))
print('done')
