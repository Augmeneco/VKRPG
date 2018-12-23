import vkrpg
import requests 
import random
import json
import sqlite3


menu_list = [
    {'title': 'ролл', 'one_time': False},
    {'title': 'Улучшения', 'one_time': False},
    {'title': 'В главное меню', 'one_time': True}
]


def main(msg):
    if msg['pure_text'].lower() in ('меню'):
        vkrpg.chat.actions_display(menu_list, msg['peer_id'])
        return
    menu_item_select = vkrpg.chat.actions_select(menu_list, msg)
    
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
        vkrpg.chat.apisay(out, msg['peer_id'])
        vkrpg.db.cursor.execute("SELECT save FROM users WHERE id=" + str(msg['from_id']))
        save = vkrpg.db.cursor.fetchone()[0]
        save['inventory']['servants'][servlist[0]] = {'hp':servlist[2],'atk':servlist[4],'np':servlist[6],'class':userservdb}
        vkrpg.db.cursor.execute("UPDATE users SET save='" + json.dumps(save) + "' WHERE id=" + str(msg['from_id']))
        vkrpg.db.conn.commit()

    elif menu_item_select == 1:
        pass

    elif menu_item_select == 2:
        vkrpg.contexts.enable_context(msg['from_id'], 'menu_main', msg)


def enablecontext(msg):
    vkrpg.chat.actions_display(menu_list, msg['peer_id'])


vkrpg.contexts.create_context('graal')
vkrpg.events.add_event('on_message', main, 'graal')
vkrpg.events.add_event('on_enablecontext', enablecontext, 'graal')