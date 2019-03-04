from dors import commandHook
import random
import itertools
import codecs

def write_quote(quote):
    fn = open('quotes.txt', 'a')
    fn.write(quote)
    fn.write('\n')
    fn.close()

@commandHook('addquote', help=".addquote <nick> something they said -- Adds the quote to the quote database.")
def addquote(irc, ev):
    if not ev.text:
        return irc.message(ev.replyto, "No quote provided.")
    
    write_quote(ev.text)
    irc.message(ev.replyto, "Quote added.")

@commandHook('quote', help=".quote [nick|numer] - Displays a given quote or a random one if no parameter is specified.")
def quote(irc, ev):
    try:
        param = ev.args[0]
    except IndexError:
        param = None
    
    try:
        fn = codecs.open('quotes.txt', 'r', encoding='utf-8')
    except:
        return irc.message(ev.replyto, "Please add a quote first.")
    
    lines = fn.readlines()
    if len(lines) < 1:
        return irc.message(ev.replyto, "There are currently no quotes saved.")
    
    MAX = len(lines)
    fn.close()
    random.seed()

    if param != None:
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
                return irc.message(ev.replyto, 'No quotes by that nick!')

            filtered_index_index = random.randint(1, len(filtered_indices))
            number = filtered_indices[filtered_index_index - 1]
    else:
        number = random.randint(1, MAX)

    
    if not (0 <= number <= MAX):
        irc.message(ev.replyto, "I'm not sure which quote you would like to see.")
    else:
        if lines:
            if number == 0:
                return irc.message(ev.replyto, 'There is no "0th" quote!')
            else:
                line = lines[number - 1].replace('\n', '').strip()
            irc.message(ev.replyto, 'Quote \002{0}\002 of \002{1}\002: {2}'.format(number, MAX, line))
        else:
            irc.message(ev.replyto, "There are currently no quotes saved.")

@commandHook(['delquote', 'rmquote'], help=".delquote <number> -- Deletes a quote from the quote database.")
def delquote(irc, ev):
    if not irc.isadmin(ev.source):
        return
    
    try:
        param = ev.args[0]
    except IndexError:
        return irc.message(ev.replyto, "No argument provided.")

    try:
        fn = open('quotes.txt', 'r')
    except:
        return irc.message(ev.replyto, 'No quotes to delete.')

    lines = fn.readlines()
    MAX = len(lines)
    fn.close()

    try:
        number = int(param)
    except:
        irc.message(ev.replyto, 'Please enter the quote number you would like to delete.')
        return

    if number > 0:
        newlines = lines[:number - 1] + lines[number:]
    elif number == 0:
        return irc.message(ev.replyto, 'There is no "0th" quote!')
    elif number == -1:
        newlines = lines[:number]
    else:
        ## number < -1
        newlines = lines[:number] + lines[number + 1:]
    fn = open('quotes.txt', 'w')
    for line in newlines:
        txt = line
        if txt:
            fn.write(txt)
            if txt[-1] != '\n':
                fn.write('\n')
    fn.close()
    irc.message(ev.replyto, 'Successfully deleted quote \002{0}\002.'.format(number))


@commandHook(['grab', 'grabquote'], help=".grab <nick> -- Creates a quote with the last line <nick> sent to the channel.")
def grab(irc, ev):
    find = irc.getPlugin('find')
    
    if not find:
        return irc.message(ev.replyto, '"find" module not loaded.')

    txt = ev.text

    if not txt:
        return irc.message(ev.replyto, 'Please provide a nick for me to look for recent activity.')

    parts = txt.split()

    if not parts:
        return irc.message(ev.replyto, 'Please provide me with a valid nick.')

    nick = parts[0]
    channel = ev.target.lower()

    quote_db = irc.recent_lines
        
    if quote_db and (channel in quote_db) and (nick in quote_db[channel]):
        quotes_by_nick = quote_db[channel][nick]
    else:
        return irc.message(ev.replyto, 'There are currently no existing quotes by the provided nick in this channel.')

    quote_by_nick = quotes_by_nick[-1][0]

    quote = '<%s> %s' % (nick, quote_by_nick)

    write_quote(quote)

    irc.message(ev.replyto, 'quote added: {0}'.format(quote))

