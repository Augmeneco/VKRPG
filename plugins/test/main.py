class TestPlugin:
    def __init__(self):
        self.os = __import__('os')
        vkrpg.commands.register_command('hello', 'hello', self.hello)
    
    def hello(self):
        vkrpg.commands.register_command('huy', 'huy a{3}', self.hello)
    
    def bye(self):
        vkrpg.commands.unregister_command('huy a{3}')


vkrpg.plugins.register_plugin('test', TestPlugin())