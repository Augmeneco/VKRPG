# VKRPG

VKRPG является context-event-driven (Контекстно-Событийным) движком.
Контекст - это окружение состоящее из событий и переменных которые могут устонавливаться для одного или более пользователя. Контексты также могут иметь копии.

## ScriptAPI
### EventsAPI
vkrpg.events.add_event(event: string, f: function, contextid='default': string) - добавляет функцию f к событию event контекста contextid
vkrpg.events.remove_event(event: string, f: function, contextid='default': string) - удаляет функцию f к событию event контекста contextid
vkrpg.events.get_events(event: string, contextid='default': string) - получить список функций к событию event контекста contextid

### ContextsAPI
vkrpg.contexts.create_context(contextid: string) - создать пустой контекст c именем contextid. Вернёт новый контекст
vkrpg.contexts.create\_context\_copy(contextid) - создать копию контекста по contextid. Вернёт имя копии
vkrpg.contexts.enable\_context(vkid, contextid, obj\_for_event=None) - включить созданый контекст с именем contextid для vkid 
vkrpg.contexts.get\_contextid\_by_vkid(vkid) - получить включённый контекст у vkid
vkrpg.contexts.get_context(contextid) - получить объект контекста по его имени
vkrpg.contexts.

### ChatAPI
vkrpg.chat.actions\_display(actions\_list, peer\_id, title=None) - показать меню представленное списком actions_list (вида [{'title': 'пункт1'}, {'title': 'пункт1'}]) в чат peer\_id с заголовком title. Чтобы после выбора пункта меню оно пропало надо добавить в объект пункта one\_time=True.
vkrpg.chat.actions\_select(actions_list, msg) - обработка сообщения msg для выявления ответа на пункт меню actions\_list