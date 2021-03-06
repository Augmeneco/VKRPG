# TODO: Счётчики принятых и отправленных сообщений

import queue
import json
import requests
import collections
import threading
import time
import lanode
import _io
import importlib
import importlib.util
import random
from unqlite import UnQLite
from datetime import datetime
import os
import html
import re
from ruamel.yaml import YAML
try:
    import vk_api
except ImportError:
    pass

with open('config.yml', errors='ignore') as config_file:
    yaml = YAML()
    CONFIG = yaml.load(config_file.read())

counters = {'msg_send': {'all': 0, 'hour': 0, 'hour_peer': {}},
            'msg_recv': {'all': 0, 'hour': 0, 'hour_peer': {}}}

debug_func = lambda x: x

updates_queue = queue.Queue()


def start():
    lanode.log_print('Инициализация скриптов...', 'info')
    # for script in filter(lambda x: x.split('.')[-1] == 'py', os.listdir('./scripts')):
    #     exec(open('./scripts/' + script).read())
    for script in [x for x in os.listdir('./scripts/') if (not os.path.isdir('./scripts/' + x)) and (x[-3:] == '.py')]:
        spec = importlib.util.spec_from_file_location(script.split('.')[0], './scripts/' + script)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        scripts.scripts_list[script[:-3]] = module

    contexts.context_list = {x.__name__: {'class': x, 'copies': {0: x(0)}} for x in contexts.BaseContext.__subclasses__()}

    for f in events.get_events('on_load'):
        f()

    if CONFIG['debug'] is True:
        print(os.path.dirname(__file__))
        print(scripts.scripts_list)
        print(contexts.context_list)

    lanode.log_print('Инициализация скриптов завершена.', 'info')

    lanode.log_print('Запуск longpoll потока ...', 'info')
    thread_longpoll = threading.Thread(target=longpollserver)
    thread_longpoll.start()

    hour_timer = datetime.now().hour
    while True:
        time.sleep(10/1000000.0)

        if datetime.now().hour > hour_timer:
            counters['msg_recv']['hour'] = 0
            counters['msg_send']['hour'] = 0
            counters['msg_recv']['hour_peer'] = {}
            counters['msg_send']['hour_peer'] = {}

        for f in events.get_events('on_evloopiter'):
            f()

        for t in events.get_events('on_timer').copy():
            if t[3] >= time.time():
                if t[1]:
                    t[0](t)
                    events.get_events('on_timer').remove(t)
                else:
                    t[0](t)
                    t[2] = time.time()

                # timers = events.get_events('on_timer').copy()
        # i = 0
        # while i <= len(timers):
        #     t = timers[i]
        #     if t[0]:
        #         t[3]()
        #         events.get_events('on_timer').remove(t)
        #     else:
        #         t[3]()
        #         t[1] =
        #     i += 1


        if not updates_queue.empty():
            update = updates_queue.get()
            if CONFIG['debug'] is True:
                print(update)

            if update['type'] == 'message_new':
                msg = update['object']

                counters['msg_recv']['all'] += 1
                counters['msg_recv']['hour'] += 1
                if msg['peer_id'] in counters['msg_recv']['hour_peer']:
                    counters['msg_recv']['hour_peer'][msg['peer_id']] += 1
                else:
                    counters['msg_recv']['hour_peer'][msg['peer_id']] = 0

                if (msg['peer_id'] > 0) and (msg['peer_id'] < 2000000000):
                    chat_type = 'private'
                elif msg['peer_id'] > 2000000000:
                    chat_type = 'dialog'
                elif msg['peer_id'] < 0:
                    chat_type = 'group_private'

                msg['chat_type'] = chat_type
                if 'text' in msg:
                    msg['text'] = html.unescape(msg['text'])
                else:
                    msg['text'] = ''

                if msg['text'].split(' ')[0] in CONFIG['prefixes']:
                    msg['pure_text'] = ' '.join(msg['text'].split(' ')[1:]).lower()
                elif re.search(r'(\[club(\d+)\|\s*\S+\s*\]).*', msg['text']) is not None:
                    match = re.findall(r'(\[club(\d+)\|\s*\S+\s*\]).*', msg['text'])[0]
                    if int(match[1]) == CONFIG['group_id']:
                        msg['pure_text'] = msg['text'].replace(match[0]+' ', '')
                    else:
                        if msg['chat_type'] == 'private':
                            msg['pure_text'] = msg['text']
                        else:
                            continue
                else:
                    if msg['chat_type'] == 'private':
                        msg['pure_text'] = msg['text']
                    else:
                        continue

                if (msg['pure_text'].split(' ')[0].lower() in ('debug', 'dbg', 'дбг', 'дебаг'))\
                    and (debug_func is not None)\
                    and (msg['from_id'] in CONFIG['admins']):
                    debug_func(msg)
                    continue

                lanode.log_print('(MsgID: ' + str(msg['id']) + ') Получено. '
                                 '{SndTime: ' + datetime.fromtimestamp(msg['date']).strftime('%Y.%m.%d %H:%M:%S') + ','
                                 ' Chat: ' + str(msg['peer_id']) + ','
                                 ' From: ' + str(msg['from_id']) + ','
                                 ' Text: "' + msg['text'].replace('\n', '\\n') + '"}',
                                 'info')
                # with db.transaction():
                #     if msg['from_id'] not in db:
                #         db[msg['from_id']] = {'settings': {},
                #                               'save': {'context':'MainContext','inventory':{}}}
                #         for f in events.get_events('on_newuser'):
                #             f(msg['from_id'])

                context = contexts.get_context_by_vkid(msg['from_id'])

                if context is None:
                    lanode.log_print('ERROR: Контекста не существует. Chat: ' + str(msg['peer_id']) + ' From: ' + str(
                        msg['from_id']), 'info')
                    for f in events.get_events('on_contextnotfound'):
                        f(msg, contexts.get_contextid_by_vkid(msg['from_id']))
                    continue


                context.on_rawmessage(update)

                # if not any(re.match(x['tmplt'], msg['pure_text']) for x in self.chat.cmds_list.values()):
                #     self.chat.apisay('Такой команды не существует!', msg['peer_id'], msg['id'])
                #     continue

                for f in events.get_events('on_preparemessage'):
                    msg = f(msg)
                    if msg is False:
                        break
                if msg is False:
                    continue

                if CONFIG['debug'] is True:
                    print(msg)

                if msg['from_id'] in chat.scanning_users:
                    for q in chat.scanning_users[msg['from_id']].values():
                        q.put(msg)
                else:
                    print(id(msg))
                    thread = threading.Thread(target=context.on_message, args=(msg,))
                    thread.setName(str(msg['id']))
                    thread.start()

def longpollserver():
    def get_lp_server():
        lp_info = requests.post('https://api.vk.com/method/groups.getLongPollServer',
                                data={'access_token': CONFIG['token'], 'v': '5.80', 'group_id': CONFIG['group_id']})
        if CONFIG['debug']:
            print(lp_info.text)
        lp_info = json.loads(lp_info.text)['response']
        lanode.log_print('Новая информация о longpoll сервере успешно получена','info')
        return lp_info

    lp_info = get_lp_server()
    lanode.log_print('Longpoll поток запущен.', 'info')
    while True:
        time.sleep(10 / 1000000.0)
        lp_url = lp_info['server'] + '?act=a_check&key=' + lp_info['key'] + '&ts=' + \
                 str(lp_info['ts']) + '&wait=60'
        result = json.loads(requests.get(lp_url).text)
        try:
            lp_info['ts'] = result['ts']
            for update in result['updates']:
                updates_queue.put(update)
        except KeyError:
            lp_info = get_lp_server()

def stat():
    print()


try:
    vk_api
except NameError:
    pass
else:
    vk_session = vk_api.VkApi(token=CONFIG['token'])
    vk = vk_session.get_api()
    lanode.log_print('Бибилиотека vk_api успешно загружена.')


class Scripts:
    scripts_list = {}

    # def register_plugin(self, name, obj):
    #     self.plugins_list[name] = obj

    # def unregister_plugin(self, name):
    #     del self.plugins_list[name]


class Events:
    # def execute_event(self, event):
    #     results = []
    #     for f in vars(self)[event]:
    #         results.append(f())
    #     return results

    # def add_event(self, event, f):
    #     contexts.get_context(contextid)['events'][event].append(f)
    #
    # def remove_event(self, event, f):
    #     contexts.get_context(contextid)['events'][event].remove(f)

    def get_events(self, event):
        return [v for x in scripts.scripts_list.values() for n,v in x.__dict__.items() if n == event]

    # def add_timerevent(self, t, f, one_time=True):
    #     timer = [f, one_time, time.time(), t]
    #     contexts.get_context('default')['events']['on_timer'].append(timer)
    #     return timer
    #
    # def add_timerevent(self, t, f, one_time=True):
    #
    #     contexts.get_context(contextid)['events'][event].remove([x for x in contexts.get_context(contextid)['events'][event]
    #                                                          if x[0] == f][0])

    # def longpoll(self, lp_event=None):
    #     if lp_event == None:
    #         pass


class Contexts:
    context_list = {}

    def get_contextid_by_vkid(self, vkid):
        #lanode.vk_api('storage')
        with db.transaction():
            if vkid in db:
                return db[vkid]['save']['context']

    def get_context(self, contextid):
        if contextid.split(':')[0] in self.context_list:
            if len(contextid.split(':')) == 1:
                return self.context_list[contextid]['copies'][0]
            elif len(contextid.split(':')) == 2:
                if int(contextid.split(':')[1]) in self.context_list[contextid.split(':')[0]]['copies']:
                    return self.context_list[contextid.split(':')[0]]['copies'][int(contextid.split(':')[1])]
                else:
                    return None
        else:
            return None

    def get_context_by_vkid(self, vkid):
        with db.transaction():
            if vkid in db:
                return self.get_context(db[vkid]['save']['context'])

    # def remove_context(self, contextid):
    #     if contextid.split(':')[0] in self.context_list:
    #         if len(contextid.split(':')) == 1:
    #             del self.context_list[contextid]
    #             return True
    #         elif len(contextid.split(':')) == 2:
    #             del self.context_list[contextid.split(':')[0]]['copies'][int(contextid.split(':')[1])]
    #             return True
    #         else:
    #             return False
    #     else:
    #         return False

    class BaseContext:
        def __init__(self, copy_id):
            self.copy_id = copy_id

        def on_message(self, msg):
            pass

        def on_rawmessage(self, update):
            pass

        def on_enablecontext(self, payload):
            pass

        def on_disablecontext(self, payload):
            pass

        def enable_for_vkid(self, vkid, payload=None):
            if self.__class__.__name__ in contexts.context_list:
                with db.transaction():
                    contextid_old = db[vkid]['save']['context']
                    user = db[vkid]
                    user['save']['context'] = self.__class__.__name__ + ':' + str(self.copy_id)
                    db[vkid] = user

                if contexts.get_context(contextid_old) is not None:
                    contexts.get_context(contextid_old).on_disablecontext(payload)
                self.on_enablecontext(payload)

                return True

            else:
                return False

        def copy(self):
            x = contexts.context_list[self.__class__.__name__]
            x['copies'][len(x['copies'])] = self.__class__(len(x['copies']))
            return self.__class__.__name__+':'+str(len(x['copies'])-1), x['copies'][len(x['copies'])-1]

        def remove(self):
            if self.copy_id != 0:
                x = contexts.context_list[self.__class__.__name__]
                del x['copies'][self.copy_id]


class Chat:
    scanning_users = {}

    hide_keyboard_in_peers = []

    def scan(self, vkid):
        t_id = int(threading.current_thread().getName())
        self.scanning_users[vkid] = {}
        self.scanning_users[vkid][t_id] = queue.Queue()
        while True:
            time.sleep(10 / 1000000.0)
            if vkid in self.scanning_users:
                if not self.scanning_users[vkid][t_id].empty():
                    msg = self.scanning_users[vkid][t_id].get()
                    del self.scanning_users[vkid][t_id]
                    if self.scanning_users[vkid] == {}:
                        del self.scanning_users[vkid]
                    return msg
            else:
                return

    def start_scan(self, vkid):
        t_id = int(threading.current_thread().getName())
        self.scanning_users[vkid] = {}
        self.scanning_users[vkid][t_id] = queue.Queue()
        while True:
            time.sleep(10 / 1000000.0)
            if vkid in self.scanning_users:
                if not self.scanning_users[vkid][t_id].empty():
                    yield self.scanning_users[vkid][t_id].get()
            else:
                return

    def stop_scan(self, vkid):
        t_id = int(threading.current_thread().getName())
        del self.scanning_users[vkid][t_id]
        if self.scanning_users[vkid] == {}:
            del self.scanning_users[vkid]

    def send(self, peer_id, text=None, photos=None, forward=None):
        params = {'v': '5.68', 'peer_id': str(peer_id), 'access_token': CONFIG['token']}
        if text is not None:
            params['message'] = text
        if forward is not None:
            if not isinstance(forward, collections.Iterable):
                forward = list([forward])
            params['forward_messages'] = ','.join([str(x) for x in forward])
        if photos is not None:
            # if isinstance(photos, _io.BufferedReader):
            #     photos = list([photos])

            uploadserver_info = requests.get(
                'https://api.vk.com/method/photos.getMessagesUploadServer?peer_id={}&access_token={}&v=5.68'.format(
                    peer_id, CONFIG['token'])).json()['response']

            uploaded_photos_info = []
            for photo in photos:
                r = requests.post(uploadserver_info['upload_url'], files={'photo': photo}).json()
                uploaded_photos_info.append(r)

            uploaded_photos_ids = []
            for photo_info in uploaded_photos_info:
                r = requests.post('https://api.vk.com/method/photos.saveMessagesPhoto',
                                  data={'album_id': '-3',
                                        'server': photo_info['server'],
                                        'photo': photo_info['photo'],
                                        'hash': photo_info['hash'],
                                        'v': '5.68',
                                        'access_token': CONFIG['token']}).json()
                uploaded_photos_ids.append('photo'+str(r['response'][0]['owner_id'])+'_'+str(r['response'][0]['id']))

            params['attachment'] = ','.join(uploaded_photos_ids)

        if peer_id in self.hide_keyboard_in_peers:
            params['keyboard'] = json.dumps({"buttons":[],"one_time":True})
            self.hide_keyboard_in_peers.remove(peer_id)

        r = requests.post('https://api.vk.com/method/messages.send', data=params).json()
        if 'response' in r:
            counters['msg_send']['all'] += 1
            counters['msg_send']['hour'] += 1
            if peer_id in counters['msg_send']['hour_peer']:
                counters['msg_send']['hour_peer'][peer_id] += 1
            else:
                counters['msg_send']['hour_peer'][peer_id] = 0
        else:
            print(r)

    def apisay(self, text, toho):
        param = {'v': '5.68', 'peer_id': toho, 'access_token': CONFIG['token'], 'message': text}
        result = requests.post('https://api.vk.com/method/messages.send', data=param).json()
        # lanode.log_print('(MsgID: ' + str(result['response']) + ') Отправлено. '
        #                  '{SndTime: ' + datetime.now().strftime('%Y.%m.%d %H:%M:%S') + ','
        #                  ' Chat: ' + str(toho) + ','
        #                  ' Text: "' + text.replace('\n', '\\n') + '"}',
        #                  'info')
        return result

    def actions_display(self, actions_list, peer_id, title=None, disabled_actions=()):
        if title is None:
            out = '[ System ] Выберете действие (цифра, название или кнопка):\n'
        else:
            out = title + '\n'

        for idx, item in enumerate(actions_list):
            if idx not in disabled_actions:
                out += '{} - {}\n'.format(str(idx + 1), item['title'])
            else:
                out += '# {} - {} #\n'.format(str(idx + 1), item['title'])

        if peer_id > 2000000000:
            chat.apisay(out, peer_id)
        elif (peer_id > 0) and (peer_id < 2000000000):
            keyboard_obj = {'one_time': False, 'buttons': []}
            for menu_list_chunk in lanode.chunks(list(enumerate(actions_list)), 4):
                keyboard_obj['buttons'].append(list([{'color': 'default' if x[0] not in disabled_actions else 'negative',
                                                      'action': {
                                                          'type': 'text',
                                                          'payload': '{\"button\": \"' + str(x[0]) + '\"}',
                                                          'label': x[1]['title'] if x[0] not in disabled_actions else '# {} #'.format(x[1]['title']),
                                                      }} for x in menu_list_chunk]))
            r = lanode.vk_api('messages.send', {'v': '5.92',
                                                'peer_id': peer_id,
                                                'random_id': random.randint(0, 9223372036854775807),
                                                'message': out,
                                                'keyboard': json.dumps(keyboard_obj, ensure_ascii=False)}, CONFIG['token'])
            print(r)

    def actions_select(self, actions_list, msg, disabled_actions=()):
        if msg['pure_text'].isdigit():
            if len(actions_list) + 1 >= int(msg['pure_text']):
                menu_item_select = int(msg['pure_text']) - 1
            else:
                return None
        elif 'payload' in msg:
            if 'button' in json.loads(msg['payload']):
                menu_item_select = int(json.loads(msg['payload'])['button'])
        else:
            menu_item = list([item for item in actions_list if item['title'].lower() == msg['pure_text'].lower()])
            if menu_item != []:
                menu_item_select = list([idx for idx, item in enumerate(actions_list)
                                         if item['title'].lower() == msg['pure_text'].lower()])[0]
            else:
                return None

        if (msg['chat_type'] == 'private') and ('one_time' in actions_list[menu_item_select]):
            if actions_list[menu_item_select]['one_time']:
                self.actions_hide(msg['peer_id'])

        if menu_item_select in disabled_actions:
            return -menu_item_select
        else:
            return menu_item_select

    def actions_hide(self, peer_id):
        self.hide_keyboard_in_peers.append(peer_id)


class Inventory:
    def __getitem__(self, i):
        return json.loads(db[i])['inventory']

    def __setitem__(self, i, c):
        self.store(i, json.dumps(c))


#
# class DB:
#     def __init__(self, conn_str):
#         self.conn = psycopg2.connect(conn_str)
#         self.cursor = self.conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
#
#     def create(self, table, data):
#         self.cursor.execute("""CREATE TABLE """ + table + """
#                                 (""" + data + """)""")
#         self.conn.commit()
#
#     def read(self, table, data):
#         sql = "SELECT * FROM " + table + " WHERE " + data
#         self.cursor.execute(sql)
#         return self.cursor.fetchall()
#
#     def write(self, table, data):
#         val = '(' + '%s,' * len(data[0]) + ')'
#         val = val.replace(',)', ')')
#         self.cursor.executemany("INSERT INTO " + table + " VALUES " + val, data)
#         self.conn.commit()
#
#     def replace(self, table, where, setd):
#         sql = """
#         UPDATE """ + table + """
#         SET """ + setd + """
#         WHERE """ + where
#         self.cursor.execute(sql)
#         self.conn.commit()
#
#     def remove(self, table, data):
#         sql = "DELETE FROM " + table + " WHERE " + data
#         self.cursor.execute(sql)
#
#         self.conn.commit()


class DB(UnQLite):
    def __getitem__(self, i):
        return json.loads(self.fetch(i).decode())

    def __setitem__(self, i, c):
        self.store(i, json.dumps(c))
#
# class DB:
#     def __init__(self, db_file, parent):
#         self.db_file = db_file
#         self.parent = parent
#
#     def __getitem__(self, i):
#         with open('users.vrdb') as db_file:
#             for line in db_file:
#                 if int(line.split(' ', 1)[0]) == i:
#                     return json.loads(line.split(' ', 1)[1])
#
#     def __setitem__(self, i, c):
#         self.store(i, json.dumps(c))

# class DB:
#     tables = {}
#     uql_db = UnQLite('./users.uql')
#
#     def __init__(self):
#         self.tables['users'] = self.uql_db.collection('users')
#         if not self.tables['users'].exists():
#             self.tables['users'].create()
#
#         if CONFIG['debug'] is True:
#             print(dict(self.uql_db))
#
#     def __getitem__(self, i):
#         if i == 'users':
#             return self.Table(self, i)
#         else:
#             raise KeyError
#
#     def transaction(self):
#         return self.uql_db.transaction()
#
#     class Table:
#         def __init__(self, p, t):
#             self.parent = p
#             self.table = t
#
#         def decode(self, l):
#             if isinstance(l, list):
#                 return [self.decode(x) for x in l]
#             elif isinstance(l, dict):
#                 return {x: self.decode(y) for x, y in l}
#             else:
#                 return l.decode()
#
#         def __getitem__(self, i):
#             return self.decode(self.parent.tables[self.table].filter(lambda x: x['id'] == i)[0])
#
#         def __setitem__(self, i, c):
#             if self.parent.tables[self.table].filter(lambda x: x['id'] == i)[0] != []:
#                 self.parent.tables[self.table].update(i, c)
#             else:
#                 c['id'] = i
#                 self.parent.tables[self.table].store(c)

chat = Chat()
contexts = Contexts()
scripts = Scripts()
events = Events()
db = DB('./users.uql')

# db = UnQLite('./users.uql')
# users = db.collection('users')

# if CONFIG['standart_db']['use_db'] is True:
#     db = DB('dbname={} user={} password={} host={}'.format(CONFIG['standart_db']['dbname'],
#                                                            CONFIG['standart_db']['user'],
#                                                            CONFIG['standart_db']['password'],
#                                                            CONFIG['standart_db']['host']))
