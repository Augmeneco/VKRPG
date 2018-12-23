import vkrpg

menu_list = [
    {'title': 'Предметы', 'one_time': False},
    {'title': 'Слуги', 'one_time': False},
    {'title': 'Выбрать слуг для битв', 'one_time': False},
    {'title': 'В главное меню', 'one_time': True}
]


def menu(msg):
    if msg['pure_text'].lower() in ('меню'):
        vkrpg.chat.actions_display(menu_list, msg['peer_id'])
        return
    menu_item_select = vkrpg.chat.actions_select(menu_list, msg)

    vkrpg.db.cursor.execute("SELECT save FROM users WHERE id=" + str(msg['from_id']))
    save = vkrpg.db.cursor.fetchone()[0]

    if menu_item_select == 0:
        vkrpg.chat.apisay(str(save['inventory']), msg['peer_id'])
    elif menu_item_select == 1:
        if len(save['servants']) != 0:
            out = '[ System ] Ваши слуги:\n'
            for name, obj in save['servants'].items():
                out += name + ' - HP: ' + str(obj['hp']) + ' | ATK: ' + str(obj['atk']) + '\n'
            vkrpg.chat.apisay(out, msg['peer_id'])
        else:
            out = '[ System ] У тебя нет слуг. Обратись к Ассоциации Магов через команду "старт"'
            vkrpg.chat.apisay(out, msg['peer_id'])
    elif menu_item_select == 3:
        vkrpg.contexts.enable_context(msg['from_id'], 'menu_main', msg)


def enablecontext(msg):
    vkrpg.chat.actions_display(menu_list, msg['peer_id'])


vkrpg.contexts.create_context('menu_inventory')
vkrpg.events.add_event('on_message', menu, 'menu_inventory')
vkrpg.events.add_event('on_enablecontext', enablecontext, 'menu_inventory')