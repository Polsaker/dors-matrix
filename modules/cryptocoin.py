from io import BytesIO

import aiofiles
import aiohttp
from nio import MatrixRoom, UploadResponse

from dors import command_hook, Jenny, HookMessage
import config
import requests

coinmap = {'btc': 'bitcoin', 'ltc': 'litecoin', 'drk': 'darkcoin', 'doge': 'dogecoin',
           'eth': 'ethereum', 'myst': 'mysterium', 'nxt': 'nxt', 'ppc': 'peercoin',
           'ifc': 'infinitecoin', 'qrk': 'quarkcoin', 'moon': 'mooncoin', 'aur': 'auroracoin',
           'vtc': 'vertcoin', 'wdc': 'worldcoin', 'nvc': 'novacoin', 'ftc': 'feathercoin',
           'zet': 'zetacoin', 'uno': 'unobtanium', 'tips': 'fedoracoin', 'clam': 'clams',
           'mint': 'mintcoin', 'ixc': 'ixcoin', 'dmd': 'diamond', 'dgc': 'digitalcoin',
           'sxc': 'sexcoin', 'btb': 'bitbar', 'ccn': 'cannacoin', 'trc': 'terracoin',
           'mzc': 'mazacoin', 'net': 'netcoin', 'cnc': 'chncoin', 'anc': 'anoncoin',
           'hbn': 'hobonickels', 'nmc': 'namecoin', 'emd': 'emerald', 'fst': 'fastcoin',
           'glc': 'globalcoin', 'xpm': 'primecoin', 'gld': 'goldcoin', 'sc': 'silkcoin',
           'src': 'securecoin', '42': '42-coin', 'xrp': 'ripple', 'dgb': 'digibyte',
           'max': 'maxcoin', 'rdd': 'reddcoin', 'red': 'reddcoin', 'myr': 'myriad',
           'cach': 'cachecoin', 'huc': 'huntercoin', 'grc': 'gridcoin', 'ttc': 'tittiecoin',
           'blk': 'blackcoin', 'bc': 'blackcoin', 'zeit': 'zeitcoin', 'pot': 'potcoin',
           'rby': 'rubycoin', 'omg': 'omisego', 'xmr': 'monero', 'dai': 'multi-collateral-dai',
           'ada': 'cardano', 'paxg': 'pax-gold'}

resultsym = {'USD': '$', 'EUR': '€', 'GBP': '£', 'AUD': 'A$', 'CAD': 'C$',
             'ARS': 'A$', 'NZD': '$', 'JPY': '¥', 'KPW': '₩', 'KRW': '₩', 'ILS': '₪',
             'BTC': '฿', 'LTC': 'Ł', 'DOGE': 'Ð', 'ETH': 'Ξ'}


@command_hook(['bit', 'bits'])
async def bit(bot: Jenny, room: MatrixRoom, event: HookMessage):
    try:
        bits = float(event.args[0].replace('k', ''))
        if 'k' in event.args[0]:
            bits *= 1000
        bits = int(bits)
    except (IndexError, ValueError):
        return await bot.say("Usage: .bit <bits>")

    bitcoin = bits / 1000000
    bitprice = requests.get("https://blockchain.info/ticker").json()

    message = "\002{0}\002 bits => ฿\002{1}\002 => $\002{2}\002, €\002{3}\002, £\002{4}\002.".format(
        bits, bitcoin, round(bitprice['USD']['last'] * bitcoin, 2), round(bitprice['EUR']['last'] * bitcoin, 2),
        round(bitprice['GBP']['last'] * bitcoin, 2))
    await bot.message(room.room_id, await bot.source_tag(event.sender) + ": " + message, p_html=True)


@command_hook(['bitcoin', 'btc'])
async def btc(bot: Jenny, room: MatrixRoom, event: HookMessage):
    tick = True
    try:
        bitcoin = float(event.args[0])
    except (IndexError, ValueError):
        if len(event.args) > 0 and 34 >= len(event.args[0]) >= 26 and event.args[0][0] in ("1", "3", 'b'):
            data = requests.get("https://blockchain.info/es/rawaddr/" + event.args[0]).json()
            bitcoin = float(data['final_balance'] / 100000000)
            tick = False
        else:
            bitcoin = 1.0

    await coin_price(bot, 'bitcoin', bitcoin, tick)


@command_hook(['dogecoin', 'doge'])
async def doge(bot: Jenny, room: MatrixRoom, event: HookMessage):
    tick = True
    try:
        dogecoin = float(event.args[0])
    except (IndexError, ValueError):
        if len(event.args) > 0 and 34 >= len(event.args[0]) >= 26 and event.args[0][0] in ("D", "9", "A"):
            data = requests.get("https://dogechain.info/api/v1/address/balance/" + event.args[0]).json()
            if data['success'] == 0:
                return await bot.reply(data['error'])
            dogecoin = float(data['balance'])
            tick = False
        else:
            dogecoin = 1000.0

    await coin_price(bot, 'dogecoin', dogecoin, tick)


@command_hook(['monero', 'xmr'])
async def xmr(bot: Jenny, room: MatrixRoom, event: HookMessage):
    try:
        monero = float(event.args[0])
    except (IndexError, ValueError):
        monero = 1.0

    await coin_price(bot, 'monero', monero)


@command_hook(['ethereum', 'eth'])
async def eth(bot: Jenny, room: MatrixRoom, event: HookMessage):
    try:
        ethereum = float(event.args[0])
    except (IndexError, ValueError):
        ethereum = 1.0

    await coin_price(bot, 'ethereum', ethereum)


@command_hook(['mysterium', 'myst'])
async def myst(bot: Jenny, room: MatrixRoom, event: HookMessage):
    try:
        mysterium = float(event.args[0])
    except (IndexError, ValueError):
        mysterium = 1.0

    await coin_price(bot, 'mysterium', mysterium)


@command_hook(['bitcoin-cash', 'bch'])
async def bch(bot: Jenny, room: MatrixRoom, event: HookMessage):
    try:
        bch = float(event.args[0])
    except (IndexError, ValueError):
        bch = 1.0

    await coin_price(bot, 'bitcoin-cash', bch)


def prettify(thing):
    thing = round(thing, 2)
    if thing > 0:
        return "\00303+" + str(thing) + "\003"
    elif thing < 0:
        return "\00304" + str(thing) + "\003"


@command_hook(['coin'])
async def coin(bot: Jenny, room: MatrixRoom, event: HookMessage):
    try:
        coin = coinmap.get(event.args[0].lower(), event.args[0])
    except (IndexError, ValueError):
        coin = 'bitcoin'
    try:
        amount = float(event.args[1])
    except (IndexError, ValueError):
        amount = 1.0

    await coin_price(bot, coin, amount)


async def coin_price(bot: Jenny, symbol, amount, tick=True):
    message = ""
    try:
        i = requests.get('https://pro-api.coinmarketcap.com/v1/cryptocurrency/quotes/latest?slug=' + symbol, headers={
            "X-CMC_PRO_API_KEY": config.coinmarketcap_apikey}).json()  # market cap sorted by top
        info = i['data']
        info = info[next(iter(info))]
    except AttributeError:
        return await bot.reply("Coin not found")

    message += "\002{0}\002 \002{1}\002 => $\002{2}\002".format(
        amount, info['symbol'], round(float(info['quote']['USD']['price']) * amount, 2))
    if tick:
        message += "  [hour: \002{0}\002%, day: \002{1}\002%, week: \002{2}\002%]".format(
            prettify(float(info['quote']['USD']['percent_change_1h'])),
            prettify(float(info['quote']['USD']['percent_change_24h'])),
            prettify(float(info['quote']['USD']['percent_change_7d'])))
    await bot.reply(message + '.')


@command_hook(['coins'], help='.coins <convertTo:optional> -- get coin price and daily/weekly percent change.')
async def coins(bot: Jenny, room: MatrixRoom, event: HookMessage):
    msg = ''
    default_show = ['BTC', 'LTC', 'ETH', 'BCH', 'DOGE', 'XMR', 'ADA', 'PAXG']  # show info for these ticker symbols
    convert = 'USD'  # default fiat or crypto ticker symbol
    i = requests.get(
        'https://pro-api.coinmarketcap.com/v1/cryptocurrency/listings/latest?convert=' + convert + '&limit=250',
        headers={"X-CMC_PRO_API_KEY": config.coinmarketcap_apikey})  # market cap sorted by top
    if not i.ok:
        return await bot.say(f'Got error {i.status_code} from coinmarketcap. :(')
    i = i.json()['data']
    if convert != 'USD':
        msg += '(\002{0}\002) ● '.format(convert)
    for c in i:
        if c['symbol'] in default_show:
            volume = ''
            coin = c['quote'][convert]
            price = coin['price']
            try:
                sym = resultsym.get(convert, '')
            except (IndexError, ValueError):
                sym = ''
            if c['symbol'] == 'DOGE':
                price = round(float(float(price * 1) * 1000), 2)
                volume = '(1000x)'
            if sym == '$':
                price = round(float(price), 2)
            msg += '\002{0}\002{1}: {2}{3} ({4}%|{5}%) ● '.format(
                c['symbol'], volume, sym, price,
                prettify(float(coin['percent_change_24h'])),
                prettify(float(coin['percent_change_7d'])))
    msg += '[coin: $price (day%|week%)]'
    await bot.say(msg)


@command_hook(['coins2'], help='.coins2 <convertTo:optional> -- get coin prices and convert to fiat or cryptos.')
async def coins2(bot: Jenny, room: MatrixRoom, event: HookMessage):
    msg = ''
    default_show = 'BTC,BCH,LTC,DOGE,ETH,XMR,MYST,ADA'  # get info for these ticker symbols
    try:
        convert = event.args[0].upper()
    except (IndexError, ValueError):
        convert = 'USD'  # default fiat or crypto ticker symbol
    i = requests.get('https://min-api.cryptocompare.com/data/pricemulti?fsyms=' + default_show + '&tsyms=' + convert)
    i = i.json()
    if 'Error' in str(i):
        await bot.say(i['Message'])
        return
    if convert != 'USD':
        msg += '(\002{0}\002) ● '.format(convert)
    for c in i.items():
        coin = c[0]
        volume = ''
        try:
            sym = resultsym.get(convert, '')
        except (IndexError, ValueError):
            sym = ''
        price = c[1][convert]
        if coin == 'DOGE':
            volume = '(1000x)'
            price = round(float(price * 1000), 2)
        msg += '\002{0}\002{1}: {2}{3} ● '.format(coin, volume, sym, price)
    await bot.say(msg[:-3])


@command_hook(['tradeview', 'tv'], help='.tradeview <coin> - view tradeview data for a pair.')
async def tradeview(bot: Jenny, room: MatrixRoom, event: HookMessage):
    if not event.args:
        return await bot.say("Usage: .tradeview <coin> (ie .tradeview BTC)")

    symbol = event.args[0].upper()

    width = 800
    height = 400

    if symbol not in ('DOGE', 'BTC', 'ETH', 'ADA', 'LTC'):
        return await bot.say("Symbol not supported. Bother Polsaker to add it.")

    await bot.room_typing(room.room_id, True, 10000)

    async with aiohttp.ClientSession() as session:
        async with session.get("https://api.chart-img.com/v1/tradingview/advanced-chart", params={
            "height": height,
            "width": width,
            "interval": "1h",
            "symbol": f"{symbol}USD"
        }) as resp:
            buffer = BytesIO(await resp.read())

    st_size = buffer.getbuffer().nbytes
    buffer.seek(0)

    async with aiofiles.open("tmp_qr.png", "r+b") as f:
        resp, maybe_keys = await bot.upload(
            buffer,  # noqa
            content_type="image/png",
            filename="doge_address.png",
            filesize=st_size)
    if isinstance(resp, UploadResponse):
        print("Image was uploaded successfully to server. ")
    else:
        print(f"Failed to upload image. Failure response: {resp}")

    content = {
        "body": "doge_address.png",
        "info": {
            "size": st_size,
            "mimetype": "image/png",
            "thumbnail_info": None,  # TODO
            "w": width,  # width in pixel
            "h": height,  # height in pixel
            "thumbnail_url": None,  # TODO
        },
        "msgtype": "m.image",
        "url": resp.content_uri,
    }

    try:
        await bot.room_send(
            room.room_id,
            message_type="m.room.message",
            content=content
        )
        print("Image was sent successfully")
    except Exception:  # noqa
        print(f"Image send of file failed.")
