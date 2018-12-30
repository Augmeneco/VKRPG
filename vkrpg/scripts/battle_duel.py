import vkrpg

class BattleDuelContext(vkrpg.contexts.BaseContext):
    menu_list = [
        {'title': 'Задания', 'context': 'missions'},
        {'title': 'Сражения', 'context': 'battle'},
        {'title': 'Профиль', 'context': 'profile'},
        {'title': 'Инвентарь', 'context': 'menu_inventory'},
        {'title': 'Малый Грааль', 'context': 'graal'}
    ]


    def on_message(self, msg):
        if msg['pure_text'].lower() in ('меню'):
            vkrpg.chat.actions_display(self.menu_list, msg['peer_id'])
            return
        menu_item_select = vkrpg.chat.actions_select(self.menu_list, msg)

        if menu_item_select is not None:
            vkrpg.contexts.enable_context(msg['from_id'], self.menu_list[menu_item_select]['context'], msg)


    def on_enablecontext(self, obj):
        if obj[1] == 0:
            pass
        elif obj[1] == 1:
            pass
        elif obj[1] == 2:
            pass
        vkrpg.chat.actions_display(self.menu_list, obj[0]['peer_id'])