import copy
import re
import requests
from nio import MatrixRoom
import inflect
from dors import command_hook, Jenny, HookMessage

convert_re = re.compile(r"^(?P<amount>[\-0-9.,KkMm ]+?)? ?(?P<unit_from>[a-zA-Z]+) (to |in ?)?(?P<unit_to>[a-zA-Z]+)?$")

temperature_units = {
    'f': 'farenheit',
    'farenheit': 'farenheit',
    'c': 'celsius',
    'celsius': 'celsius',
    'centigrade': 'celsius',
}

distance_to_m = {
    'kilometer': 1000,
    'hectometer': 100,
    'decameter': 10,
    'meter': 1,
    'decimeter': 0.1,
    'centimeter': 0.01,
    'millimeter': 0.001,

    'twip': 0.0000176389,
    'thou': 0.0000254,
    'barleycorn': 0.0084667,
    'inch': 0.0254,
    'foot': 0.3048,
    'yard': 0.9144,
    'chain': 20.1168,
    'furlong': 201.168,
    'mile': 1609.344,
    'league': 4828.032,
    'nautical mile': 1852
}

distance_plurals = {
    'inch': 'inches',
    'foot': 'feet',
}

distance_units = {
    'kilometer': 'kilometer',
    'kilometre': 'kilometer',
    'km': 'kilometer',
    'hectometer': 'hectometer',
    'hectometre': 'hectometer',
    'hm': 'hectometer',
    'decameter': 'decameter',
    'decametre': 'decameter',
    'dam': 'decameter',
    'meter': 'meter',
    'metre': 'meter',
    'm': 'meter',
    'decimeter': 'decimeter',
    'decimetre': 'decimeter',
    'dm': 'decimeter',
    'centimeter': 'centimeter',
    'centimetre': 'centimeter',
    'cm': 'centimeter',
    'millimeter': 'millimeter',
    'millimetre': 'millimeter',
    'mm': 'millimeter',

    'twip': 'twip',
    'thou': 'thou',
    'mil': 'thou',
    'th': 'thou',
    'barleycorn': 'barleycorn',
    'inch': 'inch',
    'inches': 'inch',
    'in': 'inch',
    'foot': 'foot',
    'feet': 'foot',
    'ft': 'foot',
    'yard': 'yard',
    'yd': 'yard',
    'chain': 'chain',
    'ch': 'chain',
    'furlong': 'furlong',
    'fur': 'furlong',
    'mile': 'mile',
    'mi': 'mile',
    'league': 'league',
    'lea': 'league',
    'nmi': 'nautical mile'
}

weight_to_g = {
    'metric ton': 1000000,
    'kilogram': 1000,
    'gram': 1,
    'milligram': 0.001,
    'microgram': 0.000001,

    'grain': 0.06479891,
    'drachm': 1.7718451953125,
    'ounce': 28.349523125,
    'pound': 453.59237,
    'stone': 6350.29318,
    'quarter': 12700.58636,
    'UK ton': 1016046.9088,
    'US ton': 907184.74
}

weight_plurals = {
    'stone': 'stone'
}

weight_units = {
    't': ['metric ton', 'US ton', 'UK ton'],
    'tonne': 'metric_ton',
    'ton': ['metric ton', 'US ton', 'UK ton'],
    'kilogram': 'kilogram',
    'kg': 'kilogram',
    'gram': 'gram',
    'g': 'gram',
    'milligram': 'milligram',
    'mg': 'milligram',
    'microgram': 'microgram',
    'ug': 'microgram',
    'µg': 'microgram',

    'grain': 'grain',
    'gr': 'grain',
    'drachm': 'drachm',
    'dram': 'drachm',
    'dr': 'drachm',
    'ounce': 'ounce',
    'oz': 'ounce',
    'pound': 'pound',
    'lb': 'pound',
    'stone': 'stone',
    'st': 'stone',
    'quarter': 'quarter',
    'qr': 'quarter',
    'qrt': 'quarter',

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

    if unit_from.lower().strip('s') in distance_units and unit_to.lower().strip('s') in distance_units:
        return await distance_convert(bot, amount, distance_units[unit_from.lower().strip('s')], distance_units[unit_to.lower().strip('s')])
    if unit_from.lower() in distance_units and unit_to.lower() in distance_units:
        return await distance_convert(bot, amount, distance_units[unit_from.lower()], distance_units[unit_to.lower()])


    # weight conversions
    if unit_from.lower().strip('s') in weight_units and unit_to.lower().strip('s') in weight_units:
        return await weight_convert(bot, room, event, amount, weight_units[unit_from.lower().strip('s')], weight_units[unit_to.lower().strip('s')])
    if unit_from.lower() in weight_units and unit_to.lower() in weight_units:
        return await weight_convert(bot, room, event, amount, weight_units[unit_from.lower()], weight_units[unit_to.lower()])


    await price_convert(bot, amount, unit_from.upper(), unit_to.upper())


async def price_convert(irc: Jenny, amount, coinin, coinout):
    message = ""
    if coinin.upper() == 'ARSE':
        coinin = 'ARS'
    if coinout.upper() == 'ARSE':
        coinout = 'ARS'
    info = requests.get("https://min-api.cryptocompare.com/data/price?fsym=" + coinin + "&tsyms=" + coinout).json()
    if 'Error' in str(info):
        return await irc.reply(info['Message'])
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


async def distance_convert(irc: Jenny, amount, unit_from, unit_to):
    unit_to_m = amount * distance_to_m[unit_from]
    p = inflect.engine()

    m_unit_to = unit_to_m / distance_to_m[unit_to]
    uni_fro = distance_plurals.get(unit_from, unit_from + 's') if amount != 1 else unit_from
    uni_too = distance_plurals.get(unit_to, unit_to + 's') if m_unit_to != 1 else unit_to
    amount = int(amount) if int(amount) == amount else round(amount, 4)
    m_unit_to = int(m_unit_to) if int(m_unit_to) == m_unit_to else round(m_unit_to, 4)

    await irc.reply(f"\002{amount}\002 \002{uni_fro}\002 => "
                    f"\002{m_unit_to}\002 \002{uni_too}\002")


async def weight_convert(irc: Jenny, room, event, amount, unit_from, unit_to):
    resp = ""
    if type(unit_from) != list:
        unit_from = [unit_from]
    if type(unit_to) != list:
        unit_to = [unit_to]

    for u_from in unit_from:
        for u_to in unit_to:
            unit_to_g = amount * weight_to_g[u_from]

            g_unit_to = unit_to_g / weight_to_g[u_to]
            uni_fro = weight_plurals.get(u_from, u_from + 's') if amount != 1 else u_from
            uni_too = weight_plurals.get(u_to, u_to + 's') if g_unit_to != 1 else u_to
            amount = int(amount) if int(amount) == amount else round(amount, 4)
            g_unit_to = int(g_unit_to) if int(g_unit_to) == g_unit_to else round(g_unit_to, 4)
            resp += f"\002{amount}\002 \002{uni_fro}\002 => \002{g_unit_to}\002 \002{uni_too}\002<br/>"

    if resp.count("<br/>") > 1:
        resp = "<br/>" + resp
    await irc.message(room.room_id, await irc.source_tag(event.sender) + resp, p_html=True)
