import vkrpg


def on_load():
    pass


def on_evloopiter():
    pass


def on_newuser(vkid):
    with vkrpg.db.transaction():
        inventory = vkrpg.db[vkid]
        inventory['save']['inventory']['servants'] = {}
        vkrpg.db[vkid] = inventory


def on_contextnotfound(msg, broken_context):
    c = vkrpg.contexts.get_context('MainContext')
    c.enable_for_vkid(msg['from_id'])


class MainContext(vkrpg.contexts.BaseContext):
    def on_message(self, msg):
        print('sosi pisu')
        print(msg)