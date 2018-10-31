import vkrpg
import requests 
import random
import json
import sqlite3

def main(msg):
	print(1)
	if msg['pure_text'].lower() == 'хуй':
		vkrpg.chat.apisay('соси хуй', msg['peer_id'])
		# username = req.post('https://api.vk.com/method/users.get',
		# data={'access_token': vkrpg.TOKEN, 'v': '5.84', 'user_ids': msg['from_id']}).json()
		# username = username['response'][0]['first_name'] + ' ' + username['response'][0]['last_name']

		# out = '*'+username+' встаёт к кругу призыва и произносит заклинание:*'
		# vkrpg.chat.apisay(out, msg['peer_id'])

		# servtext = json.loads(open('data/text.json', 'r').read())
		# userserv = random.choice(list(dict(servtext).keys()))
		# userservdb = userserv
		# userservdb = list(userservdb)
		# userservdb[0] = list(userservdb)[0].capitalize()
		# userservdb = ''.join(userservdb)
		# servtext = servtext[userserv]
		# vkrpg.chat.apisay(servtext, msg['peer_id'])
		# conn = sqlite3.connect('data/fate.db')
		# cursor = conn.cursor()
		# print(userservdb)
		# servlist = cursor.execute('SELECT * FROM servants WHERE class="' + userservdb + '"').fetchall()
		# servlist = random.choice(servlist)
		# print(servlist)
vkrpg.contexts.create_context('roll')
vkrpg.events.add_event('on_message', main, 'roll')