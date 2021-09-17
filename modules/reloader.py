from dors import command_hook
import sys


@command_hook('load', help="load <module> -- Loads a module")
def load(irc, event):
    if not irc.isadmin(event.source):
        return irc.message(event.replyto, "Not authorized")
    
    irc.message(event.replyto, "Trying to load {0}.py".format(event.args[0]))
    irc.load_module(event.args[0])


@command_hook('unload', help="unload <module> -- Unloads a module")
def unload(irc, event):
    if not irc.isadmin(event.source):
        return irc.message(event.replyto, "Not authorized")
    
    irc.message(event.replyto, "Trying to unload {0}.py".format(event.args[0]))
    unload_module(irc, event.args[0])


@command_hook('reload', help="reload <module> -- Unloads and then reloads a module")
def reload(irc, event):
    if not irc.isadmin(event.source):
        return irc.message(event.replyto, "Not authorized")
    
    irc.message(event.replyto, "Trying to reload {0}.py".format(event.args[0]))
    unload_module(irc, event.args[0])
    irc.load_module(event.args[0])


def unload_module(irc, module):
    # No core way of unloading stuff here. We have to do it ourselves.
    # 1 - Check if the module is loaded
    try:
        irc.plugins[module]
    except KeyError:
        raise Exception("{0}.py is not loaded".format(module))

    # 2 - Delete all the hooks
    for h in irc.stuffHandlers[:]:
        if h['module'] == module:
            irc.stuffHandlers.remove(h)
    
    for h in irc.startup_hooks[:]:
        if h['module'] == module:
            irc.startup_hooks.remove(h)
    
    for h in irc.command_hooks[:]:
        if h['module'] == module:
            irc.command_hooks.remove(h)

    # 3 - Unregister module
    del irc.plugins[module]

    # 4 - Try to remove stuff
    del sys.modules['modules.' + module]
