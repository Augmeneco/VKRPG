class TestPlugin:
    def __init__(self):
        self.os = __import__('os')
        vkrpg.commands.register_command('hello', 'hello', self.hello)
    
    def hello(self, update):
        print('hello')
        vkrpg.commands.register_command('huy', 'huy a{3}', self.bye)
    
    def bye(self, update):
        print('bye')
        vkrpg.commands.unregister_command('huy')


vkrpg.plugins.register_plugin('test', TestPlugin())