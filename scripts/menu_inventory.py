class MenuInventory:
    def __init__(self):
        self.req = __import__('requests')
        self.random = __import__('random')
        self.json = __import__('json')
        self.sqlite3 = __import__('sqlite3')
        vkrpg.contexts.create_context('menu_inventory')
        vkrpg.events.add_event('on_message', self.menu, 'menu_inventory')
        vkrpg.events.add_event('on_enablecontext', self.enablecontext, 'menu_inventory')

    def menu(self, msg):
        menu_list = [
            {'title': 'Предметы', 'context': 'menu_inventory'},
            {'title': 'Слуги', 'context': 'menu_inventory'},
            {'title': 'В главное меню', 'context': 'menu_main'}
        ]

        if msg['pure_text'].lower() == 'меню':
            out = '[ System ] Выберете пункт меню (цифра или название):\n'
            for idx, item in enumerate(menu_list):
                out += str(idx+1) + ' - ' + item['title'] + '\n'
            vkrpg.chat.apisay(out, msg['peer_id'])

            return

        if msg['pure_text'].isdigit():
            if len(menu_list)+1 >= int(msg['pure_text']):
                menu_item_select = int(msg['pure_text'])
            else:
                out = '[ System ] Такого пункта меню не существует. Напиши "меню" чтоб узнать какие пункты существуют.'
                vkrpg.chat.apisay(out, msg['peer_id'])
                return
        else:
            menu_item = list([item for item in menu_list if item['title'].lower() == msg['pure_text'].lower()])
            if menu_item != []:
                menu_item_select = list([idx for idx,item in enumerate(menu_list)
                                         if item['title'].lower() == msg['pure_text'].lower()])[0]
            else:
                out = '[ System ] Такого пункта меню не существует. Напиши "меню" чтоб узнать какие пункты существуют.'
                vkrpg.chat.apisay(out, msg['peer_id'])
                return

        vkrpg.db.cursor.execute("SELECT save FROM users WHERE id=" + str(msg['from_id']))
        save = vkrpg.db.cursor.fetchone()[0]

        if menu_item_select == 1:
            vkrpg.chat.apisay(str(save['inventory']), msg['peer_id'])
        elif menu_item_select == 2:
            if len(save['servants']) != 0:
                out = '[ System ] Ваши слуги:\n'
                for name, obj in save['servants'].items():
                    out += name + ' - HP: ' + str(obj['hp']) + ' | ATK: ' + str(obj['atk']) + '\n'
                vkrpg.chat.apisay(out, msg['peer_id'])
            else:
                out = '[ System ] У тебя нет слуг. Обратись к Ассоциации Магов через команду "старт"'
                vkrpg.chat.apisay(out, msg['peer_id'])
        elif menu_item_select == 3:
            vkrpg.contexts.enable_context(msg['from_id'], 'menu_main')
            for f in vkrpg.events.get_events('on_enablecontext', 'menu_main'):
                f(msg)


    def enablecontext(self, msg):
        menu_list = [
            {'title': 'Предметы', 'context': 'menu_inventory'},
            {'title': 'Слуги', 'context': 'menu_inventory'},
            {'title': 'В главное меню', 'context': 'menu_main'}
        ]

        out = '[ System ] Выберете пункт меню (цифра или название):\n'
        for idx, item in enumerate(menu_list):
            out += str(idx+1) + ' - ' + item['title'] + '\n'
        vkrpg.chat.apisay(out, msg['peer_id'])

vkrpg.plugins.register_plugin('menu_inventory', MenuInventory())