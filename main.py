import queue
import json
import requests
import threading
import time
import lanode
import psycopg2
import psycopg2.extras
import re
import os
import html


print(os.path.dirname(__file__))

TOKEN = 'fa11495759265b5b4c681fdb9cb063b5d7aba22c760406ac021592e4df3de8f7e3be3383c026495cbe3a5'

PREFIX = 'кб'


class VKRPG:
    updates_queue = queue.LifoQueue()

    def __init__(self):
        self.chat = self.Chat()
        self.plugins = self.Plugins()
        self.perms = self.Permissions()
        self.db = self.DB("dbname=fatedb user=postgres password=psql host=127.0.0.1")

    def start(self):
        lanode.log_print('Инициализация плагинов...', 'info')
        for plugin in os.listdir('./plugins'):
            exec(open('./plugins/' + plugin + '/main.py').read())

        for i,v in self.chat.commands_list.items():
            perms_tree_node = self.perms.perms_tree
            for perm in v['perms'].split('.'):
                if perm not in perms_tree_node['childs']:
                    perms_tree_node['childs'][perm] = {'childs':{}, 'cmds':[]}
                perms_tree_node = perms_tree_node['childs'][perm]
            perms_tree_node['cmds'].append(i)

        lanode.log_print('Инициализация плагинов завершена.', 'info')

        lanode.log_print('Запуск longpoll потока ...', 'info')
        thread_longpoll = threading.Thread(target=self.longpollserver)
        thread_longpoll.start()
        lanode.log_print('Longpoll поток запущен.', 'info')

        print(self.chat.commands_list)
        print(self.perms.perms_tree)

        while True:
            time.sleep(10/1000000.0)

            if not self.updates_queue.empty():
                update = self.updates_queue.get()

                if update['type'] == 'message_new':
                    msg = update['object']
                    msg['text'] = html.unescape(msg['text'])

                    res = self.db.read('users', "id='"+str(update['object']['from_id'])+"'")
                    if res == []:
                        self.db.write('users', [(str(update['object']['from_id']), 'nickname', '{}', '{}', '{}')])
                        res = self.db.read('users', "id='" + str(update['object']['from_id']) + "'")
                    msg['db_acc'] = res[0]
                    print(msg)

                    ### СДЕЛАТЬ ПРОВЕРКУ НА ПЕРМИШЕНСЫ!!!

                    for k,v in self.chat.commands_list.items():
                        if re.match(self.chat.commands_list[k]['tmplt'], update['object']['text'][len(PREFIX)+1:]) != None:
                            thread = threading.Thread(target=self.chat.commands_list[k]['func'], args=(msg,))
                            thread.setName(str(update['object']['id']))
                            thread.start()
                            print(self.chat.commands_list)

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
            vkrpg.chat.commands_list.update(obj.commands)

        # def unregister_plugin(self, name):
        #     del self.plugins_list[name]


    class Chat:
        commands_list = {}

        # def register_command(self, name, template, func):
        #     self.commands_list[name] = [template, func]

        # def unregister_command(self, name):
        #     del self.commands_list[name]

        def say(pic, mess, toho):
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

        def apisay(text, toho, torep):
            param = {'v': '5.68', 'peer_id': toho, 'access_token': TOKEN, 'message': text, 'forward_messages': torep}
            result = requests.post('https://api.vk.com/method/messages.send', data=param)
            return result.text

        def sendpic(pic, mess, toho):
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


    class Permissions:
        perms_tree = {'childs':{}, 'cmds': []}


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

