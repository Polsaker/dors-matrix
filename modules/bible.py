from nio import MatrixRoom

from dors import command_hook, Jenny, HookMessage
import requests


@command_hook(['bible'])
async def bible(bot: Jenny, room: MatrixRoom, event: HookMessage):
    verse = event.args[0] + '%20' + event.args[1]
    # TODO: USE ASYNC!
    i = requests.get('https://labs.bible.org/api/?passage=' + verse + '&type=json').json()
    res = ''
    for v in i:
        res += " {0}: {1}".format(v['verse'], v['text'])
    resp = "{0}".format(res)

    if len(resp) > 370:
        resp = resp[:370] + '... >> https://labs.bible.org/api/?passage=' + verse

    await bot.message(room.room_id, resp[1:])


@command_hook(['quran', 'Quran'])
async def quran(bot: Jenny, room: MatrixRoom, event: HookMessage):
    verse = event.args[0]
    i = requests.get('https://api.alquran.cloud/ayah/' + verse + '/en.asad').json()
    if i['code'] == 200:
        resp = "{0}".format(i['data']['text'])
    else:
        resp = "{0}".format(i['data'])
    if len(resp) > 370:
        resp = resp[:370] + '...'

    await bot.message(room.room_id, resp)
