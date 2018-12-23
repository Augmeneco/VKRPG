import vkrpg
import requests as req
import random
import json
import sqlite3


def main(msg):
    if 'payload' not in msg:
        msg['payload'] = '{"command":""}'
    if (msg['pure_text'].lower() == 'старт') or (json.loads(msg['payload'])['command'] == 'start'):
        # vkrpg.db.cursor.execute(
        #     'SELECT id FROM users WHERE id=' + str(msg['from_id']))
        # user = vkrpg.db.cursor.fetchone()
        # if user is not None:
        #     out = 'К твоему сожалению в Ассоциации Магов не глупцы работают. Второй раз бесплатный призыв ты не получишь'
        #     vkrpg.chat.apisay(out, msg['peer_id'])
        #     return

        out = '- Здравствуй, мастер. Готов ли ты принять участие в Войне Святого Грааля?'
        vkrpg.chat.apisay(out, msg['peer_id'])

        answer = vkrpg.chat.scan(msg['from_id'])['text'].lower()
        if answer not in ['да','yes','da','1','y']:
            out = '- Ну тогда пока.'
            vkrpg.chat.apisay(out, msg['peer_id'])
            return

        out = '''- Отлично. Теперь я ознакомлю тебя с сутью войны.\n
                     Война Святого Грааля — это состязание, в котором в серии сражений определяется владелец Святого Грааля. 
                     В прошлом было много конфликтов вокруг Святого Грааля, и эта Война также относится к ним, в центре которой 
                     — битвы до последней пары Мастера (обычно они — опытные маги) и Слуги (призванная в качестве фамильяра 
                     Героическая Душа), которая и получит Святой Грааль.'''
        vkrpg.chat.apisay(out, msg['peer_id'])

        out = '- Пришло время призыва твоего слуги. Слуги это Героические Души, классифицированные как фамильяры ' \
              'высочайшего ранга, связанные со своим Мастером.'
        vkrpg.chat.apisay(out, msg['peer_id'])

        out = '- Ты готов?'
        vkrpg.chat.apisay(out, msg['peer_id'])

        answer = vkrpg.chat.scan(msg['from_id'])['text'].lower()
        if answer not in ['да', 'yes', 'da', '1', 'y']:
            out = '- Ну если не хочешь, то приходи позже.'
            vkrpg.chat.apisay(out, msg['peer_id'])
            return

        username = req.post('https://api.vk.com/method/users.get',
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

        # !!! Сделать отправку картинки !!!
        out = 'Поздравляю! Ты призвал своего первого слугу класса '+userservdb+' по имени '+servlist[0]+'\n\
                   Уровень здоровья: '+str(servlist[2])+'\n\
                   Наносимый урон: '+str(servlist[4])+'\n\
                   Наносимый урон Небесным Фантазмом: '+str(servlist[6])
        vkrpg.chat.apisay(out, msg['peer_id'])

        vkrpg.db.cursor.execute("SELECT save FROM users WHERE id=" + str(msg['from_id']))
        save = vkrpg.db.cursor.fetchone()[0]
        save['inventory']['servants'][servlist[0]] = {'hp':servlist[2],'atk':servlist[4],'np':servlist[6],'class':userservdb}
        vkrpg.db.cursor.execute("UPDATE users "
                                "SET save='" + json.dumps(save) + "' "
                                                                       "WHERE id=" + str(msg['from_id']))
        vkrpg.db.conn.commit()

        vkrpg.contexts.enable_context(msg['from_id'], 'menu_main', msg)


vkrpg.events.add_event('on_message', main, 'default')