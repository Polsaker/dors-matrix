from dors import commandHook
import requests


@commandHook(['convert'])
def convert(irc, ev):
    try:
        amount = float(ev.args[0])
    except (IndexError, ValueError):
        amount = 1.0
    try:
        coinin = ev.args[1]
    except (IndexError, ValueError):
        coinin = 'BTC'
    try:
        coinout = ev.args[2]
    except (IndexError, ValueError):
        coinout = 'USD'

    priceConvert(irc, amount, coinin.upper(), coinout.upper())


def priceConvert(irc, amount, coinin, coinout):
    message = ""
    info = requests.get("https://min-api.cryptocompare.com/data/price?fsym=" + coinin + "&tsyms=" + coinout).json()
    if 'Error' in str(info):
        return irc.reply(info['Message'])
    info = round(float(info[coinout])*amount,8)
    if coinout != "BTC":
        message += "\002{0}\002 \002{1}\002 => \002{2}\002 \002{3}\002".format(amount, coinin, info, coinout)
    else:
        message += "\002{0}\002 \002{1}\002 => \002{2:.8f}\002 \002{3}\002".format(amount, coinin, info, coinout)
    irc.reply(message + '.')
