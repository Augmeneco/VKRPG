import vkrpg


class MenuBattleContext(vkrpg.contexts.BaseContext):
    menu_list = [
        {'title': 'Игра с MasterAI'},
        {'title': 'Игра в лобби'},
        {'title': 'Дуель'},
        {'title': 'В главное меню', 'one_time': True}
    ]


    def on_message(self, msg):
        if msg['pure_text'].lower() in ('меню'):
            vkrpg.chat.actions_display(self.menu_list, msg['peer_id'])
            return
        menu_item_select = vkrpg.chat.actions_select(self.menu_list, msg)

        if menu_item_select == 0:
            context = vkrpg.contexts.get_context('BattleAIContext')
            _, contextcopy = context.copy()
            contextcopy.enable_for_vkid(msg['peer_id'], msg)
        # elif menu_item_select == 1:
        #     copyid = vkrpg.contexts.create_context_copy('battle_lobby')
        #     vkrpg.contexts.enable_context(msg['from_id'], copyid, (msg, copyid))
        # elif menu_item_select == 2:
        #     copyid = vkrpg.contexts.create_context_copy('battle_duel')
        #     vkrpg.contexts.enable_context(msg['from_id'], copyid, (msg, menu_item_select))
        elif menu_item_select == 3:
            vkrpg.contexts.get_context('MenuMainContext').enable_for_vkid(msg['from_id'], msg)


    def on_enablecontext(self, msg):
        vkrpg.chat.actions_display(self.menu_list, msg['peer_id'])