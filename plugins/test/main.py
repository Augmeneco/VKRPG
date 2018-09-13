class TestPlugin:
    def __init__(self):
        self.os = __import__('os')
        self.commands = {'hello': {'tmplt': 'hello', 'perms': 'testplug.hello', 'func': self.hello},
                    'huy': {'tmplt': 'huy a{3}', 'perms': 'testplug', 'func': self.bye}}
    
    def hello(self, update):
        print('hello')
    
    def bye(self, update):
        print('bye')


vkrpg.plugins.register_plugin('test', TestPlugin())