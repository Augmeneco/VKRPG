import vkrpg


class MenuMainContext(vkrpg.contexts.BaseContext):
    menu_list = [
        {'title': 'Задания', 'context': 'MissionsContext'},
        {'title': 'Сражения', 'context': 'MenuBattleContext'},
        {'title': 'Профиль', 'context': 'ProfileContext'},
        {'title': 'Инвентарь', 'context': 'MenuInventoryContext'},
        {'title': 'Малый Грааль', 'context': 'GraalContext'}
    ]

    def on_message(self, msg):
        if msg['pure_text'].lower() in ('меню'):
            vkrpg.chat.actions_display(self.menu_list, msg['peer_id'])
            return
        menu_item_select = vkrpg.chat.actions_select(self.menu_list, msg)

        if menu_item_select is not None:
            c = vkrpg.contexts.get_context(self.menu_list[menu_item_select]['context'])
            c.enable_for_vkid(msg['from_id'], msg)

    def on_enablecontext(self, msg):
        vkrpg.chat.actions_display(self.menu_list, msg['peer_id'])