import vkrpg
import lanode
import json
import random

def contextnotfound(msg, broken_contextid):
    lanode.vk_api('messages.send', {'v': '5.92',
                                    'peer_id': msg['peer_id'],
                                    'random_id': random.randint(0, 9223372036854775807),
                                    'message': 'Выполняю команду ' + str(0),
                                    'keyboard': json.dumps({"buttons": [], "one_time": True})}, vkrpg.CONFIG['token'])
    vkrpg.contexts.enable_context(msg['from_id'], 'menu_main', msg)


vkrpg.events.add_event('on_contextnotfound', contextnotfound)