from nio import MatrixRoom

import config
from dors import command_hook, HookMessage, Jenny
import random
import itertools
import codecs


def write_quote(quote):
    fn = open('quotes.txt', 'a')
    fn.write(quote)
    fn.write('\n')
    fn.close()


@command_hook('addquote', help=".addquote <nick> something they said -- Adds the quote to the quote database.")
async def addquote(bot: Jenny, room: MatrixRoom, event: HookMessage):
    text = " ".join(event.args)
    if not text:
        return await bot.say("No quote provided.")
    
    write_quote(text)
    await bot.say("Quote added.")


@command_hook('quote', help=".quote [nick|numer] - Displays a given quote or a random one if no parameter is specified.")
async def quote(bot: Jenny, room: MatrixRoom, event: HookMessage):
    try:
        param = event.args[0]
    except IndexError:
        param = None
    
    try:
        fn = codecs.open('quotes.txt', 'r', encoding='utf-8')
    except:
        return await bot.say("Please add a quote first.")
    
    lines = fn.readlines()
    if len(lines) < 1:
        return await bot.say("There are currently no quotes saved.")
    
    MAX = len(lines)
    fn.close()
    random.seed()

    if param is not None:
        try:
            number = int(param)
            if number < 0:
                number = MAX - abs(number) + 1
        except:
            nick = "<" + param + ">"

            indices = range(1, len(lines) + 1)
            selectors = map(lambda x: x.split()[0] == nick, lines)
            filtered_indices = list(itertools.compress(indices, selectors))

            if len(filtered_indices) < 1:
                return await bot.say('No quotes by that nick!')

            filtered_index_index = random.randint(1, len(filtered_indices))
            number = filtered_indices[filtered_index_index - 1]
    else:
        number = random.randint(1, MAX)

    if not (0 <= number <= MAX):
        await bot.say("I'm not sure which quote you would like to see.")
    else:
        if lines:
            if number == 0:
                return await bot.say('There is no "0th" quote!')
            else:
                line = lines[number - 1].replace('\n', '').strip()
            await bot.say('Quote \002{0}\002 of \002{1}\002: {2}'.format(number, MAX, line))
        else:
            await bot.say("There are currently no quotes saved.")


@command_hook(['delquote', 'rmquote'], help=".delquote <number> -- Deletes a quote from the quote database.")
async def delquote(bot: Jenny, room: MatrixRoom, event: HookMessage):
    if event.sender not in config.admins:
        return
    
    try:
        param = event.args[0]
    except IndexError:
        return await bot.say("No argument provided.")

    try:
        fn = open('quotes.txt', 'r')
    except:
        return await bot.say('No quotes to delete.')

    lines = fn.readlines()
    MAX = len(lines)
    fn.close()

    try:
        number = int(param)
    except:
        await bot.say('Please enter the quote number you would like to delete.')
        return

    if number > 0:
        newlines = lines[:number - 1] + lines[number:]
    elif number == 0:
        return await bot.say('There is no "0th" quote!')
    elif number == -1:
        newlines = lines[:number]
    else:
        # number < -1
        newlines = lines[:number] + lines[number + 1:]
    fn = open('quotes.txt', 'w')
    for line in newlines:
        txt = line
        if txt:
            fn.write(txt)
            if txt[-1] != '\n':
                fn.write('\n')
    fn.close()
    await bot.say('Successfully deleted quote \002{0}\002.'.format(number))

