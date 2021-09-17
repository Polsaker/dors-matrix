from nio import MatrixRoom

from dors import command_hook, Jenny, HookMessage
import unicodedata


@command_hook(['u'], help="Looks up a unicode character (10 maximum). Usage: u <character>")
async def u(bot: Jenny, room: MatrixRoom, event: HookMessage):
    if not event.args:
        return await bot.reply("Usage: u <character>")
    
    chars = event.args[0]
    if len(chars) > 10:
        return await bot.reply("Sorry, your input is too long! The maximum is 6 characters")
    
    reply = ""
    for char in chars:
        try:
            name = unicodedata.name(char).replace('-{0:04X}'.format(ord(char)), '')
        except ValueError:
            name = "No name found"
        reply += "U+{0:04X} {1} ({2}) ".format(ord(char), name, char)
    
    await bot.say(reply)


@command_hook(['sc'])
async def supercombiner(bot: Jenny, room: MatrixRoom, event: HookMessage):
    """.sc -- displays the infamous supercombiner"""
    # ported from jenni
    s = 'u'
    for i in iter(range(1, 3000)):
        if unicodedata.category(chr(i)) == "Mn":
            s += chr(i)
        if len(s) > 100:
            break
    await bot.say(s)
