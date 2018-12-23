import queue
import json
import requests
import threading
import time
import lanode
import copy
import psycopg2
import importlib
import importlib.util
import random
import psycopg2.extras
from datetime import datetime
import os
import html
import re
import sys
from ruamel.yaml import YAML


with open('config.yml') as config_file:
    yaml = YAML()
    CONFIG = yaml.load(config_file.read())

debug_func = lambda x: x

updates_queue = queue.Queue()


def start():
    lanode.log_print('Инициализация плагинов-скриптов...', 'info')
    # for script in filter(lambda x: x.split('.')[-1] == 'py', os.listdir('./scripts')):
    #     exec(open('./scripts/' + script).read())
    for plugin in [x for x in os.listdir('./scripts/') if not os.path.isdir('./scripts/' + x) or x[-3] == '.py']:
        spec = importlib.util.spec_from_file_location(plugin.split('.')[0], './scripts/' + plugin)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        plugins.plugins_list[plugin[:-3]] = module

    for f in events.get_events('on_load'):
        f()

    if CONFIG['debug'] is True:
        print(os.path.dirname(__file__))
        print(plugins.plugins_list)
        print(contexts.context_list)

    lanode.log_print('Инициализация плагинов-скриптов завершена.', 'info')

    lanode.log_print('Запуск longpoll потока ...', 'info')
    thread_longpoll = threading.Thread(target=longpollserver)
    thread_longpoll.start()

    while True:
        time.sleep(10/1000000.0)

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

                if (msg['pure_text'].split(' ')[0].lower() in ('debug', 'dbg', 'дбг', 'дебаг')) and (debug_func is not None):
                    debug_func(msg)
                    continue

                lanode.log_print('(MsgID: ' + str(msg['id']) + ') Получено. '
                                 '{SndTime: ' + datetime.fromtimestamp(msg['date']).strftime('%Y.%m.%d %H:%M:%S') + ','
                                 ' Chat: ' + str(msg['peer_id']) + ','
                                 ' From: ' + str(msg['from_id']) + ','
                                 ' Text: "' + msg['text'].replace('\n', '\\n') + '"}',
                                 'info')

                if 'db' in globals():
                    res = db.read('users', "id='"+str(update['object']['from_id'])+"'")
                    if res == []:
                        db.write('users', [(str(update['object']['from_id']), '{}', '{"context":"default","inventory":{"servants":{}}}')])
                        res = db.read('users', "id='" + str(update['object']['from_id']) + "'")
                        for f in events.get_events('on_newuser'):
                            f(msg)
                    msg['db'] = res[0]
                else:
                    if msg['from_id'] not in contexts.users_contexts:
                        contexts.enable_context(msg['from_id'], 'default')

                if contexts.get_context(contexts.get_contextid_by_vkid(msg['from_id'])) is None:
                    lanode.log_print('ERROR: Контекста не существует. Chat: ' + str(msg['peer_id']) + ' From: ' + str(
                        msg['from_id']), 'info')
                    for f in events.get_events('on_contextnotfound'):
                        f(msg, contexts.get_contextid_by_vkid(msg['from_id']))
                    continue

                for f in events.get_events('on_rawmessage', contexts.get_contextid_by_vkid(msg['from_id'])):
                    f(update)

                # if not any(re.match(x['tmplt'], msg['pure_text']) for x in self.chat.cmds_list.values()):
                #     self.chat.apisay('Такой команды не существует!', msg['peer_id'], msg['id'])
                #     continue

                for f in events.get_events('on_preparemessage', contexts.get_contextid_by_vkid(msg['from_id'])):
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
                    for f in events.get_events('on_message', contexts.get_contextid_by_vkid(msg['from_id'])):
                        thread = threading.Thread(target=f, args=(msg,))
                        thread.setName(str(msg['id']))
                        thread.start()

def longpollserver():
    def get_lp_server():
        lp_info = requests.post('https://api.vk.com/method/groups.getLongPollServer',
                                data={'access_token': CONFIG['token'], 'v': '5.80', 'group_id': '171173780'})
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


class Plugins:
    plugins_list = {}

    def register_plugin(self, name, obj):
        self.plugins_list[name] = obj

    # def unregister_plugin(self, name):
    #     del self.plugins_list[name]


class Events:
    # def execute_event(self, event):
    #     results = []
    #     for f in vars(self)[event]:
    #         results.append(f())
    #     return results

    def add_event(self, event, f, contextid='default'):
        contexts.get_context(contextid)['events'][event].append(f)

    def remove_event(self, event, f, contextid='default'):
        contexts.get_context(contextid)['events'][event].remove(f)

    def get_events(self, event, contextid='default'):
        return contexts.get_context(contextid)['events'][event]

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

    def __init__(self):
        self.create_context('default')
        if 'db' in globals():
            self.users_contexts = {}

    def create_context(self, contextid):
        context = {'events': {'on_message': [],
                              'on_rawmessage': [],
                              'on_preparemessage': [],
                              'on_load': [],
                              'on_enablecontext': [],
                              'on_disablecontext': [],
                              'on_timer': [],
                              'on_evloopiter': [],
                              'on_contextnotfound': []},
                   'vars': {},
                   'copies': {},
                   'childs': {}}
        self.context_list[contextid] = context
        return context

    def create_context_copy(self, contextid):
        if contextid.split(':')[0] in self.context_list:
            context_copy = {i:copy.deepcopy(self.context_list[contextid][i])
                            for i in self.context_list[contextid]
                            if i not in ('childs', 'copies')}
            copy_id = len(self.context_list[contextid]['copies'])
            self.context_list[contextid]['copies'][copy_id] = context_copy
            return contextid + ':' + str(copy_id), context_copy

    def enable_context(self, vkid, contextid, obj_for_event=None):
        if contextid.split(':')[0] in self.context_list:
            if 'db' in globals():
                res = db.read('users', 'id=' + str(vkid))[0]
                contextid_old = res['save']['context']
                res['save']['context'] = contextid
                db.replace('users', 'id=' + str(vkid), "save='" + json.dumps(res['save']) + "' ")
            else:
                contextid_old = self.users_contexts[vkid]
                self.users_contexts[vkid] = contextid

            if self.get_context(contextid_old) is not None:
                for f in self.get_context(contextid_old)['events']['on_disablecontext']:
                    f(obj_for_event)
            for f in self.get_context(contextid)['events']['on_enablecontext']:
                f(obj_for_event)

            return True

        else:
            return False

    def get_contextid_by_vkid(self, vkid):
        if 'db' in globals():
            res = db.read('users', 'id=' + str(vkid))[0]
            return res['save']['context']
        else:
            return self.users_contexts[vkid]

    def get_context(self, contextid):
        if contextid.split(':')[0] in self.context_list:
            if len(contextid.split(':')) == 1:
                return self.context_list[contextid]
            elif len(contextid.split(':')) == 2:
                if int(contextid.split(':')[1]) in self.context_list[contextid.split(':')[0]]['copies']:
                    return self.context_list[contextid.split(':')[0]]['copies'][int(contextid.split(':')[1])]
                else:
                    return None
        else:
            return None

    def remove_context(self, contextid):
        if contextid.split(':')[0] in self.context_list:
            if len(contextid.split(':')) == 1:
                del self.context_list[contextid]
                return True
            elif len(contextid.split(':')) == 2:
                del self.context_list[contextid.split(':')[0]]['copies'][int(contextid.split(':')[1])]
                return True
            else:
                return False
        else:
            return False


class Chat:
    scanning_users = {}

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

    def send(self, toho, mess=None, pics=None, torep=None):
        r = requests.get(
            'https://api.vk.com/method/photos.getMessagesUploadServer?access_token={}&v=5.68'.format(CONFIG['token'])).json()
        for pic in pics:
            ret = requests.post(r['response']['upload_url'], files={'file': pic}).json()
            ret = requests.get('https://api.vk.com/method/photos.saveMessagesPhoto?v=5.68&album_id=-3&server=' + str(
                ret['server']) + '&photo=' + ret['photo'] + '&hash=' + str(ret['hash']) + '&access_token=' + CONFIG['token']).json()
        requests.get('https://api.vk.com/method/messages.send?attachment=photo' + str(
            ret['response'][0]['owner_id']) + '_' + str(
            ret['response'][0]['id']) + '&message=' + mess + '&v=5.68&peer_id=' + str(
            toho) + '&access_token=' + str(CONFIG['token']))

    def apisay(self, text, toho):
        param = {'v': '5.68', 'peer_id': toho, 'access_token': CONFIG['token'], 'message': text}
        result = requests.post('https://api.vk.com/method/messages.send', data=param).json()
        # lanode.log_print('(MsgID: ' + str(result['response']) + ') Отправлено. '
        #                  '{SndTime: ' + datetime.now().strftime('%Y.%m.%d %H:%M:%S') + ','
        #                  ' Chat: ' + str(toho) + ','
        #                  ' Text: "' + text.replace('\n', '\\n') + '"}',
        #                  'info')
        return result

    def sendpic(self, pic, mess, toho):
        ret = requests.get(
            'https://api.vk.com/method/photos.getMessagesUploadServer?access_token={access_token}&v=5.68'.format(
                access_token=CONFIG['token'])).json()
        with open(pic, 'rb') as f:
            ret = requests.post(ret['response']['upload_url'], files={'file1': f}).text
        ret = json.loads(ret)
        ret = requests.get('https://api.vk.com/method/photos.saveMessagesPhoto?v=5.68&album_id=-3&server=' + str(
            ret['server']) + '&photo=' + ret['photo'] + '&hash=' + str(ret['hash']) + '&access_token=' + CONFIG['token']).text
        ret = json.loads(ret)
        requests.get('https://api.vk.com/method/messages.send?attachment=photo' + str(
            ret['response'][0]['owner_id']) + '_' + str(
            ret['response'][0]['id']) + '&message=' + mess + '&v=5.68&peer_id=' + str(
            toho) + '&access_token=' + str(CONFIG['token']))

    def actions_display(self, actions_list, peer_id, title=None):
        if title is None:
            out = '[ System ] Выберете действие (цифра, название или кнопка):\n'
        else:
            out = title + '\n'

        for idx, item in enumerate(actions_list):
            out += str(idx + 1) + ' - ' + item['title'] + '\n'

        if peer_id > 2000000000:
            chat.apisay(out, peer_id)
        elif (peer_id > 0) and (peer_id < 2000000000):
            keyboard_obj = {'one_time': False, 'buttons': []}
            for menu_list_chunk in lanode.chunks(list(enumerate(actions_list)), 4):
                keyboard_obj['buttons'].append(list([{'color': 'default',
                                                      'action': {
                                                          'type': 'text',
                                                          'payload': '{\"button\": \"' + str(x[0]) + '\"}',
                                                          'label': x[1]['title']
                                                      }} for x in menu_list_chunk]))
            lanode.vk_api('messages.send', {'v': '5.92',
                                            'peer_id': peer_id,
                                            'random_id': random.randint(0, 9223372036854775807),
                                            'message': out,
                                            'keyboard': json.dumps(keyboard_obj, ensure_ascii=False)}, CONFIG['token'])

    def actions_select(self, actions_list, msg):
        if msg['pure_text'].isdigit():
            if len(actions_list) + 1 >= int(msg['pure_text']):
                menu_item_select = int(msg['pure_text']) - 1
            else:
                out = '[ System ] Такого пункта меню не существует. Напиши "меню" чтоб узнать какие пункты существуют.'
                chat.apisay(out, msg['peer_id'])
                return
        elif 'payload' in msg:
            menu_item_select = int(json.loads(msg['payload'])['button'])
        else:
            menu_item = list([item for item in actions_list if item['title'].lower() == msg['pure_text'].lower()])
            if menu_item != []:
                menu_item_select = list([idx for idx, item in enumerate(actions_list)
                                         if item['title'].lower() == msg['pure_text'].lower()])[0]
            else:
                out = '[ System ] Такого пункта меню не существует. Напиши "меню" чтоб узнать какие пункты существуют.'
                chat.apisay(out, msg['peer_id'])
                return
        print(actions_list)
        print(menu_item_select)
        if (msg['chat_type'] == 'private') and ('one_time' in actions_list[menu_item_select]):
            if actions_list[menu_item_select]['one_time']:
                lanode.vk_api('messages.send', {'v': '5.92',
                                                'peer_id': msg['peer_id'],
                                                'random_id': random.randint(0, 9223372036854775807),
                                                'message': 'Выполняю команду '+str(menu_item_select),
                                                'keyboard': json.dumps({"buttons":[],"one_time":True})}, CONFIG['token'])
        return menu_item_select


class DB:
    def __init__(self, conn_str):
        self.conn = psycopg2.connect(conn_str)
        self.cursor = self.conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    def create(self, table, data):
        self.cursor.execute("""CREATE TABLE """ + table + """
                                (""" + data + """)""")
        self.conn.commit()

    def read(self, table, data):
        sql = "SELECT * FROM " + table + " WHERE " + data
        self.cursor.execute(sql)
        return self.cursor.fetchall()

    def write(self, table, data):
        val = '(' + '%s,' * len(data[0]) + ')'
        val = val.replace(',)', ')')
        self.cursor.executemany("INSERT INTO " + table + " VALUES " + val, data)
        self.conn.commit()

    def replace(self, table, where, setd):
        sql = """
        UPDATE """ + table + """
        SET """ + setd + """ 
        WHERE """ + where
        self.cursor.execute(sql)
        self.conn.commit()

    def remove(self, table, data):
        sql = "DELETE FROM " + table + " WHERE " + data
        self.cursor.execute(sql)

        self.conn.commit()

chat = Chat()
contexts = Contexts()
plugins = Plugins()
events = Events()
if CONFIG['standart_db']['use_db'] is True:
    db = DB('dbname={} user={} password={} host={}'.format(CONFIG['standart_db']['dbname'],
                                                           CONFIG['standart_db']['user'],
                                                           CONFIG['standart_db']['password'],
                                                           CONFIG['standart_db']['host']))