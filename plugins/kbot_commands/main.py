class KBotCommandsPlugin:
    def __init__(self):
        vkrpg.chat.cmds_list = {}

    def register_command(self, name, template, func):
        vkrpg.chat.cmds_list[name] = [template, func]

    def unregister_command(self, name):
        del vkrpg.chat.cmds_list[name]


vkrpg.plugins.register_plugin('kbot_commands', KBotCommandsPlugin())