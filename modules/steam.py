""" Crappy module to get info on a steam game. """
from typing import Optional

from nio import MatrixRoom

from dors import command_hook, startup_hook, Jenny, HookMessage
import time
import requests

ts_steam = 0
ts_apps = {}


@startup_hook()
async def on_start(bot):
    updateapps()


def updateapps():
    global ts_steam, ts_apps
    search1 = requests.get("https://api.steampowered.com/ISteamApps/GetAppList/v2/").json()

    applist = {}
    for l in search1['applist']['apps']:
        applist[l['name'].lower()] = l['appid']
    
    ts_steam = time.time()
    ts_apps = applist


@command_hook(['steam', 'game'], help="Returns game info from Steam.")
async def steam(bot: Jenny, room: MatrixRoom, event: HookMessage):
    global ts_steam, ts_apps
    game = " ".join(event.args)
    try:
        appid = ts_apps[game.lower()]
    except KeyError:
        try:
            appid = int(game.lower())
        except ValueError:
            return await bot.say("Couldn't find \002{0}\002".format(game))

    await bot.say(getAppInfo(appid))


def getAppInfo(appid, error=True):
    info = requests.get("https://store.steampowered.com/api/appdetails?appids={0}&cc=US&l=english".format(appid)).json()
    
    try:
        if not info[str(appid)]['success']:
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
