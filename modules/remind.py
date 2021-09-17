# ported from jenni :x
import asyncio
from datetime import datetime, timedelta

from nio import MatrixRoom

import config
from dors import command_hook, startup_hook, Jenny, HookMessage
import re
import time
import os
import threading
import html


rfn = 'remind.db'

scaling = {
    'years': 365.25 * 24 * 3600,
    'year': 365.25 * 24 * 3600,
    'yrs': 365.25 * 24 * 3600,
    'y': 365.25 * 24 * 3600,

    'months': 29.53059 * 24 * 3600,
    'month': 29.53059 * 24 * 3600,
    'mo': 29.53059 * 24 * 3600,

    'weeks': 7 * 24 * 3600,
    'week': 7 * 24 * 3600,
    'wks': 7 * 24 * 3600,
    'wk': 7 * 24 * 3600,
    'w': 7 * 24 * 3600,

    'days': 24 * 3600,
    'day': 24 * 3600,
    'd': 24 * 3600,

    'hours': 3600,
    'hour': 3600,
    'hrs': 3600,
    'hr': 3600,
    'h': 3600,

    'minutes': 60,
    'minute': 60,
    'mins': 60,
    'min': 60,
    'm': 60,

    'seconds': 1,
    'second': 1,
    'secs': 1,
    'sec': 1,
    's': 1
}

periods = '|'.join(scaling.keys())
p_command = r'{}in ([0-9]+(?:\.[0-9]+)?)\s?((?:{})\b)?:?\s?(.*)'.format(config.prefix, periods,)
r_command = re.compile(p_command)


def load_database(name):
    data = {}
    if os.path.isfile(name):
        f = open(name, 'rb')
        for line in f:
            unixtime, channel, nick, message = line.decode('utf-8').split('\t')
            message = message.rstrip('\n')
            t = int(unixtime)
            reminder = (channel, nick, message)
            try: data[t].append(reminder)
            except KeyError: data[t] = [reminder]
        f.close()
    return data


def dump_database(name, data):
    f = open(name, 'wb')
    for unixtime, reminders in data.items():
        for channel, nick, message in reminders:
            f.write('{0}\t{1}\t{2}\t{3}\n'.format(unixtime, channel, nick, message).encode('utf-8'))
    f.close()


@startup_hook()
async def setup(bot: Jenny):
    bot.rdb = load_database('remind.db')

    async def monitor(bot: Jenny):
        await asyncio.sleep(5)
        print(" >> Starting remind loop!")
        while True:
            now = int(time.time())
            unixtimes = [int(key) for key in bot.rdb]
            oldtimes = [t for t in unixtimes if t <= now]
            if oldtimes:
                for oldtime in oldtimes:
                    for (channel, nick, message) in bot.rdb[oldtime]:
                        try:
                            mention = await bot.source_tag(nick)
                        except:
                            mention = nick
                        if message:
                            try:
                                await bot.message(channel, mention + ': ' + html.escape(message),
                                                  p_html=True, message_type='m.text')
                            except:
                                pass
                        else:
                            try:
                                await bot.message(channel, mention + '!', p_html=True, message_type='m.text')
                            except:
                                pass
                    del bot.rdb[oldtime]

                dump_database(rfn, bot.rdb)
            await asyncio.sleep(2.5)

    await monitor(bot)


@command_hook(['in'], help="Reminds you of something after X time. Usage: in <time> <something>. "
                           "Example: in 10 mins clean microwave")
async def remind(bot: Jenny, room: MatrixRoom, event: HookMessage):
    m = r_command.match(event.body)
    if not m:
        return bot.reply("Sorry, didn't understand the input.")
    length, scale, message = m.groups()

    length = float(length)
    factor = scaling.get(scale, 60)
    duration = length * factor

    if duration % 1:
        duration = int(duration) + 1
    else:
        duration = int(duration)

    t = int(time.time()) + duration
    message += ' | Set on: ' + str(datetime.now().isoformat())
    reminder = (room.room_id, event.sender, message)

    try:
        bot.rdb[t].append(reminder)
    except KeyError:
        bot.rdb[t] = [reminder]

    dump_database(rfn, bot.rdb)

    if duration >= 60:
        try:
            w = ''
            if duration >= 3600 * 12:
                w += time.strftime(' on %d %b %Y', time.gmtime(t))
            w += time.strftime(' at %H:%MZ', time.gmtime(t))
            await bot.reply('Okay, will remind%s' % w)
        except:
            await bot.reply('Please enter a more realistic time-frame.')
    else:
        await bot.reply(f'Okay, will remind in {duration} secs')

