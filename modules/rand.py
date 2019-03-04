from dors import commandHook
import random

@commandHook(['pick', 'choose', 'choice'], help=".choice <something> <something else> [third choice] ... -- Makes a choice for you")
def choice(irc, event):
    if len(event.args) < 2:
        return irc.message(event.replyto, "Not enough parameters. Usage: .choice <something> <something else> [third choice]")
    
    irc.message(event.replyto, "{0}: {1}".format(event.source, random.choice(event.args)))

@commandHook(['rand', 'random'], help=".random [arg1] [arg2] ... -- Picks a random number between arg1 and arg2 (If one argument is missing it assumes the only argument is the upper limit and the lower is 1, and if both arguments are missing it generates a number between 1 and 10)")
def rand(irc, event):
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
                
        if (bottom <= 0) or (top <= 0):
            return irc.message(event.replyto, "The limits must be higher than 0")
        if bottom >= top:
            return irc.message(event.replyto, "Lolwut?")

    irc.message(event.replyto, "{0}: Your random integer is {1}".format(event.source, random.randint(1, top)))
