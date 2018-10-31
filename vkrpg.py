import queue
import json
import requests
import threading
import time
import lanode
import psycopg2
import importlib
import importlib.util
import psycopg2.extras
from datetime import datetime
import os
import html
import sys
from ruamel.yaml import YAML


with open('config.yml') as config_file:
    yaml = YAML()
    CONFIG = yaml.load(config_file.read())


updates_queue = queue.Queue()


def start():
    sys.dont_write_bytecode = True
    lanode.log_print('Инициализация плагинов-скриптов...', 'info')
    # for script in filter(lambda x: x.split('.')[-1] == 'py', os.listdir('./scripts')):
    #     exec(open('./scripts/' + script).read())
    for plugin in [x for x in os.listdir('./scripts/') if not os.path.isdir('./scripts/' + x)]:
        spec = importlib.util.spec_from_file_location(plugin.split('.')[0], './scripts/' + plugin)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        plugins.plugins_list[plugin] = module

    for f in events.get_events('on_load'):
        f()

    print(contexts.context_list)

    lanode.log_print('Инициализация плагинов-скриптов завершена.', 'info')

    lanode.log_print('Запуск longpoll потока ...', 'info')
    thread_longpoll = threading.Thread(target=longpollserver)
    thread_longpoll.start()
    lanode.log_print('Longpoll поток запущен.', 'info')

    while True:
        time.sleep(10/1000000.0)

        if not updates_queue.empty():
            update = updates_queue.get()

            if update['type'] == 'message_new':
                msg = update['object']

                lanode.log_print('(MsgID: ' + str(msg['id']) + ') Получено. '
                                 '{SndTime: ' + datetime.fromtimestamp(msg['date']).strftime('%Y.%m.%d %H:%M:%S') + ','
                                 ' Chat: ' + str(msg['peer_id']) + ','
                                 ' From: ' + str(msg['from_id']) + ','
                                 ' Text: "' + msg['text'].replace('\n', '\\n') + '"}',
                                 'info')

                if 'db' in globals():
                    res = db.read('users', "id='"+str(update['object']['from_id'])+"'")
                    if res == []:
                        db.write('users', [(str(update['object']['from_id']), '{}', '{"context":"default","inventory":[],"servants":{}}')])
                        res = db.read('users', "id='" + str(update['object']['from_id']) + "'")

                    msg['db'] = res[0]
                else:
                    if msg['from_id'] in contexts.users_contexts:
                        contexts.enable_context(msg['from_id'], 'default')

                msg['context'] = contexts.get_context(msg['from_id'])

                for f in events.get_events('on_rawmessage', msg['context']):
                    f(update)

                if (msg['peer_id'] > 0) and (msg['peer_id'] < 2000000000):
                    chat_type = 'private'
                elif (msg['peer_id'] > 0) and (msg['peer_id'] > 2000000000):
                    chat_type = 'dialog'
                elif msg['peer_id'] < 0:
                    chat_type = 'group_private'

                msg['chat_type'] = chat_type
                msg['text'] = html.unescape(msg['text'])

                if msg['chat_type'] == 'dialog':
                    if msg['text'].split(' ')[0] in ('кб', 'kb'):
                        msg['pure_text'] = ' '.join(msg['text'].split(' ')[1:]).lower()
                    else:
                        continue
                else:
                    msg['pure_text'] = msg['text']

                # if not any(re.match(x['tmplt'], msg['pure_text']) for x in self.chat.cmds_list.values()):
                #     self.chat.apisay('Такой команды не существует!', msg['peer_id'], msg['id'])
                #     continue

                for f in events.get_events('on_preparemessage', msg['context']):
                    msg = f(msg)
                    if msg is False:
                        break
                if msg is False:
                    continue
                    
                if msg['from_id'] in chat.scanning_users:
                    for q in chat.scanning_users[msg['from_id']].values():
                        q.put(msg)
                else:
                    for f in events.get_events('on_message', msg['context']):
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

    def add_event(self, event, f, context='default'):
        contexts.context_list[context]['events'][event].append(f)

    def remove_event(self, event, f, context='default'):
        contexts.context_list[context]['events'][event].remove(f)

    def get_events(self, event, context='default'):
        return contexts.context_list[context]['events'][event]

    # def longpoll(self, lp_event=None):
    #     if lp_event == None:
    #         pass


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

    def print(self, toho, mess=None, pics=None, torep=None):
        ret = requests.get(
            'https://api.vk.com/method/photos.getMessagesUploadServer?access_token={access_token}&v=5.68'.format(
                access_token=CONFIG['token'])).json()
        for pic in pics:
            ret = requests.post(ret['response']['upload_url'], files={'file1': pic}).json()
        ret = requests.get('https://api.vk.com/method/photos.saveMessagesPhoto?v=5.68&album_id=-3&server=' + str(
            ret['server']) + '&photo=' + ret['photo'] + '&hash=' + str(ret['hash']) + '&access_token=' + CONFIG['token']).text
        ret = json.loads(ret)
        requests.get('https://api.vk.com/method/messages.send?attachment=photo' + str(
            ret['response'][0]['owner_id']) + '_' + str(
            ret['response'][0]['id']) + '&message=' + mess + '&v=5.68&peer_id=' + str(
            toho) + '&access_token=' + str(CONFIG['token']))

    def apisay(self, text, toho):
        lanode.log_print(' Отправлено. '
                         '{SndTime: ' + datetime.now().strftime('%Y.%m.%d %H:%M:%S') + ','
                         ' Chat: ' + str(toho) + ','
                         ' Text: "' + text.replace('\n', '\\n') + '"}',
                         'info')
        param = {'v': '5.68', 'peer_id': toho, 'access_token': CONFIG['token'], 'message': text}
        result = requests.post('https://api.vk.com/method/messages.send', data=param)
        return result.text

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

class Contexts:
    context_list = {}

    def __init__(self):

        self.create_context('default')
        if 'db' in globals():
            self.users_contexts = {}

    def create_context(self, name):
        self.context_list[name] = {'events': {'on_message': [],
                                              'on_rawmessage': [],
                                              'on_preparemessage': [],
                                              'on_load': [],
                                              'on_enablecontext': []},
                                   'vars': {}}

    def enable_context(self, vk_id, context_id):
        if context_id in self.context_list:
            if 'db' in globals():
                res = db.read('users', 'id=' + str(vk_id))[0]
                res['save']['context'] = context_id
                db.replace('users', 'id=' + str(vk_id), "save='" + json.dumps(res['save']) + "' ")
            else:
                self.users_contexts[vk_id] = context_id
        
        else:
            return None

    def get_context(self, vk_id):
        if 'db' in globals():
            res = db.read('users', 'id=' + str(vk_id))[0]
            if res['save']['context'] in self.context_list:
                return res['save']['context']
            else:
                return None
        else:
            if vk_id in self.users_contexts:
                return self.users_contexts[vk_id]
            else:
                return None

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