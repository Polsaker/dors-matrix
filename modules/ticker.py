from nio import MatrixRoom

from dors import command_hook, Jenny, HookMessage
import requests


@command_hook(['ticker'])
async def ticker(bot: Jenny, room: MatrixRoom, event: HookMessage):
    try:
        coin = event.args[0]
    except (IndexError, ValueError):
        coin = 'BTC'
    try:
        amount = float(event.args[1])
    except (IndexError, ValueError):
        amount = 1.0
    if coin.upper() == "DOGE":
        try:
            amount = float(event.args[1])
        except (IndexError, ValueError):
            amount = 1000

    await ticker_price(bot, coin.upper(), amount)


async def ticker_price(bot: Jenny, coin, amount):
    message = ""
    info = requests.get("https://min-api.cryptocompare.com/data/price?fsym=" + coin + "&tsyms=BTC,USD,GBP,EUR,AUD,NZD,ARS").json()
    if 'Error' in str(info):
        return await bot.reply(info['Message'])
    usd_base = info['USD']
    usd = round(float(info['USD'])*amount,2)
    gbp = round(float(info['GBP'])*amount,2)
    eur = round(float(info['EUR'])*amount,2)
    aud = round(float(info['AUD'])*amount,2)
    nzd = round(float(info['NZD'])*amount,2)
    ars = round(float(info['ARS'])*amount,2)
    message += f"\002{amount}\002 \002{coin}\002 => $\002{usd}\002, £\002{gbp}\002, €\002{eur}\002, " \
               f"$\002{aud}\002 AUD, $\002{nzd}\002 NZD, $\002{ars}\002 ARS"
    if coin != "USD":
        history = requests.get("https://min-api.cryptocompare.com/data/histoday?fsym=" + coin + "&tsym=USD&limit=365")
        history = history.json()
        # docs https://www.cryptocompare.com/api/#-api-data-histoday-
        if 'Error' in str(history):
            return await bot.reply(info['Message'])
        yesterday = float(history['Data'][365]['close'])
        yesterday = round(float((usd_base - yesterday) / yesterday)*100, 2)
        lastweek = float(history['Data'][358]['close'])
        lastweek = round(float((usd_base - lastweek) / lastweek)*100, 2)
        twoweeks = float(history['Data'][351]['close'])
        twoweeks = round(float((usd_base - twoweeks) / twoweeks)*100, 2)
        threeweeks = float(history['Data'][344]['close'])
        threeweeks = round(float((usd_base - threeweeks) / threeweeks)*100, 2)
        lastmonth = float(history['Data'][337]['close'])
        lastmonth = round(float((usd_base - lastmonth) / lastmonth)*100, 2)
        threemonth = float(history['Data'][277]['close'])
        threemonth = round(float((usd_base - threemonth) / threemonth)*100, 2)
        sixmonth = float(history['Data'][187]['close'])
        sixmonth = round(float((usd_base - sixmonth) / sixmonth)*100, 2)
        oneyear = float(history['Data'][1]['close'])
        oneyear = round(float((usd_base - oneyear) / oneyear)*100,2) if oneyear != 0 else "inf"
        message += f" [1d: \002{yesterday}\002%, 7d: \002{lastweek}\002%, 14d: \002{twoweeks}\002%, " \
                   f"21d: \002{threeweeks}\002%, 28d: \002{lastmonth}\002%, 3m: \002{threemonth}\002%, " \
                   f"6m: \002{sixmonth}\002%, 1y: \002{oneyear}\002%]"

    await bot.reply(message + '.')
