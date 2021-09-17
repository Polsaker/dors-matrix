from dors import command_hook
import requests

currs = requests.get('https://www.cryptonator.com/api/currencies').json()
currencies = {}
for c in currs['rows']:
    currencies[c['code'].lower()] = c['name']

@command_hook(['crypto'])
def crypto(irc, ev):
    global currencies
    if len(ev.args) < 1:
        return irc.reply("Usage: crypto <from>-[to] [amount]. Example: .crypto btc-doge 10")
    
    if not "-" in ev.args[0]:
        cfrom = ev.args[0].lower()
        to = 'usd'
    else:
        to = ev.args[0].split("-")[1].lower()
        cfrom = ev.args[0].split("-")[0].lower()
    if len(ev.args) == 1:
        amount = 1.0
    else:
        amount = abs(float(ev.args[1]))
    
    if not currencies.get(cfrom):
        return irc.reply("I don't know what {0} is.".format(cfrom.upper()))
    if not currencies.get(to):
        return irc.reply("I don't know what {0} is.".format(to.upper()))
    
    fdc = "{0}-{1}".format(cfrom, to)
    xx = requests.get('https://api.cryptonator.com/api/ticker/{0}'.format(fdc))
    xx = xx.json()
    
    price = float(xx['ticker']['price'])
    pos = "\00303↑\003" if float(xx['ticker']['change']) > 0 else "\00304↓\003"
    rprice = "{0:.20f}".format(price*amount).rstrip("0")
    irc.say("Converting {0} \002{1}\002 => {2} \002{3}\002 (\002{4}\002)".format(amount, currencies.get(cfrom), rprice , currencies.get(to), pos))
