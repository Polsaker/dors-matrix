from matrix_client.client import MatrixClient
import config
import json
import os
import time
import traceback
import re
import threading
import html

class Message(object):
    def __init__(self, source, target, message, cli=None):
        self.source = source
        self.target = target
        self.message = message
        
        self.args = list(filter(None, message.split(" ")[1:]))
        self.text = " ".join(self.args)
        self.replyto = target  # IRC compat
        
        self.source_obj = cli.get_user(self.source)
        self.source_tag = '<a href="https://matrix.to/#/{0}">{1}</a>'.format(self.source, self.source_obj.get_display_name())
    
    def __repr__(self):
        return "<Message from:{0} to:{1} - {2}>".format(self.source, self.target, self.message)
        
IRC_COLOR_MAP = {'0': '#FFFFFF', '00': '#FFFFFF',
 '1': '#000000', '01': '#000000',
 '2': '#00007F', '02': '#00007F',
 '3': '#009300', '03': '#009300',
 '4': '#FF0000', '04': '#FF0000',
 '5': '#7F0000', '05': '#7F0000',
 '6': '#9C009C', '06': '#9C009C',
 '7': '#FC7F00', '07': '#FC7F00',
 '8': '#FFFF00', '08': '#FFFF00',
 '9': '#00FC00', '09': '#00FC00',
 '10': '#009393',
 '11': '#00FFFF',
 '12': '#0000FC',
 '13': '#FF00FF',
 '14': '#7F7F7F',
 '15': '#D2D2D2'}
 

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

        if whitelistonly == True:
            for module in config.whitelistonly_modules:
                self.loadModule(module)
        else:
            for module in modules:
                if module in config.disabled_modules:
                    continue
                self.loadModule(module)
    
    def connect(self):
        try:
            tok = json.load(open('.token', 'r'))
            self.client = MatrixClient(config.homeserver, token=tok['token'], user_id=tok['user_id'])
        except FileNotFoundError:
            self.client = MatrixClient(config.homeserver)
            token = self.client.login_with_password(username=config.username, password=config.password)
            json.dump({'token': token, 'user_id': self.client.user_id}, open('.token', 'w'))
        
        self.client.add_invite_listener(self.on_invite)
        self.client.add_listener(self.on_message, 'm.room.message')
        
        for hook in self.startupHooks:
            try:
                t = threading.Thread(target=hook['func'], args=(self,))
                t.daemon=True
                t.start()
            except Exception as e:
                print(traceback.format_exc())

                tb = repr(e) + traceback.format_exc().splitlines()[-3]
                print("Error in {0} module: {1}".format(hook['module'], tb))



    def loadModule(self, module):
        print("Loading", module)
        themodule = __import__("modules." + module, locals(), globals())
        themodule = getattr(themodule, module)

        self.plugins[module] = themodule
        # Iterate over all the methods in the module to find handlers
        funcs = [f for _, f in themodule.__dict__.items() if callable(f)]
        for func in funcs:
            try:
                func._handler
            except:
                continue # nothing to do here.
            if func._handler == 1: # Stuff handler.
                self.stuffHandlers.append({'regex': func._regex, 'func': func, 'module': module})
            elif func._handler == 2: # startup
                self.startupHooks.append({'func': func, 'module': module})
            elif func._handler == 3: # command
                self.commandHooks.append({'commands': func._commands, 'help': func._help, 'func': func, 'module': module})



    # callbacks
    def on_invite(self, room_id, state):
        self.client.join_room(room_id)
        print("Got an invite for", room_id, "Display name:", state['events'][0]['content']['displayname'])


    def on_message(self, roomchunk):
        event = Message(roomchunk['sender'], roomchunk['room_id'], roomchunk['content']['body'], cli=self.client)
        source, target, message = (roomchunk['sender'], roomchunk['room_id'], roomchunk['content']['body'])
        print(event)
        # Commands
        if message.strip().startswith(config.prefix):
            try:
                if ((time.time() - self.lastheardfrom[source] < 6) and # if it's been six seconds since this person has made a command...
                    (source == self.sourcehistory[-2] and source == self.sourcehistory[-1]) and # And they made the last two commands...
                    not self.isadmin(source)): # And the person is not an administrator...
                    return # Ignore it
            except (KeyError, IndexError):
                pass
            finally:
                self.lastheardfrom[source] = time.time()
                self.sourcehistory.append(source)

            command = message.strip().split()[0].replace(config.prefix, '', 1)
            args = message.strip().split()[1:]
            
            try:
                pot = next((item for item in self.commandHooks if command in item['commands']))
            except StopIteration:
                pot = False

            if pot:
                try:
                    pot['func'](self.wrapper(event), event)
                except Exception as e:
                    print(traceback.format_exc())
                    tb = repr(e) + traceback.format_exc().splitlines()[-3]
                    self.message(target, "Error in {0} module: {1}".format(pot['module'], tb))
        
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


    def message(self, target, message, p_html=False):
        """ Compatibility layer for porting IRC modules """
        print(message)
        if "\002" in message or "\003" in message or "\x1f" in message or "\x1d" in message or p_html:
            # transform from IRC to HTML and send..
            if not p_html:
                message = html.escape(message)
            message = re.sub('\002(.*?)\002', '<b>\\1</b>', message)
            message = re.sub('\x1f(.*?)\x1f', '<u>\\1</u>', message)
            message = re.sub('\x1d(.*?)\x1d', '<i>\\1</i>', message)
            def replcolor(m):
                return '<font color="{0}">{1}</font>'.format(IRC_COLOR_MAP[m.group(1)], m.group(2))
            message = re.sub('\003(\d{1,2})(.*?)\003', replcolor, message)
            return self.html_message(target, message)
        self.client.api.send_message(target, message)
    
    def html_message(self, target, message):
        stripped = re.sub('<[^<]+?>', '', html.unescape(message))

        self.client.api.send_message_event(room_id=target, event_type='m.room.message',
                                           content={'formatted_body': message, 'format': 'org.matrix.custom.html',
                                                    'body': stripped, 'msgtype': 'm.text'})

    def isadmin(self, user):
        if user not in config.admins:
            return False
        return True
    
    def getPlugin(self, plugin):
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
                    return (lambda msg: self._bot.message(event.target, msg))
                elif attr == 'reply':
                    return (lambda msg: self._bot.message(event.target, event.source_tag + ': ' + html.escape(msg), p_html=True))
                
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
