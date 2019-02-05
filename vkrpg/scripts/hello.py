import vkrpg

class MainContext(vkrpg.contexts.BaseContext):
    def on_message(self, msg):
        vkrpg.chat.send(msg['peer_id'], text='Привет, VKID#{}!'.format(msg['from_id']))
        