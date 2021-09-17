""" return a character that is broken on your keyboard """
from dors import command_hook


@command_hook(['keys', 'char'])
def missingkeys(irc, ev):
    irc.message(ev.replyto, "`1234567890-=<>~?!@#$%^&*()_+ abcdefghijklmnopqrstuvwxyz ABCDEFGHIJKLMNOPQRSTUVWXYZ")
