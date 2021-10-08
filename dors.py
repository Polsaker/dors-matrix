#!/usr/bin/env python3

import asyncio
import dataclasses
import html
import os
import sys
import json
import re
import time
import traceback
from dataclasses import dataclass

from typing import Optional, List, Coroutine

from nio import (AsyncClient, InviteEvent, LoginResponse, MatrixRoom, RoomMessageText, AsyncClientConfig,
                 RoomMessageFormatted, RoomMessageNotice)

import config


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


@dataclass
class HookMessage(RoomMessageFormatted):  # noqa
    @classmethod
    def _dict_factory(cls, data):
        return dict(x for x in data if x[1] is not None)

    @classmethod
    def from_roomessage(cls, msg: RoomMessageFormatted):
        if not isinstance(msg, dict):
            msg = dataclasses.asdict(msg, dict_factory=cls._dict_factory)

        temp = cls(body=msg['body'], format=msg['format'], formatted_body=msg['formatted_body'], source=msg['source'])
        for key, val in msg.items():
            setattr(temp, key, val)
        return temp

    @property
    def args(self) -> List[str]:
        cmdparts = self.body.replace(config.prefix, '', 1).lstrip(" *").strip().split()
        return list(filter(None, cmdparts[1:]))


class Jenny(AsyncClient):
    def __init__(self, homeserver, user, device_id='', store_path='', cli_config=None, ssl=None, proxy=None):
        # Calling super.__init__ means we're running the __init__ method
        # defined in AsyncClient, which this class derives from. That does a
        # bunch of setup for us automatically
        super().__init__(homeserver, user=user, device_id=device_id, store_path=store_path, config=cli_config, ssl=ssl,
                         proxy=proxy)

        # if the store location doesn't exist, we'll make it
        if store_path and not os.path.isdir(store_path):
            os.mkdir(store_path)

        self.stuffHandlers = []
        self.startup_hooks = []
        self.command_hooks = []
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

        # auto-join room invites
        self.add_event_callback(self.cb_autojoin_room, InviteEvent)  # noqa
        self.add_event_callback(self.on_message, RoomMessageText)  # noqa
        self.add_event_callback(self.on_message, RoomMessageNotice)  # noqa

    def get_module(self, module_name: str):
        return self.plugins[module_name]

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
                    'regex': func._regex,  # noqa
                    'func': func,
                    'module': module
                })
            elif getattr(func, '_handler') == 2:  # startup
                self.startup_hooks.append({
                    'func': func,
                    'module': module
                })
            elif getattr(func, '_handler') == 3:  # command
                self.command_hooks.append({
                    'commands': func._commands,  # noqa
                    'help': func._help,  # noqa
                    'func': func,
                    'module': module
                })

    async def login(self, *args, **kwargs) -> None:
        """Log in either using the global variables or (if possible) using the
        session details file.
        """
        if os.path.exists('credentials.json') and os.path.isfile('credentials.json'):
            try:
                with open('credentials.json', "r") as f:
                    credentials = json.load(f)
                    self.access_token = credentials['access_token']
                    self.user_id = credentials['user_id']
                    self.device_id = credentials['device_id']

                    # This loads our verified/blacklisted devices and our keys
                    self.load_store()
                    print(f"Logged in using stored credentials: {self.user_id} on {self.device_id}")
            except IOError as err:
                print(f"Couldn't load session from file. Logging in. Error: {err}")
            except json.JSONDecodeError:
                print("Couldn't read JSON file; overwriting")

        # We didn't restore a previous session, so we'll log in with a password
        if not self.user_id or not self.access_token or not self.device_id:
            # this calls the login method defined in AsyncClient from nio
            resp = await super().login(config.password, device_name=config.device_name)

            if isinstance(resp, LoginResponse):
                print("Logged in using a password; saving details to disk")
                self.__write_details_to_disk(resp)
            else:
                print(f"Failed to log in: {resp}")
                sys.exit(1)

    def trust_devices(self, user_id: str, device_list: Optional[str] = None) -> None:
        """Trusts the devices of a user.

        If no device_list is provided, all of the users devices are trusted. If
        one is provided, only the devices with IDs in that list are trusted.

        Arguments:
            user_id {str} -- the user ID whose devices should be trusted.

        Keyword Arguments:
            device_list {Optional[str]} -- The full list of device IDs to trust
                from that user (default: {None})
        """

        print(f"{user_id}'s device store: {self.device_store[user_id]}")

        # The device store contains a dictionary of device IDs and known
        # OlmDevices for all users that share a room with us, including us.

        # We can only run this after a first sync. We have to populate our
        # device store and that requires syncing with the server.
        for device_id, olm_device in self.device_store[user_id].items():
            if device_list and device_id not in device_list:
                # a list of trusted devices was provided, but this ID is not in
                # that list. That's an issue.
                print(f"Not trusting {device_id} as it's not in {user_id}'s pre-approved list.")
                continue

            if user_id == self.user_id and device_id == self.device_id:
                # We cannot explictly trust the device @alice is using
                continue

            self.verify_device(olm_device)
            print(f"Trusting {device_id} from user {user_id}")

    async def cb_autojoin_room(self, room: MatrixRoom, event: InviteEvent):
        """Callback to automatically joins a Matrix room on invite.

        Arguments:
            room {MatrixRoom} -- Provided by nio
            event {InviteEvent} -- Provided by nio
        """
        await self.join(room.room_id)

    async def on_message(self, room: MatrixRoom, event: RoomMessageText):
        """Callback to print all received messages to stdout.

        Arguments:
            room {MatrixRoom} -- Provided by nio
            event {RoomMessageText} -- Provided by nio
        """
        if event.decrypted:
            encrypted_symbol = "🛡 "
        else:
            encrypted_symbol = "⚠️ "
        print(f"{room.display_name} |{encrypted_symbol}| {room.user_name(event.sender)}: {event.body}")

        source = event.sender

        if source == self.user_id:
            return

        event = HookMessage.from_roomessage(dataclasses.asdict(event))

        if event.body.lstrip(" *").strip().startswith(config.prefix):
            try:
                # if it's been six seconds since this person has made a command...
                # And they made the last two commands...
                # And the person is not an administrator...
                last_msg = time.time() - self.lastheardfrom[source]
                is_spammy = source == self.sourcehistory[-2] and source == self.sourcehistory[-1]
                if last_msg < 6 and is_spammy and source not in config.admins:
                    return  # Ignore it
            except (KeyError, IndexError):
                pass
            finally:
                self.lastheardfrom[source] = time.time()
                self.sourcehistory.append(source)

            command_parts = event.body.replace(config.prefix, '', 1).lstrip(" *").strip().split()
            command = command_parts[0].lower()

            try:
                pot = next((item for item in self.command_hooks if command in item['commands']))
                try:
                    await self.room_read_markers(room.room_id, event.event_id, event.event_id)
                    await pot['func'](self.wrapper(room, event), room, event)
                except Exception as e:
                    print(traceback.format_exc())
                    tb = repr(e) + traceback.format_exc().splitlines()[-3]
                    await self.message(room.room_id, f"Error in {pot['module']} module: {tb}")
            except StopIteration:
                pass

            # Hooks
            # Iterate over all the stuff handlers.
        for stuff in self.stuffHandlers:
            # try to find a match
            if stuff['regex'].match(event.body):
                event.match = stuff['regex'].match(event.body)
                # Got a match. Call the function
                try:
                    await stuff['func'](self.wrapper(room, event), room, event)
                except Exception as e:
                    print(traceback.format_exc())

                    tb = repr(e) + traceback.format_exc().splitlines()[-3]
                    await self.message(room.room_id, f"Error in {stuff['module']} module: {tb}")

    async def message(self, target, message, p_html=False, message_type='m.notice'):
        """ Compatibility layer for porting IRC modules """
        message = str(message)
        if "\002" in message or "\003" in message or "\x1f" in message or "\x1d" in message or p_html:
            # transform from IRC to HTML and send..
            if not p_html:
                message = html.escape(message)
            message = re.sub('\002(.*?)\002', '<b>\\1</b>', message)
            message = re.sub('\x1f(.*?)\x1f', '<u>\\1</u>', message)
            message = re.sub('\x1d(.*?)\x1d', '<i>\\1</i>', message)
            message = message.replace("\n\n", "<br/>")

            def replcolor(m):
                return '<font color="{0}">{1}</font>'.format(IRC_COLOR_MAP[m.group(1)], m.group(3))

            message = re.sub(r'\003(\d{1,2})(?:,(\d{1,2}))?(.*?)\003', replcolor, message)
            return await self.html_message(target, message, message_type)

        return await self.room_send(
            room_id=target,
            message_type="m.room.message",
            content={
                "msgtype": message_type,
                "body": message
            },
            ignore_unverified_devices=True
        )

    async def html_message(self, target, message, message_type='m.notice'):
        stripped = re.sub('<[^<]+?>', '', html.unescape(message))

        return await self.room_send(
            room_id=target,
            message_type="m.room.message",
            content={
                'formatted_body': message,
                'format': 'org.matrix.custom.html',
                "msgtype": message_type,
                "body": stripped
            },
            ignore_unverified_devices=True
        )

    async def source_tag(self, source):
        displayname = await self.get_displayname(source)
        return f'<a href="https://matrix.to/#/{source}">{displayname.displayname}</a>'

    async def say(self, message):
        """ Dummy definition (wrapped) """

    async def reply(self, message):
        """ Dummy definition (wrapped) """

    def wrapper(self, room: MatrixRoom, event: RoomMessageFormatted):
        """ we wrap ourselves before passing to modules """

        class BotWrapper(object):
            def __init__(self, bot: Jenny):
                self._bot: Jenny = bot

            async def w_message(self, message: str):
                await self._bot.message(room.room_id, message)

            async def w_reply(self, message):
                await self._bot.message(
                    room.room_id,
                    await self._bot.source_tag(event.sender) + ': ' + html.escape(message),
                    p_html=True
                )

            def __getattr__(self, attr):
                if attr == 'say' or attr == 'msg':
                    return self.w_message
                elif attr == 'reply':
                    return self.w_reply

                return getattr(self._bot, attr)

            def __setattr__(self, attr, value):
                if attr == '_bot':
                    return super(BotWrapper, self).__setattr__(attr, value)
                else:
                    return setattr(self._bot, attr, value)

        return BotWrapper(self)

    @staticmethod
    def __write_details_to_disk(resp: LoginResponse) -> None:
        """Writes login details to disk so that we can restore our session later
        without logging in again and creating a new device ID.

        Arguments:
            resp {LoginResponse} -- the successful client login response.
        """
        with open('credentials.json', "w") as f:
            json.dump({
                "access_token": resp.access_token,
                "device_id": resp.device_id,
                "user_id": resp.user_id
            }, f)


async def run_client(client: Jenny) -> None:
    """A basic encrypted chat application using nio.
    """

    # This is our own custom login function that looks for a pre-existing config
    # file and, if it exists, logs in using those details. Otherwise it will log
    # in using a password.
    await client.login()

    # Here we create a coroutine that we can call in asyncio.gather later,
    # along with sync_forever and any other API-related coroutines you'd like
    # to do.
    async def after_first_sync():
        print("Awaiting sync")
        await client.synced.wait()
        # Trust people here
        for admin in config.admins:
            client.trust_devices(admin)

    for hook in client.startup_hooks:
        try:
            asyncio.create_task(hook['func'](client))
        except Exception as e:
            print(traceback.format_exc())
            tb = repr(e) + traceback.format_exc().splitlines()[-3]
            print("Error in {0} module: {1}".format(hook['module'], tb))

    after_first_sync_task = asyncio.create_task(after_first_sync())

    # We use full_state=True here to pull any room invites that occured or
    # messages sent in rooms _before_ this program connected to the
    # Matrix server
    sync_forever_task = asyncio.ensure_future(client.sync_forever(30000, full_state=True, set_presence="online"))

    await asyncio.gather(
        # The order here IS significant! You have to register the task to trust
        # devices FIRST since it awaits the first sync
        after_first_sync_task,
        sync_forever_task
    )


# Decorators and other shit
def message_hook(regex):
    def wrap(func):
        func._handler = 1  # 1: Stuff handler.
        func._regex = re.compile(regex)
        return func
    return wrap


def command_hook(commands, help=""):  # noqa
    if type(commands) == str:
        commands = [commands]

    def wrap(func: Coroutine[Jenny, MatrixRoom, HookMessage]):
        func._handler = 3  # 3: Command.
        func._commands = commands
        func._help = help
        return func
    return wrap


def startup_hook(dummy=None):
    def wrap(func):
        func._handler = 2  # 2: function called when bot connects.
        return func
    return wrap


async def main():
    cli_config = AsyncClientConfig(store_sync_tokens=True)
    client = Jenny(
        config.homeserver,
        config.username,
        store_path="matrix_store/",
        cli_config=cli_config,
    )

    try:
        await run_client(client)
    except (asyncio.CancelledError, KeyboardInterrupt):
        await client.close()

# Run the main coroutine, which instantiates our custom subclass, trusts all the
# devices, and syncs forever (or until your press Ctrl+C)

if __name__ == "__main__":
    try:
        asyncio.run(
            main()
        )
    except KeyboardInterrupt:
        pass