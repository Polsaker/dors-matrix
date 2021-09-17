from nio import MatrixRoom

from dors import command_hook, Jenny, HookMessage
import random


@command_hook(['pick', 'choose', 'choice'], help=".choice <something> <something else> [third choice] ... "
                                                 "-- Makes a choice for you")
async def choice(bot: Jenny, room: MatrixRoom, event: HookMessage):
    if len(event.args) < 2:
        return await bot.say("Not enough parameters. Usage: .choice <something> <something else> [third choice]")

    await bot.reply(random.choice(event.args))


@command_hook(['rand', 'random'], help=".random [arg1] [arg2] ... -- Picks a random number between arg1 and arg2 "
                                       "(If one argument is missing it assumes the only argument is the upper limit "
                                       "and the lower is 1, and if both arguments are missing it generates a number "
                                       "between 1 and 10)")
async def rand(bot: Jenny, room: MatrixRoom, event: HookMessage):
    bottom = 1
    top = 10
    if len(event.args):
        try:
            first = int(event.args[0])
        except:
            first = False
        
        try:
            last = int(event.args[1])
        except:
            last = False
        
        if not last:
            top = first
        else:
            bottom = first
            top = last
                
        if top <= 0:
            return await bot.say("The limits must be higher than 0")
        if bottom >= top:
            return await bot.say("Lolwut?")

    await bot.say("Your random integer is {0}".format(random.randint(1, top)))
