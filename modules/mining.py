from dors import commandHook, startupHook
import config
import requests
import time

def prettify(thing):
    if thing > 0:
        return "\00303+" + str(thing) + "\003"
    elif thing < 0:
        return "\00304" + str(thing) + "\003"


def pretty_date(time=False):
    """
    Get a datetime object or a int() Epoch timestamp and return a
    pretty string like 'an hour ago', 'Yesterday', '3 months ago',
    'just now', etc
    """
    from datetime import datetime
    now = datetime.now()
    if type(time) is int:
        diff = now - datetime.fromtimestamp(time)
    elif isinstance(time,datetime):
        diff = now - time
    elif not time:
        diff = now - now
    second_diff = diff.seconds
    day_diff = diff.days

    if day_diff < 0:
        return ''

    if day_diff == 0:
        if second_diff < 10:
            return str(second_diff) + " seconds ago"  # "just now"
        if second_diff < 60:
            return str(second_diff) + " seconds ago"
        if second_diff < 120:
            return "a minute ago"
        if second_diff < 3600:
            return str(second_diff / 60) + " minutes ago"
        if second_diff < 7200:
            return "an hour ago"
        if second_diff < 86400:
            return str(second_diff / 3600) + " hours ago"
    if day_diff == 1:
        return "Yesterday"
    if day_diff < 7:
        return str(day_diff) + " days ago"
    if day_diff < 31:
        return str(day_diff / 7) + " weeks ago"
    if day_diff < 365:
        return str(day_diff / 30) + " months ago"
    return str(day_diff / 365) + " years ago"


@commandHook(['mine', 'miner', 'mining'])
def miningstats(irc, ev):
    mine = requests.get("https://phuks.co/miner/stats").json()
    info = requests.get("https://api.coinmarketcap.com/v1/ticker/monero/").json()[0]
    rate = mine['hash']
    pending = mine['amtDue']
    xmrpaid = mine['amtPaid']
    # poolactive = pretty_date(mine['lastHash'])
    monies = float(mine['amtPaid'] + mine['amtDue'])
    reward = round(float(monies / (mine['totalHashes'] / 1000000)),6)
    active = len(mine['speed'])
    if active > 0:
        topboi = mine['speed'][0]['username']
        topboirate = mine['speed'][0]['hashes']
    else:
        topboi = "None"
        topboirate = "0"
    #topleader = mine['users'][0]['username']
    #topleaderhash = mine['users'][0]['hashes']
    priceusd = info['price_usd']
    pendingusd = round(float(info['price_usd']) * pending,2)
    xmrpaidusd = round(float(info['price_usd']) * xmrpaid,2)
    if active <= 9:
        activemsg = 'Active: {0}'.format(active)
    else:
        activemsg = 'Woot \o/ Active Users Leaderboad full!!!'
    #leaderboard = ''
    #for u in mine['speed']:
    leaderboard = '{0}({1}h/s). {2}'.format(topboi, topboirate, activemsg)

    message = "Site: {0}h/s. Pending/Paid: {1}/{2}xmr (${3}/${4}). Rate: {5:.6f}xmr/Mhash. Top: {6}  [XMR=${7:.5} | ".format(
              rate, pending, xmrpaid, pendingusd, xmrpaidusd, reward, leaderboard, priceusd)
    message += "day: \002{0}\002%, week: \002{1}\002%]".format(
               prettify(float(info['percent_change_24h'])),
               prettify(float(info['percent_change_7d'])))
    irc.message(ev.replyto, message)


@commandHook(['supportxmr'])
def supportxmr(irc, ev):
    info = requests.get("https://supportxmr.com/api/miner/{0}/stats".format(config.XMRaddress)).json()
    rate = info['hash']
    # lasttmp = datetime.datetime.fromtimestamp(info['lastHash']).strftime('%Y-%m-%d %H:%M:%S') # %Y-%m-%d %H:%M:%S
    last = pretty_date(info['lastHash'])
    pending = float(info['amtDue'] / 1000000000000)
    xmrpaid = float(info['amtPaid'] / 1000000000000)
    monies = float(info['amtPaid'] + info['amtDue'])
    reward = round(float(monies / (info['totalHashes'] * 1000000)), 10)
    message = "Site: {0}H/s. Pending: {1}xmr. Paid: {2}xmr. Rate: {3:.10f}xmr/Mhash. LastHash: {4}.".format(
              rate, pending, xmrpaid, reward, last)
    irc.message(ev.replyto, message)
