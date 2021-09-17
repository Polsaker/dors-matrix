from nio import MatrixRoom

from dors import command_hook, HookMessage, Jenny
import re
import requests

# Ported from jenni

exp = re.compile(r'</a></span>(.+)</li>')


@command_hook(['pun', 'badpun'], help="Gives a bad pun.")
async def puns(bot: Jenny, room: MatrixRoom, event: HookMessage):
    url = 'https://pun.me/random/'
    page = requests.get(url).content.decode()

    result = exp.search(page)
    if result:
        pun = result.groups()[0]
        return await bot.say(pun)
    else:
        return await bot.say("I'm afraid I'm not feeling punny today!")
