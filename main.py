import queue
import json
import requests
import threading
import time
import lanode
import psycopg2
import psycopg2.extras
import re
from datetime import datetime
import os
import html

lanode.log_print('VKRPG v0.4 by Lanode (from Augmeneco)')

print(os.path.dirname(__file__))

TOKEN = 'fa11495759265b5b4c681fdb9cb063b5d7aba22c760406ac021592e4df3de8f7e3be3383c026495cbe3a5'

PREFIX = 'кб'

USE_DB = True


class VKRPG:
    updates_queue = queue.Queue()

    def __init__(self):
        self.chat = self.Chat()
        self.contexts = self.Contexts(self)
        self.plugins = self.Plugins()
        self.events = self.Events()
        if USE_DB is True:
            self.db = self.DB("dbname=fatedb user=postgres password=psql host=127.0.0.1")

    def start(self):
        lanode.log_print('Инициализация плагинов...', 'info')
        for plugin in os.listdir('./plugins'):
            exec(open('./plugins/' + plugin + '/main.py').read())

        for f in self.events.get_events('on_load'):
            f()

        lanode.log_print('Инициализация плагинов завершена.', 'info')

        lanode.log_print('Запуск longpoll потока ...', 'info')
        thread_longpoll = threading.Thread(target=self.longpollserver)
        thread_longpoll.start()
        lanode.log_print('Longpoll поток запущен.', 'info')

        while True:
            time.sleep(10/1000000.0)

            if not self.updates_queue.empty():
                update = self.updates_queue.get()

                if update['type'] == 'message_new':
                    msg = update['object']
                    if not hasattr(vkrpg, 'db'):
                        res = self.db.read('users', "id='"+str(update['object']['from_id'])+"'")
                        if res == []:
                            self.db.write('users', [(str(update['object']['from_id']), '%username%', '{}', '{}', '{"context":"default"}')])
                            res = self.db.read('users', "id='" + str(update['object']['from_id']) + "'")

                        msg['db_acc'] = res[0]
                    else:
                        if msg['from_id'] in self.contexts.users_contexts:
                            self.contexts.enable_context(msg['from_id'], 'default')

                    msg['context'] = self.contexts.get_context(msg['from_id'])

                    for f in self.events.get_events('on_rawmessage'):
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
                            msg['pure_text'] = ' '.join(msg['text'].split(' ')[1:])
                        else:
                            continue
                    else:
                        msg['pure_text'] = msg['text']

                    lanode.log_print('(CmdID: ' + str(msg['id']) + ') Получено. '
                                      '{SndTime: ' + datetime.fromtimestamp(msg['date']).strftime('%Y.%m.%d %H:%M:%S') + ','
                                      ' Chat: ' + str(msg['peer_id']) + ','
                                      ' From: ' + str(msg['from_id']) + ','
                                      ' Text: "' + msg['text'] + '"}',
                                      'info')

                    # if not any(re.match(x['tmplt'], msg['pure_text']) for x in self.chat.cmds_list.values()):
                    #     self.chat.apisay('Такой команды не существует!', msg['peer_id'], msg['id'])
                    #     continue

                    for f in self.events.get_events('on_preparemessage'):
                        msg = f(msg)
                        if msg is False:
                            continue

                    if msg['from_id'] in self.chat.scanning_users:
                        self.chat.scanning_users[msg['from_id']].put(msg)
                    else:
                        for f in self.events.get_events('on_message'):
                            thread = threading.Thread(target=f, args=(msg,))
                            thread.setName(str(msg['id']))
                            thread.start()

    def longpollserver(self):
        def get_lp_server():
            lp_info = requests.post('https://api.vk.com/method/groups.getLongPollServer',
                                data={'access_token': TOKEN, 'v': '5.80', 'group_id': '171173780'})
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
                    self.updates_queue.put(update)
            except KeyError:
                lp_info = get_lp_server()



    class Plugins:
        plugins_list = {}

        def register_plugin(self, name, obj):
            self.plugins_list[name] = obj

        # def unregister_plugin(self, name):
        #     del self.plugins_list[name]


    class Events:
        def __init__(self):
            self.events = {'on_message': [],
                           'on_rawmessage': [],
                           'on_preparemessage': [],
                           'on_load': []}

        # def execute_event(self, event):
        #     results = []
        #     for f in vars(self)[event]:
        #         results.append(f())
        #     return results

        def add_event(self, event, f):
            self.events[event].append(f)

        def remove_event(self, event, f):
            self.events[event].remove(f)

        def get_events(self, event, context='default'):
            if context == 'default':
                return self.events[event]
            else:
                return vkrpg.contexts.context_list[context]['events'][event]

        # def longpoll(self, lp_event=None):
        #     if lp_event == None:
        #         pass

        def set_context_event(self, context, event, func):
            vkrpg.contexts.context_list[context]['events'][event] = func

        def unset_context_event(self, context, event):
            del vkrpg.contexts.context_list[context]['events'][event]


    class Chat:
        scanning_users = {}

        def scan(self, vkid):
            self.scanning_users[vkid] = queue.Queue()
            while True:
                time.sleep(10 / 1000000.0)
                if vkid in self.scanning_users:
                    if not self.scanning_users[vkid].empty():
                        yield self.scanning_users[vkid].get()
                else:
                    return

        def stop_scan(self, vkid):
            del self.scanning_users[vkid]

        def print(self, pic, mess, toho, torep):
            ret = requests.get(
                'https://api.vk.com/method/photos.getMessagesUploadServer?access_token={access_token}&v=5.68'.format(
                    access_token=TOKEN)).json()
            with open(pic, 'rb') as f:
                ret = requests.post(ret['response']['upload_url'], files={'file1': f}).text
            ret = json.loads(ret)
            ret = requests.get('https://api.vk.com/method/photos.saveMessagesPhoto?v=5.68&album_id=-3&server=' + str(
                ret['server']) + '&photo=' + ret['photo'] + '&hash=' + str(ret['hash']) + '&access_token=' + TOKEN).text
            ret = json.loads(ret)
            requests.get('https://api.vk.com/method/messages.send?attachment=photo' + str(
                ret['response'][0]['owner_id']) + '_' + str(
                ret['response'][0]['id']) + '&message=' + mess + '&v=5.68&peer_id=' + str(
                toho) + '&access_token=' + str(TOKEN))

        def apisay(self, text, toho, torep):
            param = {'v': '5.68', 'peer_id': toho, 'access_token': TOKEN, 'message': text, 'forward_messages': torep}
            result = requests.post('https://api.vk.com/method/messages.send', data=param)
            return result.text

        def sendpic(self, pic, mess, toho):
            ret = requests.get(
                'https://api.vk.com/method/photos.getMessagesUploadServer?access_token={access_token}&v=5.68'.format(
                    access_token=TOKEN)).json()
            with open(pic, 'rb') as f:
                ret = requests.post(ret['response']['upload_url'], files={'file1': f}).text
            ret = json.loads(ret)
            ret = requests.get('https://api.vk.com/method/photos.saveMessagesPhoto?v=5.68&album_id=-3&server=' + str(
                ret['server']) + '&photo=' + ret['photo'] + '&hash=' + str(ret['hash']) + '&access_token=' + TOKEN).text
            ret = json.loads(ret)
            requests.get('https://api.vk.com/method/messages.send?attachment=photo' + str(
                ret['response'][0]['owner_id']) + '_' + str(
                ret['response'][0]['id']) + '&message=' + mess + '&v=5.68&peer_id=' + str(
                toho) + '&access_token=' + str(TOKEN))

    class Contexts:
        context_list = {}

        def __init__(self, vkrpg):
            self.create_context('default', {'events':{}})
            if not hasattr(vkrpg, 'db'):
                self.users_contexts = {}

        def create_context(self, name, cont_obj):
            self.context_list[name] = cont_obj

        def enable_context(self, vk_id, context_id):
            if hasattr(vkrpg, 'db'):
                res = vkrpg.db.read('users', 'id=' + str(vk_id))
                res['save']['context'] = context_id
                vkrpg.db.replace('users', "save='" + json.dumps(res['save']) + "'", 'id=' + str(vk_id))
            else:
                self.users_contexts[vk_id] = context_id

        def get_context(self, vk_id):
            if hasattr(vkrpg, 'db'):
                res = vkrpg.db.read('users', 'id=' + str(vk_id))[0]
                if res['save']['context'] in self.context_list:
                    return self.context_list[res['save']['context']]
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


if __name__ == "__main__":
    vkrpg = VKRPG()
    try:
        vkrpg.start()
    except KeyboardInterrupt:
        lanode.log_print('Получен сигнал завершения. Завершаю работу!', 'info')
        os._exit(0)

