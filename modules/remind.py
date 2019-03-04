# ported from jenni :x
from datetime import datetime, timedelta
from dors import commandHook, startupHook
import re
import time
import os
import threading


rfn = 'remind.db'
r_command = None
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

@startupHook()
def setup(bot):
    global r_command
    periods = '|'.join(scaling.keys())
    p_command = r'{}in ([0-9]+(?:\.[0-9]+)?)\s?((?:{})\b)?:?\s?(.*)'.format(
        bot.config.prefix,
        periods,
    )
    r_command = re.compile(p_command)

    bot.rdb = load_database('remind.db')

    def monitor(bot):
        time.sleep(5)
        while True:
            now = int(time.time())
            unixtimes = [int(key) for key in bot.rdb]
            oldtimes = [t for t in unixtimes if t <= now]
            if oldtimes:
                for oldtime in oldtimes:
                    for (channel, nick, message) in bot.rdb[oldtime]:
                        if message:
                            bot.message(channel, nick + ': ' + message)
                        else: bot.message(channel, nick + '!')
                    del bot.rdb[oldtime]

                dump_database(rfn, bot.rdb)
            time.sleep(2.5)

    targs = (bot,)
    t = threading.Thread(target=monitor, args=targs)
    t.start()

@commandHook(['in'], help="Reminds you of something after X time. Usage: in <time> <something>. Example: in 10 mins clean microwave")
def remind(bot, event):
    m = r_command.match(event.message)
    if not m:
        return bot.reply("Sorry, didn't understand the input.")
    length, scale, message = m.groups()

    length = float(length)
    factor = scaling.get(scale, 60)
    duration = length * factor

    if duration % 1:
        duration = int(duration) + 1
    else: duration = int(duration)

    t = int(time.time()) + duration
    message += ' | Set on: ' + str(datetime.now().isoformat())
    reminder = (event.replyto, event.source, message)

    try: bot.rdb[t].append(reminder)
    except KeyError: bot.rdb[t] = [reminder]

    dump_database(rfn, bot.rdb)

    if duration >= 60:
        try:
            w = ''
            if duration >= 3600 * 12:
                w += time.strftime(' on %d %b %Y', time.gmtime(t))
            w += time.strftime(' at %H:%MZ', time.gmtime(t))
            bot.reply('Okay, will remind%s' % w)
        except:
            bot.reply('Please enter a more realistic time-frame.')
    else: bot.reply('Okay, will remind in %s secs' % duration)
