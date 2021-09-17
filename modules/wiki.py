from nio import MatrixRoom

from dors import command_hook, Jenny, HookMessage
import requests
import re


@command_hook(['wiki'])
async def wikipedia(bot: Jenny, room: MatrixRoom, event: HookMessage):
    term = '+'.join(str(x) for x in event.args)
    url = f"https://en.wikipedia.org/w/api.php?action=query&prop=extracts&exintro=&titles={term}&format=json" \
          f"&exsentences=3&redirects"
    resp = requests.get(url).json()
    tmp = str(resp['query']['pages'])
    pageid = tmp.split(':', 1)[0]
    pageid = re.findall(r'\d+', pageid)[0]
    message = resp['query']['pages'][pageid]['extract'].strip()
    link = '_'.join(str(x) for x in event.args)
    flink = 'https://en.wikipedia.org/wiki/' + link

    await bot.message(room.room_id, message + '\n' + flink, p_html=True)


@command_hook(['wikisearch'])
async def wikipediasearch(bot: Jenny, room: MatrixRoom, event: HookMessage):
    term = '+'.join(str(x) for x in event.args)
    url = f"https://en.wikipedia.org/w/api.php?action=query&list=search&srsearch={term}&utf8=&format=json"
    resp = requests.get(url).json()
    message = ''
    for entry in resp['query']['search'][0:5]:
        link = re.sub(' ', '_', entry['title'])
        message += 'https://en.wikipedia.org/wiki/' + link + ' | '
    await bot.reply(message[0:-3])
