from nio import MatrixRoom

import config
from dors import command_hook, Jenny, HookMessage
import sys


@command_hook('load', help="load <module> -- Loads a module")
async def load(bot: Jenny, room: MatrixRoom, event: HookMessage):
    if event.sender not in config.admins:
        return await bot.say("Not authorized")
    
    await bot.say("Trying to load {0}.py".format(event.args[0]))
    bot.load_module(event.args[0])


@command_hook('unload', help="unload <module> -- Unloads a module")
async def unload(bot: Jenny, room: MatrixRoom, event: HookMessage):
    if event.sender not in config.admins:
        return await bot.say("Not authorized")
    
    await bot.say("Trying to unload {0}.py".format(event.args[0]))
    unload_module(bot, event.args[0])


@command_hook('reload', help="reload <module> -- Unloads and then reloads a module")
async def reload(bot: Jenny, room: MatrixRoom, event: HookMessage):
    if event.sender not in config.admins:
        return await bot.say("Not authorized")
    
    await bot.say("Trying to reload {0}.py".format(event.args[0]))
    unload_module(bot, event.args[0])
    bot.load_module(event.args[0])


def unload_module(bot: Jenny, module):
    # No core way of unloading stuff here. We have to do it ourselves.
    # 1 - Check if the module is loaded
    try:
        bot.plugins[module]
    except KeyError:
        raise Exception("{0}.py is not loaded".format(module))

    # 2 - Delete all the hooks
    for h in bot.stuffHandlers[:]:
        if h['module'] == module:
            bot.stuffHandlers.remove(h)
    
    for h in bot.startup_hooks[:]:
        if h['module'] == module:
            bot.startup_hooks.remove(h)
    
    for h in bot.command_hooks[:]:
        if h['module'] == module:
            bot.command_hooks.remove(h)

    # 3 - Unregister module
    del bot.plugins[module]

    # 4 - Try to remove stuff
    del sys.modules['modules.' + module]
