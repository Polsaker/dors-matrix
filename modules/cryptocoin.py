from nio import MatrixRoom

from dors import command_hook, Jenny, HookMessage
import config
import requests
import math

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
           'ada': 'cardano'}

resultsym = {'USD': '$', 'EUR': '€', 'GBP': '£', 'AUD': 'A$', 'CAD': 'C$',
             'ARS': 'A$', 'NZD': '$', 'JPY': '¥', 'KPW': '₩', 'KRW': '₩', 'ILS': '₪',
             'BTC': '฿', 'LTC': 'Ł', 'DOGE': 'Ð', 'ETH': 'Ξ'}


@command_hook(['fees'])
async def bitfee(bot: Jenny, room: MatrixRoom, event: HookMessage):
    txs = requests.get('https://blockchain.info/q/unconfirmedcount')
    txs = str(txs.content).replace('b', '').replace('\'', '')

    btc_fee = requests.get("https://bitcoiner.live/api/fees/estimates/latest").json()
    btc_fee = btc_fee["estimates"]["30"]["total"]
    message = f"Bitcoin (30 min): Legacy: $\002{round(btc_fee['p2pkh']['usd'], 2)}\002 " \
              f"({btc_fee['p2pkh']['satoshi']} sat) | "
    message += f"Segwit (P2SH): $\002{round(btc_fee['p2sh-p2wpkh']['usd'], 2)}\002 " \
               f"({btc_fee['p2sh-p2wpkh']['satoshi']} sat) | "
    message += f"Segwit (Native): $\002{round(btc_fee['p2wpkh']['usd'], 2)}\002 " \
               f"({btc_fee['p2wpkh']['satoshi']} sat) | {txs} unconfirmed transactions.\n\n"

    try:
        try:
            i = requests.get('https://pro-api.coinmarketcap.com/v1/cryptocurrency/quotes/latest?slug=ethereum',
                             headers={"X-CMC_PRO_API_KEY": config.coinmarketcap_apikey}).json()
            info = i['data']
            info = info[next(iter(info))]
        except AttributeError:
            return await bot.reply("Coin not found")
        price_usd = float(info['quote']['USD']['price'])

        eth_fee = requests.get(
            f"https://api.etherscan.io/api?module=gastracker&action=gasoracle&apikey={config.etherscan_apikey}").json()
        eth_fee = eth_fee["result"]
        eth_gas = int(eth_fee['ProposeGasPrice'])
        congestion = eth_fee["gasUsedRatio"].split(",")
        congestion = [float(x) for x in congestion]
        avg_congestion = round((sum(congestion) / len(congestion)) * 100, 2)
        eth_gas = round(((eth_gas * 21000) / 10 ** 9) * price_usd, 2)
        erc20_gas = round(((eth_gas * 50000) / 10 ** 9) * price_usd, 2)
        message += f"\n\nEthereum: \002{eth_gas}\002 Gwei - ETH: $\002{eth_gas}\002 | ERC20: $\002{erc20_gas}\002"
        message += f" - Avg. network congestion: \002{avg_congestion}%\002"
    except RuntimeError:
        message += "\n\nEthereum: (error)"
    await bot.message(room.room_id, message)


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
    bitprice = requests.get("https://blockchain.info/es/ticker").json()

    message = "\002{0}\002 bits => ฿\002{1}\002 => $\002{2}\002, €\002{3}\002, £\002{4}\002.".format(
        bits, bitcoin, round(bitprice['USD']['last'] * bitcoin, 2), round(bitprice['EUR']['last'] * bitcoin, 2),
        round(bitprice['GBP']['last'] * bitcoin, 2))
    await bot.message(room.room_id, await bot.source_tag(event.sender) + ": " + message)


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
    default_show = ['BTC', 'LTC', 'ETH', 'BCH', 'DOGE', 'XMR', 'ADA']  # show info for these ticker symbols
    convert = 'USD'  # default fiat or crypto ticker symbol
    i = requests.get(
        'https://pro-api.coinmarketcap.com/v1/cryptocurrency/listings/latest?convert=' + convert + '&limit=250',
        headers={"X-CMC_PRO_API_KEY": "950e7d29-19f8-47eb-8395-a0c442298d59"})  # market cap sorted by top
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
