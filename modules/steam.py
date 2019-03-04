""" Crappy module to get info on a steam game. """ 

from dors import commandHook, startupHook
import time
import requests

ts_steam = 0
ts_apps = {}

@startupHook()
def updateapps(irc):
    global ts_steam, ts_apps
    search1 = requests.get("https://api.steampowered.com/ISteamApps/GetAppList/v2/").json()

    applist = {}
    for l in search1['applist']['apps']:
        applist[l['name'].lower()] = l['appid']
    
    ts_steam = time.time()
    ts_apps = applist

updateapps(None)


@commandHook(['steam', 'game'], help="Returns game info from Steam.")
def steam(irc, ev):
    global ts_steam, ts_apps
    game = " ".join(ev.args)
    try:
        appid = ts_apps[game.lower()]
    except KeyError:
        try:
            appid = int(game.lower())
        except ValueError:
            return irc.message(ev.replyto, "Couldn't find \002{0}\002".format(game))

    irc.message(ev.replyto, getAppInfo(appid))


def getAppInfo(appid, error=True):
    info = requests.get("https://store.steampowered.com/api/appdetails?appids={0}&cc=US&l=english".format(appid)).json()
    
    try:
        if info[str(appid)]['success'] != True:
            return "Error getting info for \002{0}\002".format(appid) if error else 0
    except KeyError:
        return "Error getting info for \002{0}\002".format(appid) if error else 0
    
    info = info[str(appid)]['data']
    
    resp = "[{0}] ".format(info['type']) if error else ""
    resp += "\002{0}\002".format(info['name'])
    if info['is_free']:
        resp += " (\00303free!\003)."
    else:
        resp += " (\002{0}\002 {1}".format(info['price_overview']['initial']/100, info['price_overview']['currency'])
        if info['price_overview']['discount_percent'] != 0:
            resp += " || \00303{0}% off\003!, \002{1}\002 {2}".format(info['price_overview']['discount_percent'],
                                                          info['price_overview']['final']/100, info['price_overview']['currency'])
        resp += ")."
    
    resp += " Platforms:"
    if info['platforms']['windows']:
        resp += " Windows,"
    if info['platforms']['mac']:
        resp += " Mac,"
    if info['platforms']['mac']:
        resp += " Linux,"
    resp = resp[:-1] + "."
    
    if info['genres']:
        resp += " Genres:"
        for genre in info['genres']:
            resp += " {0},".format(genre['description'])
        resp = resp [:-1] + "."
    
    try:
        resp += " Metacritic: \002{0}\002/100.".format(info['metacritic']['score'])
    except:
        pass
    
    qq = requests.get("https://api.steampowered.com/ISteamUserStats/GetNumberOfCurrentPlayers/v1/?appid={0}".format(appid)).json()
    if qq['response']['result'] == 1:
        resp += " [\002{0}\002 people playing]".format(qq['response']['player_count'])
    if error:
        resp += " https://store.steampowered.com/app/{0}/".format(appid)
    
    return resp
