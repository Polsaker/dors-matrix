from dors import commandHook
import requests


@commandHook(['ticker'])
def ticker(irc, ev):
    try:
        coin = ev.args[0]
    except (IndexError, ValueError):
        coin = 'BTC'
    try:
        amount = float(ev.args[1])
    except (IndexError, ValueError):
        amount = 1.0
    if coin.upper() == "DOGE":
        try:
            amount = float(ev.args[1])
        except (IndexError, ValueError):
            amount = 1000

    tickerPrice(irc, coin.upper(), amount)


def tickerPrice(irc, coin, amount):
    message = ""
    info = requests.get("https://min-api.cryptocompare.com/data/price?fsym=" + coin + "&tsyms=BTC,USD,GBP,EUR,AUD,NZD,ARS").json()
    if 'Error' in str(info):
        return irc.reply(info['Message'])
    USDbase = info['USD']
    USD = round(float(info['USD'])*amount,2)
    GBP = round(float(info['GBP'])*amount,2)
    EUR = round(float(info['EUR'])*amount,2)
    AUD = round(float(info['AUD'])*amount,2)
    NZD = round(float(info['NZD'])*amount,2)
    ARS = round(float(info['ARS'])*amount,2)
    message += "\002{0}\002 \002{1}\002 => $\002{2}\002, £\002{3}\002, €\002{4}\002, $\002{5}\002 AUD, $\002{6}\002 NZD, $\002{7}\002 ARS".format(amount, coin, USD, GBP, EUR, AUD, NZD, ARS)
    if coin != "USD":
        history = requests.get("https://min-api.cryptocompare.com/data/histoday?fsym=" + coin + "&tsym=USD&limit=365").json()
            # docs https://www.cryptocompare.com/api/#-api-data-histoday-
        if 'Error' in str(history):
            return irc.reply(info['Message'])
        yesterday = float(history['Data'][365]['close'])
        lastweek = float(history['Data'][358]['close'])
        twoweeks = float(history['Data'][351]['close'])
        threeweeks = float(history['Data'][344]['close'])
        lastmonth = float(history['Data'][337]['close'])
        threemonth = float(history['Data'][277]['close'])
        sixmonth = float(history['Data'][187]['close'])
        oneyear = float(history['Data'][1]['close'])
        oy_perc = round(float((USDbase - oneyear) / oneyear)*100,2) if oneyear != 0 else "inf"
        message += " [1d: \002{0}\002%, 7d: \002{1}\002%, 14d: \002{2}\002%, 21d: \002{3}\002%, 28d: \002{4}\002%, 3m: \002{5}\002%, 6m: \002{6}\002%, 1y: \002{7}\002%]".format(
                    round(float((USDbase - yesterday) / yesterday)*100,2),
                    round(float((USDbase - lastweek) / lastweek)*100,2),
                    round(float((USDbase - twoweeks) / twoweeks)*100,2),
                    round(float((USDbase - threeweeks) / threeweeks)*100,2),
                    round(float((USDbase - lastmonth) / lastmonth)*100,2),
                    round(float((USDbase - threemonth) / threemonth)*100,2),
                    round(float((USDbase - sixmonth) / sixmonth)*100,2), oy_perc
)
    irc.reply(message + '.')
