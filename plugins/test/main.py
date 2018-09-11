class TestPlugin:
    def __init__(self):
        self.os = __import__(os)
        vkrpg.register_command('hello', self.hello)
    
    def hello(self):
        vkrpg.register_command('huy a{3}', self.hello)
    
    def bye(self):
        vkrpg.unregister_command('huy a{3}')


vkrpg.register_plugin('test', TestPlugin())