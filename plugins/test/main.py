class TestPlugin:
    def __init__(self):
        self.os = __import__('os')
        self.commands = {'hello': {'tmplt': 'hello', 'perms': 'testplug.hello', 'func': self.on_hello},
                    'huy': {'tmplt': 'huy a{3}', 'perms': 'testplug', 'func': self.bye}}
        vkrpg.chat.contexts.create_context('test', ['hello'], 'blacklist')
    
    def on_hello(self, msg):
        vkrpg.chat.apisay('ПРИВЕТ МИР!', msg['peer_id'], msg['id'])
    
    def bye(self, msg):
        print('bye')


vkrpg.plugins.register_plugin('test', TestPlugin())