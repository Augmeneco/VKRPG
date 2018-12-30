import vkrpg
import requests 
import random
import json
import sqlite3


class GraalContext(vkrpg.contexts.BaseContext):
    menu_list = [
        {'title': 'ролл', 'one_time': False},
        {'title': 'Улучшения', 'one_time': False},
        {'title': 'В главное меню', 'one_time': True}
    ]


    def on_message(self, msg):
        if msg['pure_text'].lower() in ('меню'):
            vkrpg.chat.actions_display(self.menu_list, msg['peer_id'])
            return
        menu_item_select = vkrpg.chat.actions_select(self.menu_list, msg)

        if menu_item_select == 0:
            #vkrpg.chat.apisay('йух', msg['peer_id'])
            username = requests.post('https://api.vk.com/method/users.get',
            data={'access_token': vkrpg.CONFIG['token'], 'v': '5.84', 'user_ids': msg['from_id']}).json()
            username = username['response'][0]['first_name'] + ' ' + username['response'][0]['last_name']

            out = '*'+username+' встаёт к кругу призыва и произносит заклинание:*'
            vkrpg.chat.apisay(out, msg['peer_id'])

            servtext = json.loads(open('data/text.json', 'r').read())
            userserv = random.choice(list(dict(servtext).keys()))
            userservdb = userserv
            userservdb = list(userservdb)
            userservdb[0] = list(userservdb)[0].capitalize()
            userservdb = ''.join(userservdb)
            servtext = servtext[userserv]
            vkrpg.chat.apisay(servtext, msg['peer_id'])
            conn = sqlite3.connect('data/fate.db')
            cursor = conn.cursor()
            print(userservdb)
            servlist = cursor.execute('SELECT * FROM servants WHERE class="' + userservdb + '"').fetchall()
            servlist = random.choice(servlist)
            out = 'Поздравляю! Ты призвал слугу класса '+userservdb+' по имени '+servlist[0]+'\n\
                       Уровень здоровья: '+str(servlist[2])+'\n\
                       Наносимый урон: '+str(servlist[4])+'\n\
                       Наносимый урон Небесным Фантазмом: '+str(servlist[6])
            vkrpg.chat.send(msg['peer_id'], text=out, photos=[open('data/servants/' + servlist[8], 'rb')])

            with vkrpg.db.transaction():
                user = vkrpg.db[msg['peer_id']]
                user['save']['inventory']['servants'][servlist[0]] = {'hp':servlist[2],'atk':servlist[4],'np':servlist[6],'class':userservdb}
                vkrpg.db[msg['peer_id']] = user

        elif menu_item_select == 1:
            pass

        elif menu_item_select == 2:
            vkrpg.contexts.get_context('MenuMainContext').enable_for_vkid(msg['from_id'], msg)


    def on_enablecontext(self, msg):
        vkrpg.chat.actions_display(self.menu_list, msg['peer_id'])