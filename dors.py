#!/usr/bin/env python
# -*- coding: utf-8

from matrix_client.client import MatrixClient
from urllib.parse import quote
import config
import json
import os
import time
import traceback
import re
import threading
import html


class Message(object):
    def __init__(self, source, target, message, event_id, cli=None, evt=None):
        self.source = source
        self.target = target
        self.message = message
        self.chunk = evt
        
        self.args = list(filter(None, message.split(" ")[1:]))
        self.text = " ".join(self.args)
        self.replyto = target  # IRC compat
        
        self.event_id = event_id
        
        self.source_obj = cli.get_user(self.source)
        self.source_tag = f'<a href="https://matrix.to/#/{self.source}">{self.source_obj.get_display_name()}</a>'
    
    def __repr__(self):
        return "<Message from:{0} to:{1} - {2}>".format(self.source, self.target, self.message)


IRC_COLOR_MAP = {
    '0': 'white', '00': 'white',
    '1': 'black', '01': 'black',
    '2': '#00007F', '02': '#00007F',
    '3': 'green', '03': 'green',
    '4': 'red', '04': 'red',
    '5': '#7F0000', '05': '#7F0000',
    '6': '#9C009C', '06': '#9C009C',
    '7': '#FC7F00', '07': '#FC7F00',
    '8': '#FFFF00', '08': '#FFFF00',
    '9': 'lime', '09': 'lime',
    '10': 'teal',
    '11': 'aqua',
    '12': 'blue',
    '13': 'fuchsia',
    '14': '#7F7F7F',
    '15': '#D2D2D2'
}
 

class Dors(object):
    def __init__(self):
        self.client = None
        self.config = config

        self.stuffHandlers = []
        self.startupHooks = []
        self.commandHooks = []
        self.plugins = {}
        self.lastheardfrom = {}
        self.sourcehistory = []

        modules = []
        whitelistonly = False
        for module in os.listdir(os.path.dirname("modules/")):
            if module == '__init__.py' or module[-3:] != '.py':
                continue
            module = module[:-3]
            modules.append(module)
            if module in config.whitelistonly_modules:
                whitelistonly = True

        if whitelistonly:
            for module in config.whitelistonly_modules:
                self.load_module(module)
        else:
            for module in modules:
                if module in config.disabled_modules:
                    continue
                self.load_module(module)
    
    def connect(self):
        try:
            tok = json.load(open('.token', 'r'))
            self.client = MatrixClient(config.homeserver, token=tok['token'], user_id=tok['user_id'])
        except FileNotFoundError:
            self.client = MatrixClient(config.homeserver)
            token = self.client.login(username=config.username, password=config.password, sync=True)
            json.dump({'token': token, 'user_id': self.client.user_id}, open('.token', 'w'))
        
        self.client.add_invite_listener(self.on_invite)
        self.client.add_listener(self.on_message, 'm.room.message')
        
        for hook in self.startupHooks:
            try:
                t = threading.Thread(target=hook['func'], args=(self,))
                t.daemon = True
                t.start()
            except Exception as e:
                print(traceback.format_exc())

                tb = repr(e) + traceback.format_exc().splitlines()[-3]
                print("Error in {0} module: {1}".format(hook['module'], tb))

    def load_module(self, module):
        print("Loading", module)
        themodule = __import__("modules." + module, locals(), globals())
        themodule = getattr(themodule, module)

        self.plugins[module] = themodule
        # Iterate over all the methods in the module to find handlers
        funcs = [f for _, f in themodule.__dict__.items() if callable(f)]
        for func in funcs:
            if not getattr(func, '_handler', False):
                continue
            if getattr(func, '_handler') == 1:  # Stuff handler.
                self.stuffHandlers.append({
                    'regex': func._regex,
                    'func': func,
                    'module': module
                })
            elif getattr(func, '_handler') == 2:  # startup
                self.startupHooks.append({
                    'func': func,
                    'module': module
                })
            elif getattr(func, '_handler') == 3:  # command
                self.commandHooks.append({
                    'commands': func._commands,
                    'help': func._help,
                    'func': func,
                    'module': module
                })

    # callbacks
    def on_invite(self, room_id, _):
        if room_id.split(':')[1] in config.allowed_servers:
            self.client.join_room(room_id)
            print("Got an invite for", room_id)
        else:
            print("Got an invite for", room_id, "but it's not in an allowed_server")

    def on_message(self, roomchunk):
        # if it's a notice we ignore it
        if roomchunk['content']['msgtype'] == 'm.notice':
            return
        event = Message(roomchunk['sender'], roomchunk['room_id'], roomchunk['content']['body'], roomchunk['event_id'],
                        cli=self.client, evt=roomchunk)
        source, target, message = (roomchunk['sender'], roomchunk['room_id'], roomchunk['content']['body'])
        print(event)
        # Commands
        if message.strip().startswith(config.prefix):
            try:
                # if it's been six seconds since this person has made a command...
                # And they made the last two commands...
                # And the person is not an administrator...
                last_msg = time.time() - self.lastheardfrom[source]
                is_spammy = source == self.sourcehistory[-2] and source == self.sourcehistory[-1]
                if last_msg < 6 and is_spammy and not self.isadmin(source):
                    return  # Ignore it
            except (KeyError, IndexError):
                pass
            finally:
                self.lastheardfrom[source] = time.time()
                self.sourcehistory.append(source)

            command = message.strip().split()[0].replace(config.prefix, '', 1)
            args = message.strip().split()[1:]
            
            try:
                pot = next((item for item in self.commandHooks if command in item['commands']))
                try:
                    self.send_read_receipt(event.target, event.event_id)
                    pot['func'](self.wrapper(event), event)
                except Exception as e:
                    print(traceback.format_exc())
                    tb = repr(e) + traceback.format_exc().splitlines()[-3]
                    self.message(target, "Error in {0} module: {1}".format(pot['module'], tb))
            except StopIteration:
                pass
        
        # Hooks
        # Iterate over all the stuff handlers.
        for stuff in self.stuffHandlers:
            # try to find a match
            if stuff['regex'].match(message):
                event.match = stuff['regex'].match(message)
                # Got a match. Call the function
                try:
                    stuff['func'](self.wrapper(event), event)
                except Exception as e:
                    print(traceback.format_exc())

                    tb = repr(e) + traceback.format_exc().splitlines()[-3]
                    self.message(target, "Error in {0} module: {1}".format(stuff['module'], tb))

    def message(self, target, message, p_html=False, message_type='m.notice'):
        """ Compatibility layer for porting IRC modules """
        message = str(message)
        if "\002" in message or "\003" in message or "\x1f" in message or "\x1d" in message or p_html:
            # transform from IRC to HTML and send..
            if not p_html:
                message = html.escape(message)
            message = re.sub('\002(.*?)\002', '<b>\\1</b>', message)
            message = re.sub('\x1f(.*?)\x1f', '<u>\\1</u>', message)
            message = re.sub('\x1d(.*?)\x1d', '<i>\\1</i>', message)

            def replcolor(m):
                return '<font color="{0}">{1}</font>'.format(IRC_COLOR_MAP[m.group(1)], m.group(3))
            message = re.sub(r'\003(\d{1,2})(?:,(\d{1,2}))?(.*?)\003', replcolor, message)
            return self.html_message(target, message, message_type)
        self.client.api.send_message_event(room_id=target, event_type='m.room.message',
                                           content={'body': message, 'msgtype': message_type})

    def send_read_receipt(self, room_id, event_id):
        path = "/rooms/%s/receipt/m.read/%s" % (
            quote(room_id, safe=''), quote(str(event_id), safe=''),
        )
        return self.client.api._send("POST", path, {})  # noqa

    def send_typing(self, room_id, typing=True, timeout=10000):
        user_id = self.client.user_id
        path = "/rooms/%s/typing/%s" % (
            quote(room_id, safe=''), quote(str(user_id), safe=''),
        )
        content = {
            "typing": typing,
            "timeout": timeout
        }
        return self.client.api._send("PUT", path, content)  # noqa
    
    def html_message(self, target, message, message_type='m.notice'):
        stripped = re.sub('<[^<]+?>', '', html.unescape(message))

        self.client.api.send_message_event(room_id=target, event_type='m.room.message',
                                           content={'formatted_body': message, 'format': 'org.matrix.custom.html',
                                                    'body': stripped, 'msgtype': message_type})

    def isadmin(self, user):
        if user not in config.admins:
            return False
        return True
    
    def get_plugin(self, plugin):
        try:
            return self.plugins[plugin]
        except KeyError:
            return False

    def wrapper(self, event):
        """ we wrap ourselves before passing to modules """
        class BotWrapper(object):
            def __init__(self, bot):
                self._bot = bot

            def __getattr__(self, attr):
                if attr == 'say' or attr == 'msg':
                    return lambda msg: self._bot.message(event.target, msg)
                elif attr == 'reply':
                    return lambda msg: self._bot.message(event.target, event.source_tag + ': ' + html.escape(msg),
                                                         p_html=True)
                
                return getattr(self._bot, attr)

            def __setattr__(self, attr, value):
                if attr == '_bot':
                    return super(BotWrapper, self).__setattr__(attr, value)
                else:
                    return setattr(self._bot, attr, value)

        return BotWrapper(self)


if __name__ == '__main__':
    mb = Dors()
    mb.connect()

    def foo(e):
        print(e)
        
    mb.client.listen_forever(exception_handler=foo)


# Decorators and other shit
def stuffHook(regex):
    def wrap(func):
        func._handler = 1 # 1: Stuff handler.
        func._regex = re.compile(regex)
        return func
    return wrap


def commandHook(commands, help=""):
    if type(commands) == str:
        commands = [commands]

    def wrap(func):
        func._handler = 3 # 3: Command.
        func._commands = commands
        func._help = help
        return func
    return wrap


def startupHook(dummy=None):
    def wrap(func):
        func._handler = 2 # 2: function called when bot connects.
        return func
    return wrap
