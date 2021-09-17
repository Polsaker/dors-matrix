# Ported from jenni (yanosbot)
from collections import defaultdict

from nio import MatrixRoom

from dors import message_hook, Jenny, HookMessage
import config

import random
import re
import openai

openai.api_key = config.openai_api_key

start_sequence = "\nJenny:"

response = openai.Completion.create(
  engine="davinci",
  prompt="You're talking to Phuks, a chat group full of random people. Your job is to be of use.",
  temperature=0.9,
  max_tokens=150,
  top_p=1,
  frequency_penalty=0,
  presence_penalty=0.6,
  stop=["\n"]
)

mycb = {}

nowords = ['reload', 'help', 'tell', 'ask', 'ping']

r_entity = re.compile(r'&[A-Za-z0-9#]+;')
HTML_ENTITIES = { 'apos': "'" }
noun = ['ZHVjaw==', 'Y2F0', 'ZG9n', 'aHVtYW4=',]
r_entity = re.compile(r'\|[0-9A-F#]{,4}')
random.seed()


channel_histories = defaultdict(list)
sources = []


@message_hook(".+")
async def random_chat(bot: Jenny, room: MatrixRoom, event: HookMessage):
    bad_chans = fchannels()
    if bad_chans and room.room_id in bad_chans:
        return

    text = event.body.strip()

    if event.body.startswith(config.nick):
        text = " ".join(text.split(" ")[1:])

    channel_histories[room.room_id].append(f"{await bot.get_displayname(event.sender)}: {text}")
    if len(channel_histories[room.room_id]) > 15:
        channel_histories[room.room_id].pop(0)

    trigger = random.random() <= (1 / 2500.0) or config.nick.lower() in event.body.lower() or \
              "jen" in event.body.lower()

    if not trigger:
        return

    await bot.room_read_markers(room.room_id, event.event_id, event.event_id)
    await bot.room_typing(room.room_id, True, 10000)

    prompt = f"Your name is {config.nick}. You are a cheerful robot in a room with strange people\n\n"
    prompt += "\n".join(channel_histories[room.room_id])
    prompt += "\nJenny:"

    response = openai.Completion.create(
        engine="davinci",
        prompt=prompt,
        temperature=0.9,
        max_tokens=150,
        top_p=1,
        frequency_penalty=0,
        presence_penalty=0.6,
        stop=["\n"]
    )
    print(prompt)
    print(response)
    reply = response['choices'][0]['text'].strip()
    await bot.room_typing(room.room_id, False)
    channel_histories[room.room_id].append(f"{config.nick}: {reply}")
    if len(channel_histories[room.room_id]) > 15:
        channel_histories[room.room_id].pop(0)

    await bot.message(room.room_id, reply)


def fchannels():
    try:
        f = open('nochannels.txt', 'r')
    except:
        return False
    lines = f.readlines()[0]
    f.close()
    lines = lines.replace('\n', '')
    return lines.split(',')
