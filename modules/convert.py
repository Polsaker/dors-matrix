import re
import requests
from dors import commandHook

convert_re = re.compile(r"^(?P<amount>[0-9.,Kk ]+?)? ?(?P<unit_from>[a-zA-Z]+) (to ?)?(?P<unit_to>[a-zA-Z]+)?$")

temperature_units = {
    'f': 'farenheit',
    'farenheit': 'farenheit',
    'c': 'celsius',
    'celsius': 'celsius',
    'centigrade': 'celsius',
}


@commandHook(['convert', 'conv', 'co', 'c'])
def convert(irc, ev):
    if not ev.args:
        irc.reply("Usage: .convert <amount> <from> <to> -- Converts stuff from one unit to another.")

    res = convert_re.match(" ".join(ev.args))
    if not res:
        irc.reply("Usage: .convert <amount> <from> <to> -- Converts stuff from one unit to another.")

    amount = res.group('amount')
    if not amount:
        amount = "1"
    amount = amount.replace('k', '000').replace('K', '000')
    amount = amount.replace('m', '000000').replace('M', '000000')
    amount = amount.replace(',', '.')  # tehee
    amount = amount.replace(" ", "")
    amount = float(amount)

    unit_from = res.group('unit_from')
    unit_to = res.group('unit_to')
    if not unit_to:
        unit_to = 'USD'

    # Check if we're trying to convert temperature
    if unit_from in temperature_units and unit_to in temperature_units:
        return temperature_convert(irc, amount, temperature_units[unit_from], temperature_units[unit_to])

    price_convert(irc, amount, unit_from.upper(), unit_to.upper())


def price_convert(irc, amount, coinin, coinout):
    message = ""
    info = requests.get("https://min-api.cryptocompare.com/data/price?fsym=" + coinin + "&tsyms=" + coinout).json()
    if 'Error' in str(info):
        return irc.reply(info['Message'])
    info = round(float(info[coinout]) * amount, 8)
    if coinout != "BTC":
        message += "\002{0}\002 \002{1}\002 => \002{2}\002 \002{3}\002".format(amount, coinin, info, coinout)
    else:
        message += "\002{0}\002 \002{1}\002 => \002{2:.8f}\002 \002{3}\002".format(amount, coinin, info, coinout)
    irc.reply(message + '.')


def temperature_convert(irc, amount, unit_from, unit_to):
    temp_funcs = {
        'celsius': lambda x: x,
        'farenheit': lambda x: (x * 9/5) + 32
    }
    # Here we basically only do f to c and c to f, but i'll make this the long way
    # Convert to common unit (c)
    conv_amount = temp_funcs[unit_from](amount)
    # Convert to specified unit
    conv_amount = temp_funcs[unit_to](conv_amount)
    irc.reply(f"\002{amount:.2f}\002 \002{unit_from.capitalize()}\002 => \002{conv_amount:.2f}\002 "
              f"\002{unit_to.capitalize()}\002")
