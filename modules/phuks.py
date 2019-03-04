import requests
import datetime
from babel.dates import format_timedelta
import time
from dors import commandHook


def get_user(name):
    try:
        usdata = requests.get('https://phuks.co/api/getUser/{0}'.format(name))
    except:
        return "Could not contact Phuks"
    if usdata.status_code != 200:
        return "Could not contact Phuks"
    usdata = usdata.json()
    if usdata['status'] != "ok":
        return "Error: " + usdata['error']
    usdata = usdata['user']
    resp = "User \002{0}\002".format(usdata['name'])
    if usdata['bot']:
        resp += " [bot]"
    resp += ": level \002{0}\002 (lvlup in {1}). ".format(usdata['level'], ((usdata['level'] + 1) ** 2) *10 - usdata['xp'])
    resp += "\002{0}\002 phuks taken, \002{1}\002 phuks given (+{2}|-{3}). ".format(usdata['score'], usdata['given'], usdata['upvotes_given'], usdata['downvotes_given'])
    resp += "Created \002{0}\002 posts, \002{1}\002 comments. ".format(usdata['post_count'], usdata['comment_count'])
    regist = datetime.datetime.strptime(usdata['created'], "%a, %d %b %Y %H:%M:%S %Z")
    del_regist = datetime.datetime.utcnow() - regist
    resp += "Registered \002{0}\002 ago, ".format(format_timedelta(del_regist, locale='en_US'))
    resp += "mods {0} and owns {1} subs. https://phuks.co/u/{2}".format(len(usdata['mods']), len(usdata['owns']), usdata['name'])
    return resp


def get_sub(name):
    try:
        usdata = requests.get('https://phuks.co/api/getSub/{0}'.format(name))
    except:
        return "Could not contact Phuks"
    if usdata.status_code != 200:
        return "Could not contact Phuks"
    usdata = usdata.json()
    if usdata['status'] != "ok":
        return "Error: " + usdata['error']
    usdata = usdata['sub']
    resp = "Sub \002{0}\002".format(usdata['name'])
    if usdata['nsfw']:
        resp += " [NSFW]"
    regist = datetime.datetime.strptime(usdata['created'], "%Y-%m-%d %H:%M:%S.%f")
    del_regist = datetime.datetime.utcnow() - regist
    resp += " Created \002{0}\002 ago by {1},".format(format_timedelta(del_regist, locale='en_US'), usdata['creator'])
    resp += " {0} posts, {1} subscribers, {2} mods".format(usdata['posts'], usdata['subscribers'], len(usdata['mods']))
    return resp


@commandHook(['user'])
def phukuser(irc, ev):
    if ev.target in ("#phuks", "#phukadmins", "#throat", "Polsaker"):
        if not ev.args:
            return irc.reply("Usage: user <username>")

        irc.message(ev.replyto, get_user(ev.args[0]))


@commandHook(['sub'])
def phuksub(irc, ev):
    if ev.target in ("#phuks", "#phukadmins", "#throat", "Polsaker"):
        if not ev.args:
            return irc.reply("Usage: sub <subname>")

        irc.message(ev.replyto, get_sub(ev.args[0]))
