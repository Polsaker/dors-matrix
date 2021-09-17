""" return a character that is broken on your keyboard """
from nio import MatrixRoom

from dors import command_hook, Jenny, HookMessage


@command_hook(['keys', 'char'])
async def missingkeys(bot: Jenny, room: MatrixRoom, event: HookMessage):
    await bot.say("`1234567890-=<>~?!@#$%^&*()_+ abcdefghijklmnopqrstuvwxyz ABCDEFGHIJKLMNOPQRSTUVWXYZ")
