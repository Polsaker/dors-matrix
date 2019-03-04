from dors import stuffHook, startupHook, commandHook
import sqlite3
import time
import config
import random

database = None

def checkdb(c):
    c.execute("CREATE TABLE IF NOT EXISTS tell ( tellee text,\
            teller text, time text, msg text)")

def load_db():
    conn = sqlite3.connect('tell.db')
    c = conn.cursor()
    checkdb(c)
    conn.commit()
    
    c.execute("SELECT * FROM tell")

    ret = {}
    for x in c:
        try:
            ret[x[0]]
        except KeyError:
            ret[x[0]] = []
        ret[x[0]].append({'tellee': x[0], 'teller': x[1], 'time': x[2], 'msg': x[3]})

    return ret


def addReminder(tellee, teller, timenow, msg):
    global database
    conn = sqlite3.connect('tell.db')
    c = conn.cursor()
    checkdb(c)
    conn.commit()
    c.execute("INSERT INTO tell VALUES (?,?,?,?)", (tellee, teller, timenow, msg))
    conn.commit()
    c.close()
    database = load_db()


    
@commandHook(['tell', 'yell', 'to'], help=".tell someone something -- tells something to someone the next time they talk.")
def tell(irc, ev):
    teller = ev.source
    
    if len(ev.args) < 1:
        return irc.message(ev.replyto, 'Please tell me who and what to tell people.')
    
    tellee = ev.args[0]
    msg = " ".join(ev.args[1:])
    
    tellee = tellee.rstrip('.,:;')
    
    timenow = time.strftime('%d %b %H:%MZ', time.gmtime())

    reminders = {}

    whogets = []
    for tellee in tellee.split(','):
        if len(tellee) > 20:
            irc.message(ev.replyto, 'Nickname %s is too long.' % (tellee))
            continue
        if not tellee.lower() in (teller.lower(), config.nick):  # @@
            if not tellee.lower() in whogets:
                whogets.append(tellee)
                addReminder(tellee, teller, timenow, msg)
                
    
    if teller.lower() == tellee.lower() or tellee.lower() == 'me':
        response = 'You can tell yourself that.'
    elif tellee.lower() == config.nick.lower():
        response = "Hey, I'm not as stupid as Monty you know!"
    else:
        response = "I'll pass that on when {0} is around."
        if len(whogets) > 1:
            listing = ', '.join(whogets[:-1]) + ', or ' + whogets[-1]
            response = response.format(listing)
        elif len(whogets) == 1:
            response = response.format(whogets[0])
        else:
            return irc.message(ev.replyto, 'Huh?')

    if not whogets: # Only get cute if there are not legits
        rand = random.random()
        if rand > 0.9999: response = 'yeah, yeah'
        elif rand > 0.999: response = 'yeah, sure, whatever'

    irc.message(ev.replyto, response)

def getReminders(irc, channel, key, tellee):
    global database
    lines = []
    template = '{0}: {1} <{2}> tell {0} {3}'
    today = time.strftime('%d %b', time.gmtime())

    #jenni.tell_lock.acquire()
    
    conn = sqlite3.connect('tell.db')
    c = conn.cursor()
    checkdb(c)
    conn.commit()


    for entry in database[key]:
        if entry['time'].startswith(today):
            entry['time'] = entry['time'][len(today) + 1:]
        lines.append(template.format(entry['tellee'], entry['time'], 
                                     entry['teller'], entry['msg']))
    
    c.execute("DELETE FROM tell WHERE tellee = ?", (key,))
    conn.commit()
    c.close()


    try: del database[key]
    except KeyError: irc.message(channel, 'Er...')

    return lines


@stuffHook(".+")
def message(irc, ev):
    global database
    if not ev.target.startswith('#'): return

    tellee = ev.source
    channel = ev.target

    reminders = []
    
    remkeys = list(reversed(sorted(database.keys())))
    for remkey in remkeys:
        if not remkey.endswith('*') or remkey.endswith(':'):
            if tellee.lower() == remkey.lower():
                reminders.extend(getReminders(irc, channel, remkey, tellee))
        elif tellee.lower().startswith(remkey.rstrip('*:').lower()):
            reminders.extend(getReminders(irc, channel, remkey, tellee))

    # maximum = 4
    for line in reminders[:4]:
        irc.message(channel, line)

    if reminders[4:]:
        irc.message(channel, 'Further messages sent privately')
        for line in reminders[4:]:
            irc.message(tellee, line)


@startupHook()
def start(irc):
    global database
    database = load_db()
