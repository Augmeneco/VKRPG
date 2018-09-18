import re

class KBotPermissionsPlugin:
    def __init__(self):
        vkrpg.perms = self.Permissions()

    class Permissions:
        perms_tree = {'childs': {}, 'cmds': []}

        def on_load(self):
            for i, v in vkrpg.chat.cmds_list.items():
                perms_tree_node = vkrpg.perms.perms_tree
                for perm in v['perms'].split('.'):
                    if perm not in perms_tree_node['childs']:
                        perms_tree_node['childs'][perm] = {'childs': {}, 'cmds': []}
                    perms_tree_node = perms_tree_node['childs'][perm]
                perms_tree_node['cmds'].append(i)

        def on_preparemessage(self, msg):
            available_cmds = []
            for v in msg['db_acc']['permissions']:
                perms_tree_node = self.perms.perms_tree
                prev_perms_tree_node = perms_tree_node
                for idx, perm in enumerate(v.split('.')):
                    if perm == '*':

                        def perms_tree_search(perms_tree_node):
                            available_cmds.extend(perms_tree_node['cmds'])
                            for val in perms_tree_node['childs']:
                                perms_tree_search(perms_tree_node['childs'][val])

                        perms_tree_search(prev_perms_tree_node)
                        break
                    perms_tree_node = perms_tree_node['childs'][perm]
                    prev_perms_tree_node = perms_tree_node
                available_cmds.extend(perms_tree_node['cmds'])
            # https://stackoverflow.com/questions/3040716/python-elegant-way-to-check-if-at-least-one-regex-in-list-matches-a-string

            if not any(
                    re.match(v['tmplt'], msg['text'][len(PREFIX) + 1:]) for i, v in self.chat.cmds_list.items()
                    if i in available_cmds):
                vkrpg.chat.apisay('У вас нету доступа к этой команде!', msg['peer_id'], msg['id'])
                return False


vkrpg.plugins.register_plugin('kbot_permissions', KBotPermissionsPlugin())