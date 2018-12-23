import vkrpg


menu_list = [
    {'title': 'Игра с MasterAI'},
    {'title': 'Игра в лобби'},
    {'title': 'Дуель'},
    {'title': 'В главное меню', 'one_time': True}
]


def menu(msg):
    if msg['pure_text'].lower() in ('меню'):
        vkrpg.chat.actions_display(menu_list, msg['peer_id'])
        return
    menu_item_select = vkrpg.chat.actions_select(menu_list, msg)

    if menu_item_select == 0:
        copyid, _ = vkrpg.contexts.create_context_copy('battle_ai')
        vkrpg.contexts.enable_context(msg['from_id'], copyid, (msg, copyid))
    # elif menu_item_select == 1:
    #     copyid = vkrpg.contexts.create_context_copy('battle_lobby')
    #     vkrpg.contexts.enable_context(msg['from_id'], copyid, (msg, copyid))
    # elif menu_item_select == 2:
    #     copyid = vkrpg.contexts.create_context_copy('battle_duel')
    #     vkrpg.contexts.enable_context(msg['from_id'], copyid, (msg, menu_item_select))
    elif menu_item_select == 3:
        vkrpg.contexts.enable_context(msg['from_id'], 'menu_main', msg)


def enablecontext(msg):
    vkrpg.chat.actions_display(menu_list, msg['peer_id'])


vkrpg.contexts.create_context('menu_battle')
vkrpg.events.add_event('on_message', menu, 'menu_battle')
vkrpg.events.add_event('on_enablecontext', enablecontext, 'menu_battle')