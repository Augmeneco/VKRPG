class TestPlugin:
    def __init__(self):
        self.os = __import__('os')
        vkrpg.events.add_event('on_message', self.hello)
    
    def hello(self, msg):
        vkrpg.chat.apisay('ПРИВЕТ МИР! Напиши своё имя:', msg['peer_id'], msg['id'])
        # for msg in vkrpg.chat.start_scan(msg['from_id']):
        #     name = msg['text']
        #     vkrpg.chat.stop_scan(msg['from_id'])
        name = vkrpg.chat.scan(msg['from_id'])['text']
        vkrpg.chat.apisay('Привет, ' + name + '!', msg['peer_id'], msg['id'])

vkrpg.plugins.register_plugin('test', TestPlugin())