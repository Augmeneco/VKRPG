import vkrpg
from io import StringIO
import contextlib
import sys


def on_preparemessage(msg):
	if msg['pure_text'].split(' ')[0].lower() in ('debug'):

		return False
	else:
		return msg


def on_load():
	for c in vkrpg.contexts.context_list.values():
		c['events']['on_preparemessage'].append(on_preparemessage)
		
vkrpg.events.add_event('on_load', on_load)