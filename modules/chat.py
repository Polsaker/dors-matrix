# Ported from jenni (yanosbot)

from dors import stuffHook
import config

from cleverwrap import CleverWrap
from html.entities import name2codepoint
import json
from urllib.parse import quote

import random
import re
import time
import base64

mycb = {}

nowords = ['reload', 'help', 'tell', 'ask', 'ping']

r_entity = re.compile(r'&[A-Za-z0-9#]+;')
HTML_ENTITIES = { 'apos': "'" }
noun = ['ZHVjaw==', 'Y2F0', 'ZG9n', 'aHVtYW4=',]
r_entity = re.compile(r'\|[0-9A-F#]{,4}')
random.seed()

@stuffHook("(?i)" + config.nick + "[:,]?\s*(.*)")
def chat(irc, event):
    try:
        text = event.match.group(1)
    except IndexError:
        text = event.message
    
    read_receipt(irc.client, event.target, event.event_id)

    if len(text) > 1:
        if text.startswith('\x03') or text.startswith('\x01'):
            ## block out /ctcp
            return
    else:
        print(time.time(), 'Something went wrong with chat.py')
        return

    if not text:
        return
    
    if config.nick in text.split(" ")[0]:
        text = " ".join(text.split(" ")[1:])
    
    channel = event.target
    try:
        mycb[channel]
    except KeyError:
        mycb[channel] = CleverWrap(config.CLEVERBOT_API_KEY)

    for x in nowords:
        if text.startswith(x):
            return

    msgi = text.strip()
    msgo = str()

    msgo = mycb[channel].say(msgi)
    
    if type(msgo) == bytes:
        msgo = msgo.decode()
    
    if msgo:
        stime = random.randint(1, 9)
        typing(irc.client, event.target, stime * 1000)
        time.sleep(stime)

        response = re.sub('(?i)clever(me|script|bot)', config.nick, msgo)
        response = re.sub('(?i)\S+bot', (base64.b64decode(random.choice(noun)).decode()), response)
        response = re.sub('(?i)(bot|human)', (base64.b64decode(random.choice(noun)).decode()), response)
        response = re.sub('(?i)computer', (base64.b64decode(random.choice(noun)).decode()), response)
        response = r_entity.sub(e, response)

        if random.random() <= 0.5:
            response = response[0].lower() + response[1:]

        if random.random() <= 0.5:
            response = response[:-1]

        def chomp(txt):
            random_int_rm = random.randint(1, len(txt))
            return txt[:random_int_rm-1] + txt[random_int_rm:]

        def switcharoo(txt):
            temp = random.randint(1, len(txt) - 2)
            return txt[:temp] + txt[temp + 1] + txt[temp] + txt[temp + 2:]
        
        def fixaroo(txt):
            return chr(int(txt[1:], 16))

        if random.random() <= 0.25:
            l_response = len(response) // 20
            for x in range(1, l_response):
                response = chomp(response)

        if random.random() <= 0.15:
            l_response = len(response) // 30
            for x in range(1, l_response):
                response = switcharoo(response)

        if random.random() <= 0.05:
            response = response.upper()

        response = r_entity.sub(e, response)
        delim = random.choice((',', ':'))
        msg = '%s' % (response)
        typing(irc.client, event.target, 1, False)
        if random.random() <= 0.25:
            return irc.reply(msg)
        if random.random() <= 0.05:
            return

        irc.message(event.target, msg)

    if random.random() <= 0.05:
        chat(irc, event)



FANCY_ENGLISH_DICT = {
    "french fries": "\002chips\002",
    "chips": "\002crisps\002",
    "candy bar": "\002chocolate glabbernaught\002",
    "car": "\002motorised rollingham\002",
    "firework": "\002merry fizzlebomb\002",
    "gravy": "\002meat water\002",
    "power cable": "\002electro rope\002",
    "hamburger": "\002beef wellington ensemble with lettuce\002",
    "pen": "\002whimsy filmsy mark and scribble\002",
    "doorknob": "\002twisty plankhandle\002",
    "sandwich": "\002breaddystack\002",
    "keyboard": "\002hoighty toigthy tippy typer\002",
    "escalator": "\002upsy stairsy\002",
    "elevator": "\002upsy stairsy\002",
    "sweater": "\002knittedy wittedy sheepity sleepity\002",
    "gear shift": "\002rickedy-pop\002",
    "cookie": "\002choco chip bicky wicky\002",
    "sex": "\002peepee friction pleasure\002",
    "screwdriver": "\002pip pip gollywock\002",
    "gun": "\002rooty tooty point-n-shooty\002",
    "lightbulb": "\002ceiling-bright\002",
    "ball": "\002blimpy bounce bounce\002",
    "snake": "\002slippery dippery long mover\002",
    "road": "\002cobble-stone-clippity-clop\002",
    "mail": "\002pip paper\002",
    "rape": "\002forcey fun time\002",
    "mailman": "\002postlord\002",
    "pant": "\002leg sleeve\002",
    "eggplant": "\002bunglespleen\002",
    "popsicle": "\002cold on the cob\002",
    "move": "\002pembo\002",
    "moving": "\002pemboing\002"
}

FE_PATTERN = pattern = '|'.join(sorted(('\\b' + re.escape(k) + '\\b') for k in FANCY_ENGLISH_DICT))

@stuffHook(".+")
def random_chat(jenni, event):
    bad_chans =  fchannels()
    if bad_chans and (event.target).lower() in bad_chans:
        return

    if random.random() <= (1 / 2500.0):
        old_input = event
        chat(jenni, event)

    if random.randint(1,4) == 1:
        print(pattern)
        ntext = re.sub(FE_PATTERN, lambda m: FANCY_ENGLISH_DICT.get(m.group(0).lower()), event.message, flags=re.IGNORECASE)
        if ntext != event.message:
            jenni.message(event.target, "Did you mean: {0}".format(ntext))

    if not event.message.startswith(config.nick) and config.nick in event.message and random.randint(1, 3) == 1:
        chat(jenni, event)


def e(m):
    entity = m.group()
    if entity.startswith('&#x'):
        cp = int(entity[3:-1], 16)
        meep = unichr(cp)
    elif entity.startswith('&#'):
        cp = int(entity[2:-1])
        meep = unichr(cp)
    else:
        entity_stripped = entity[1:-1]
        try:
            char = name2codepoint[entity_stripped]
            meep = unichr(char)
        except:
            if entity_stripped in HTML_ENTITIES:
                meep = HTML_ENTITIES[entity_stripped]
            else:
                meep = str()
    return meep


def fchannels():
    try:
        f = open('nochannels.txt', 'r')
    except:
        return False
    lines = f.readlines()[0]
    f.close()
    lines = lines.replace('\n', '')
    return lines.split(',')
    

def typing(cli, channel, msecs, typing=True):
    path = "/rooms/%s/typing/%s" % (
        quote(channel), quote(cli.user_id),
    )
    params = {'typing': typing, 'timeout': msecs}
    return cli.api._send("PUT", path, params)


def read_receipt(cli, channel, event):
    path = "/rooms/%s/receipt/m.read/%s" % (
        quote(channel), quote(event),
    )
    params = {}
    return cli.api._send("POST", path, params)
