from datetime import datetime


def log_print(text, type='info'):
    print('[' + datetime.now().strftime("%H:%M:%S") + '] ' + text)
