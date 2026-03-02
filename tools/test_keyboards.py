from handlers.admin.keyboards import admin_main_kb, choose_section_kb, confirm_publish_kb, confirm_delete_kb
from utils.keyboards import get_object_actions_keyboard, get_pagination_keyboard, get_my_objects_keyboard

kb1 = admin_main_kb()
kb2 = choose_section_kb()
kb3 = confirm_publish_kb()
kb4 = confirm_delete_kb(123)
kb5 = get_object_actions_keyboard(1, 'kochmas')
kb6 = get_pagination_keyboard(0, 3, 'test')
kb7 = get_my_objects_keyboard(True)

print('kb types:', type(kb1), type(kb2), type(kb3), type(kb4), type(kb5), type(kb6), type(kb7))
print('inline_keyboard lengths:', len(kb1.inline_keyboard), len(kb2.inline_keyboard), len(kb3.inline_keyboard))
print('done')
