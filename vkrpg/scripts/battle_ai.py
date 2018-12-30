import vkrpg
import random
import sqlite3
import json


class BattleAIContext(vkrpg.contexts.BaseContext):
    ai_servants = {}
    player_servants = {}

    def on_message(self, msg):
        enemy_for_atk = vkrpg.chat.actions_select([{'title': x, 'one_time': True} for x in self.ai_servants], msg)
        # damage = random.randint(100, self.player_servants[])
        vkrpg.chat.apisay('[ System ] Сервант противника '+str(enemy_for_atk)+' атакован', msg['peer_id'])

        player_for_atk = random.choice(list(x[0] for x in enumerate(self.player_servants)))
        vkrpg.chat.apisay('[ System ] Сервант игрока ' + str(player_for_atk) + ' атакован', msg['peer_id'])

        vkrpg.chat.actions_display([{'title': x, 'one_time': True} for x in self.ai_servants], msg['peer_id'],
                                   '[ System ] Выберите слугу противника для атаки')


    def on_enablecontext(self, msg):
        #"Nero Claudius (Bride)": {"hp": 2089, "atk": 1793, "np": 12706, "class": "Saber"}
        vkrpg.chat.apisay('[ System ] Запускаю сражение...', msg['peer_id'])

        vkrpg.chat.apisay('[ System ] Загружаю MasterAI... Загружен', msg['peer_id'])
        for i in range(3):
            servtext = json.loads(open('data/text.json', 'r').read())
            userserv = random.choice(list(dict(servtext).keys()))
            userservdb = userserv
            userservdb = list(userservdb)
            userservdb[0] = list(userservdb)[0].capitalize()
            userservdb = ''.join(userservdb)
            conn = sqlite3.connect('data/fate.db')
            cursor = conn.cursor()
            print(userservdb)
            servlist = cursor.execute('SELECT * FROM servants WHERE class="' + userservdb + '"').fetchall()
            servlist = random.choice(servlist)
            self.ai_servants[servlist[0]] = {'class': userservdb, 'name': servlist[0], 'hp': servlist[2], 'atk': servlist[4], 'np': servlist[6]}

        vkrpg.chat.apisay('[ System ] Загружаю вас... Загружен', msg['peer_id'])
        user = vkrpg.db[msg['peer_id']]
        self.player_servants = user['inventory']['servants']

        vkrpg.chat.apisay('[ System ] Загружаю слуг и магию... Загружен', msg['peer_id'])

        vkrpg.chat.apisay('[ System ] Сражение запущено.', msg['peer_id'])

        vkrpg.chat.actions_display([{'title': x, 'one_time': True} for x in self.ai_servants], msg['peer_id'],
                                   '[ System ] Выберите слугу противника для атаки')