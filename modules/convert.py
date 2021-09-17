import copy
import re
import requests
from nio import MatrixRoom

from dors import command_hook, Jenny, HookMessage

convert_re = re.compile(r"^(?P<amount>[\-0-9.,KkMm ]+?)? ?(?P<unit_from>[a-zA-Z]+) (to ?)?(?P<unit_to>[a-zA-Z]+)?$")

temperature_units = {
    'f': 'farenheit',
    'farenheit': 'farenheit',
    'c': 'celsius',
    'celsius': 'celsius',
    'centigrade': 'celsius',
}


@command_hook(['convert', 'conv', 'co', 'c'])
async def convert(bot: Jenny, room: MatrixRoom, event: HookMessage):
    if not event.args:
        return await bot.reply("Usage: .convert <amount> <from> <to> -- Converts stuff from one unit to another.")

    res = convert_re.match(" ".join(event.args))
    if not res:
        return await bot.reply("Usage: .convert <amount> <from> <to> -- Converts stuff from one unit to another.")

    amount = res.group('amount')
    if not amount:
        amount = "1"
    amount = amount.replace('k', '000').replace('K', '000')
    amount = amount.replace('m', '000000').replace('M', '000000')
    amount = amount.replace(',', '')  # tehee
    amount = amount.replace(" ", "")
    amount = float(amount)

    unit_from = res.group('unit_from')
    unit_to = res.group('unit_to')
    if not unit_to:
        unit_to = 'USD'

    # Check if we're trying to convert temperature
    if unit_from in temperature_units and unit_to in temperature_units:
        return await temperature_convert(bot, amount, temperature_units[unit_from], temperature_units[unit_to])

    await price_convert(bot, amount, unit_from.upper(), unit_to.upper())


async def price_convert(irc: Jenny, amount, coinin, coinout):
    message = ""
    info = requests.get("https://min-api.cryptocompare.com/data/price?fsym=" + coinin + "&tsyms=" + coinout).json()
    if 'Error' in str(info):
        return irc.reply(info['Message'])
    info = round(float(info[coinout]) * amount, 8)
    if coinout in ("BTC", 'ETH'):
        message += "\002{0}\002 \002{1}\002 => \002{2:.8f}\002 \002{3}\002.".format(amount, coinin, info, coinout)
    else:
        message += "\002{0:,.2f}\002 \002{1}\002 => \002{2:,.2f}\002 \002{3}\002.".format(amount, coinin, info, coinout)
    await irc.reply(message)


async def temperature_convert(irc: Jenny, amount, unit_from, unit_to):
    temp_to_c_funcs = {
        'celsius': lambda x: x,
        'farenheit': lambda x: (x - 32) * 5 / 9
    }
    c_to_temp_funcs = copy.copy(temp_to_c_funcs)
    c_to_temp_funcs |= {
        'farenheit': lambda x: (x * 9 / 5) + 32
    }
    # Here we basically only do f to c and c to f, but i'll make this the long way
    # Convert to common unit (c)
    conv_amount = temp_to_c_funcs[unit_from](amount)
    # Convert to specified unit
    conv_amount = c_to_temp_funcs[unit_to](conv_amount)
    await irc.reply(f"\002{amount:.2f}\002 \002{unit_from.capitalize()}\002 => \002{conv_amount:.2f}\002 "
                    f"\002{unit_to.capitalize()}\002.")
