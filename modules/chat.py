# Ported from jenni (yanosbot)
from collections import defaultdict

from nio import MatrixRoom

from dors import message_hook, Jenny, HookMessage
import config
import time

import random
import re
import openai

openai.api_key = config.openai_api_key

start_sequence = "\nJenny:"

mycb = {}

nowords = ['reload', 'help', 'tell', 'ask', 'ping']

r_entity = re.compile(r'&[A-Za-z0-9#]+;')
HTML_ENTITIES = { 'apos': "'" }
noun = ['ZHVjaw==', 'Y2F0', 'ZG9n', 'aHVtYW4=',]
r_entity = re.compile(r'\|[0-9A-F#]{,4}')
random.seed()
last_trigger = defaultdict(lambda: 0)


channel_histories = defaultdict(list)
sources = []


@message_hook(".+")
async def random_chat(bot: Jenny, room: MatrixRoom, event: HookMessage):
    bad_chans = fchannels()
    if bad_chans and room.room_id in bad_chans:
        return

    text = event.sane_body.strip()

    # if event.body.startswith(config.nick):
    #     text = " ".join(text.split(" ")[1:])

    dn = await bot.get_displayname(event.sender)
    if not getattr(dn, "displayname", False) or len(dn.displayname) > 16:
        dn = event.sender[1:].split(":")[0]
    else:
        dn = dn.displayname
    channel_histories[room.room_id].append(f"<{dn}> {text}")
    if len(channel_histories[room.room_id]) > 15:
        channel_histories[room.room_id].pop(0)

    trigger = random.random() <= (1 / 2500.0) or config.nick.lower() in event.sane_body.lower() or \
              "jen" in event.sane_body.lower()

    a = lambda x: min(80, (100/x)+(x**-2)*20000)
    dice = random.randrange(0, 10000) / 100

    trigger = trigger or dice < (a(time.time() - last_trigger[room.room_id]))
    if not trigger:
        return

    await bot.room_read_markers(room.room_id, event.event_id, event.event_id)
    await send_chat_msg(bot, room)


async def send_chat_msg(bot: Jenny, room: MatrixRoom):
    await bot.room_typing(room.room_id, True, 10000)
    prompt = f"{config.prompt}\n\n"
    prompt += "\n".join(channel_histories[room.room_id])
    prompt += "\n<Jenny>"

#    prompts = [{"role": "system", "content": config.prompt}]
#    prompts += [{"role": "user", "content": config.prompt}]
#    prompts += channel_histories[room.room_id]

    response = openai.Completion.create(
        engine="davinci",
        prompt=prompt,
        temperature=0.9,
        max_tokens=500,
        top_p=1,
        frequency_penalty=0.7,
        presence_penalty=0.5,
        stop=["\n", "<Jenny>"]
#         messages=prompts
    )
    print(prompt)
    print(response)
    reply = response['choices'][0]['text'].strip()
    await bot.room_typing(room.room_id, False)
    channel_histories[room.room_id].append(f"<Jenny> {reply}")
    if len(channel_histories[room.room_id]) > 10:
        channel_histories[room.room_id].pop(0)
    last_trigger[room.room_id] =  time.time()
    await bot.message(room.room_id, reply)
    if random.randint(0, 10) == 0:
        await send_chat_msg(bot, room)


def fchannels():
    try:
        f = open('nochannels.txt', 'r')
    except:
        return False
    lines = f.readlines()[0]
    f.close()
    lines = lines.replace('\n', '')
    return lines.split(',')
