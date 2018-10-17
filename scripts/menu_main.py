class MenuMain:
    def __init__(self):
        self.req = __import__('requests')
        self.random = __import__('random')
        self.json = __import__('json')
        self.sqlite3 = __import__('sqlite3')
        vkrpg.contexts.create_context('menu_main')
        vkrpg.events.add_event('on_message', self.menu, 'menu_main')
        vkrpg.events.add_event('on_enablecontext', self.enablecontext, 'menu_main')

    def menu(self, msg):
        menu_list = [
            {'title': 'Задания', 'context': 'missions'},
            {'title': 'Сражения', 'context': 'battle'},
            {'title': 'Профиль', 'context': 'profile'},
            {'title': 'Инвентарь', 'context': 'menu_inventory'},
            {'title': 'Малый Грааль', 'context': 'graal'}
        ]

        if msg['pure_text'].lower() == 'меню':
            out = '[ System ] Выберете пункт меню (цифра или название):\n'
            for idx, item in enumerate(menu_list):
                out += str(idx+1) + ' - ' + item['title'] + '\n'
            vkrpg.chat.apisay(out, msg['peer_id'])

            return

        if msg['pure_text'].isdigit():
            if len(menu_list)+1 >= int(msg['pure_text']):
                vkrpg.contexts.enable_context(msg['from_id'], menu_list[int(msg['pure_text'])-1]['context'])
                for f in vkrpg.events.get_events('on_enablecontext', menu_list[int(msg['pure_text'])-1]['context']):
                    f(msg)
                return
            else:
                out = '[ System ] Такого пункта меню не существует. Напиши "меню" чтоб узнать какие пункты существуют.'
                vkrpg.chat.apisay(out, msg['peer_id'])
                return
        else:
            menu_item = list([item for item in menu_list if item['title'].lower() == msg['pure_text'].lower()])
            if menu_item != []:
                vkrpg.contexts.enable_context(msg['from_id'], menu_item[0]['context'])
                for f in vkrpg.events.get_events('on_enablecontext', menu_item[0]['context']):
                    f(msg)
                return
            else:
                out = '[ System ] Такого пункта меню не существует. Напиши "меню" чтоб узнать какие пункты существуют.'
                vkrpg.chat.apisay(out, msg['peer_id'])
                return


    def enablecontext(self, msg):
        menu_list = [
            {'title': 'Задания', 'context': 'missions'},
            {'title': 'Сражения', 'context': 'battle'},
            {'title': 'Профиль', 'context': 'profile'},
            {'title': 'Инвентарь', 'context': 'menu_inventory'},
            {'title': 'Малый Грааль', 'context': 'graal'}
        ]

        out = '[ System ] Выберете пункт меню (цифра или название):\n'
        for idx, item in enumerate(menu_list):
            out += str(idx + 1) + ' - ' + item['title'] + '\n'
        vkrpg.chat.apisay(out, msg['peer_id'])

vkrpg.plugins.register_plugin('menu_main', MenuMain())