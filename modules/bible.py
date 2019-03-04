from dors import commandHook
import requests


@commandHook(['bible', 'Bible'])
def bible(irc, ev):
    verse = ev.args[0] + '%20' + ev.args[1]
    i = requests.get('http://labs.bible.org/api/?passage=' + verse + '&type=json').json()
    res = ''
    for v in i:
        res += " {0}: {1}".format(v['verse'], v['text'])
    resp = "{0}".format(res)

    if len(resp) > 370:
        resp = resp[:370] + '... >> http://labs.bible.org/api/?passage=' + verse

    irc.message(ev.replyto, resp[1:])


@commandHook(['quran', 'Quran'])
def quran(irc, ev):
    verse = ev.args[0]
    i = requests.get('http://api.alquran.cloud/ayah/' + verse + '/en.asad').json()
    if i['code'] == 200:
        resp = "{0}".format(i['data']['text'])
    else:
        resp = "{0}".format(i['data'])
    if len(resp) > 370:
        resp = resp[:370] + '...'

    irc.message(ev.replyto, resp)
