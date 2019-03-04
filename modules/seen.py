""" Seen module. Requires the find module to be loaded. """

from dors import commandHook
from datetime import datetime, timedelta

@commandHook(['seen'], help="Shows when a nick was last seen. Usage: seen <nick>")
def seen(irc, ev):
    if not ev.args:
        return irc.reply("Usage: seen <nick>")
    target = ev.args[0]
    if target == ev.source:
        return irc.reply("You can tell better!")
    
    if target == irc.nickname:
        return irc.reply("I don't have a mirror :(")
    
    shit = [x for sl in [[l + [k] for l in v[target.lower()]] for k, v in irc.recent_lines.items() if target.lower() in list(v)] for x in sl]
    shit = sorted(shit, key=lambda x: x[1])
    try:
        last_seen = shit[-1]
    except:
        return irc.reply("I haven't seen {0}.".format(target))
    
    try:
        int(last_seen[1])
    except ValueError:
        last_seen = shit[-2]

    td = datetime.now() - datetime.fromtimestamp(int(last_seen[1])) 
    
    weeks, days = divmod(td.days, 7)
    hours, remainder = divmod(td.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    
    resp = "I saw \002{0}\002 last time ".format(target)
    ts = []
    if weeks:
        ts.append("{0} weeks".format(weeks))
    if days:
        ts.append("{0} days".format(days))
    if hours:
        ts.append("{0} hours".format(hours))
    if minutes and not weeks:
        ts.append("{0} minutes".format(minutes))
    if not minutes and not hours and not days and not weeks:
        return irc.reply("I can confirm that {0} is still around and not lurking!".format(target))
    if seconds and not days:
        ts.append("{0} seconds".format(seconds))
    
    if ts[:-1]:
        resp += ", ".join(ts[:-1]) + " and "
    resp += ts[-1] + " ago"
    
    if last_seen[2] == ev.target:
        resp += " on this channel, saying <{0}> {1}".format(target, last_seen[0])
    
    irc.say(resp)
        
