import vkrpg


class MenuInventoryContext(vkrpg.contexts.BaseContext):
    menu_list = [
        {'title': 'Предметы', 'one_time': False},
        {'title': 'Слуги', 'one_time': False},
        {'title': 'Выбрать слуг для битв', 'one_time': False},
        {'title': 'В главное меню', 'one_time': True}
    ]


    def on_message(self, msg):
        if msg['pure_text'].lower() in ('меню'):
            vkrpg.chat.actions_display(self.menu_list, msg['peer_id'])
            return
        menu_item_select = vkrpg.chat.actions_select(self.menu_list, msg)

        if menu_item_select == 0:
            user = vkrpg.db[msg['from_id']]
            vkrpg.chat.apisay(str(user['save']['inventory']), msg['peer_id'])
        elif menu_item_select == 1:
            user = vkrpg.db[msg['from_id']]
            if len(user['save']['inventory']['servants']) != 0:
                out = '[ System ] Ваши слуги:\n'
                for name, obj in user['save']['inventory']['servants'].items():
                    out += name + ' - HP: ' + str(obj['hp']) + ' | ATK: ' + str(obj['atk']) + '\n'
                vkrpg.chat.apisay(out, msg['peer_id'])
            else:
                out = '[ System ] У тебя нет слуг. Обратись к Ассоциации Магов через команду "старт"'
                vkrpg.chat.apisay(out, msg['peer_id'])
        elif menu_item_select == 3:
            vkrpg.contexts.get_context('MenuMainContext').enable_for_vkid(msg['from_id'], msg)


    def on_enablecontext(self, msg):
        vkrpg.chat.actions_display(self.menu_list, msg['peer_id'])
