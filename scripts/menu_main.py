import vkrpg


menu_list = [
    {'title': 'Задания', 'context': 'missions'},
    {'title': 'Сражения', 'context': 'battle'},
    {'title': 'Профиль', 'context': 'profile'},
    {'title': 'Инвентарь', 'context': 'menu_inventory'},
    {'title': 'Малый Грааль', 'context': 'graal'}
]


def menu(msg):
    if msg['pure_text'].lower() in ('меню'):
        vkrpg.chat.actions_display(menu_list, msg['peer_id'])
        return
    menu_item_select = vkrpg.chat.actions_select(menu_list, msg)

    if menu_item_select is not None:
        vkrpg.contexts.enable_context(msg['from_id'], menu_list[menu_item_select]['context'], msg)


def enablecontext(msg):
    vkrpg.chat.actions_display(menu_list, msg['peer_id'])


vkrpg.contexts.create_context('menu_main')
vkrpg.events.add_event('on_message', menu, 'menu_main')
vkrpg.events.add_event('on_enablecontext', enablecontext, 'menu_main')