from datetime import datetime
import requests


def log_print(text, type='info'):
    print('[' + datetime.now().strftime("%H:%M:%S") + '] ' + text)


def vk_api(method, parameters, token):
    url = 'https://api.vk.com/method/' + method
    headers = {
        'User-Agent': 'KateMobileAndroid/45 lite-421 (Android 5.0; SDK 21; armeabi-v7a; LENOVO Lenovo A1000; ru)'
    }
    parameters['access_token'] = token
    if parameters['v'] is None:
        parameters['v'] = '5.74'

    # if method.split('.')[1][:3] == 'get':
    r = requests.post(url, params=parameters, headers=headers)

    return r.json()


def tg_api(method, parameters, token, file=None):
    url = 'https://api.telegram.org/bot' + token + '/' + method
    headers = {}
    parameters['parse_mode'] = 'markdown'
    parameters['disable_web_page_preview'] = True

    # if method.split('.')[1][:3] == 'get':
    if file == None:
        r = requests.post(url, params=parameters, headers=headers)
    else:
        r = requests.post(url, params=parameters, headers=headers, files={'file': file})
    # print(r.text)
    return r.json()


def chunks(l, n):
    """Yield successive n-sized chunks from l."""
    for i in range(0, len(l), n):
        yield l[i:i + n]