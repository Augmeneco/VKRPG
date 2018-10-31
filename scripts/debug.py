import vkrpg
from io import StringIO
import contextlib
import sys


def on_preparemessage(msg):
	if msg['pure_text'].split(' ')[0].lower() in ('debug'):
		code = ' '.join(msg['pure_text'].split(' ')[1:])
		
		@contextlib.contextmanager
		def stdoutIO(stdout=None):
			old = sys.stdout
			if stdout is None:
				stdout = StringIO()
			sys.stdout = stdout
			yield stdout
			sys.stdout = old

		with stdoutIO() as s:
			try:
				exec(code, globals(), locals())
			except Exception as e:
				vkrpg.chat.apisay(str(e), msg['peer_id'])
				
			vkrpg.chat.apisay(s.getvalue(), msg['peer_id'])

		return False
	else:
		return msg


def on_load():
	for c in vkrpg.contexts.context_list.values():
		c['events']['on_preparemessage'].append(on_preparemessage)
		
vkrpg.events.add_event('on_load', on_load)