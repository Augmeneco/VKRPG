import vkrpg
import time
import threading
import queue


class BattleLobbyContext(vkrpg.contexts.BaseContext):
    def on_message(self, msg):
        pass


    def on_enablecontext(self, args):
        msg = args[0]
        vkrpg.chat.apisay('[ System ] Ищу вам противника...', msg['peer_id'])
        context = vkrpg.contexts.get_context('battle_lobby')
        context['vars']['waitqueue'].put(msg['from_id'])
        timer = time.time()
        while (timer - time.time()) <= 5:
            time.sleep(10 / 1000000.0)
            with lock_lobby_queues:
                for x in output_lobby_queue:
                    if msg['from_id'] in x[0]:
                        if not x[1][0]:
                            x[1][0] = True
                        else:
                            x[1][1] = True
                for x in final_lobby_queue.copy():
                    if msg['from_id'] in x[0]:
                        if not x[1]:
                            x[1] = True
                        else:
                            final_lobby_queue.remove(x)

        else:
            vkrpg.chat.apisay('[ System ] Я не смогла найти вам противника.\n'
                              'Пожалуйста приходите позже. Или же вы можете сразиться с MasterAI.', msg['peer_id'])
            vkrpg.contexts.remove_context(args[1])
            vkrpg.contexts.enable_context(msg['from_id'], 'menu_main', msg)
            return

        vkrpg.chat.apisay('[ System ] Запускаю сражение...', msg['peer_id'])
        vkrpg.chat.apisay('[ System ] Загружаю противника... Загружен', msg['peer_id'])
        vkrpg.db.cursor.execute("SELECT save FROM users WHERE id=" + str(enemy_vkid))
        save_enemy = vkrpg.db.cursor.fetchone()[0]
        vkrpg.chat.apisay('[ System ] Загружаю вас... Загружен', msg['peer_id'])
        vkrpg.db.cursor.execute("SELECT save FROM users WHERE id=" + str(msg['from_id']))
        save = vkrpg.db.cursor.fetchone()[0]
        vkrpg.chat.apisay('[ System ] Загружаю слуг и магию... Загружен', msg['peer_id'])

        vkrpg.chat.apisay('[ System ] Сражение запущено.', msg['peer_id'])


    input_lobby_queue = queue.Queue()
    output_lobby_queue = []
    final_lobby_queue = []
    lock_lobby_queues = threading.Lock()

    def lobbyserver(self):
        if not input_lobby_queue.empty():
            with lock_lobby_queues:
                enemy1 = input_lobby_queue.get()
                enemy2 = input_lobby_queue.get()
                output_lobby_queue.append([(enemy1, enemy2), [False, False], time.time()])
                for i in output_lobby_queue:
                    if (sum(i[1]) == 2) or ((time.time() - i[2]) < 5):
                        copyid = vkrpg.contexts.create_context_copy('battle_lobby')
                        final_lobby_queue.append([(enemy1, enemy2), False, copyid])