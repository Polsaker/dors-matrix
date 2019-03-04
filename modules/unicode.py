from dors import commandHook
import unicodedata

@commandHook(['u'], help="Looks up a unicode character (10 maximum). Usage: u <character>")
def u(irc, ev):
    if not ev.args:
        return irc.reply("Usage: u <character>")
    
    chars = ev.args[0]
    if len(chars) > 10:
        return irc.reply("Sorry, your input is too long! The maximum is 6 characters")
    
    reply = ""
    for char in chars:
        try:
            name = unicodedata.name(char).replace('-{0:04X}'.format(ord(char)), '')
        except ValueError:
            name = "No name found"
        reply += "U+{0:04X} {1} ({2}) ".format(ord(char), name, char)
    
    irc.say(reply)

@commandHook(['sc'])
def supercombiner(bot, ev):
    """.sc -- displays the infamous supercombiner"""
    # ported from jenni
    s = 'u'
    for i in iter(range(1, 3000)):
        if unicodedata.category(chr(i)) == "Mn":
            s += chr(i)
        if len(s) > 100:
            break
    bot.say(s)
