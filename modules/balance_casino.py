import asyncio
import copy
import hashlib
import hmac
import random
import secrets
import time
from typing import Optional

from nio import MatrixRoom, RoomSendResponse, UnknownEvent

from dors import command_hook, HookMessage, Jenny, startup_hook
from modules import balance

open_games = {}
g_bot: Optional[Jenny] = None


@startup_hook()
async def expire_games(bot: Jenny):
    global g_bot
    g_bot = bot
    bot.add_event_callback(on_unknown, UnknownEvent)  # noqa
    while True:
        await asyncio.sleep(1)
        for user, data in copy.copy(open_games).items():
            if (time.time() - data['time']) > 60 * 2.5:
                tag = await bot.source_tag(user)
                await bot.message(data['room'], f"Cancelling {tag}'s game for \002{open_games[user]['amount']}\002 "
                                                f"DOGE.", p_html=True)
                del open_games[user]
                await bot.room_redact(data['room'], data['react_evid'])


async def on_unknown(room: MatrixRoom, event: UnknownEvent):
    # Catch the m.reaction events
    if event.sender == g_bot.user_id:
        return
    if event.type != "m.reaction":
        return
    reacted_to = event.source['content']['m.relates_to']['event_id']
    reaction_cont = event.source['content']['m.relates_to']['key']

    evid_to_game = {x['accept_evid']: y for y, x in open_games.items()}
    if evid_to_game.get(reacted_to) and reaction_cont == "✅":
        player_one = evid_to_game[reacted_to]
        game = open_games[player_one]
        amount = game['amount']
        # Accepted! Remove reactions and do a countdown.
        await g_bot.room_redact(room.room_id, event.event_id)

        # if event.sender == player_one:
        #     return

        if await balance.get_balance(event.sender) < amount:
            return
        del open_games[player_one]
        randomclass: ProvablyFair = game['rand']
        randomclass.client_seed = hashlib.sha256(f"{game['1h_seed']}{event.sender}".encode()).hexdigest()

        tagone = await g_bot.source_tag(player_one)
        tagtwo = await g_bot.source_tag(event.sender)

        # Edit the message. This is a bit cumbersome :/
        await g_bot.room_send(room.room_id, 'm.room.message', {
            "body": f"Playing against {event.sender}\nClient seed: `{randomclass.client_seed}`",
            "format": "org.matrix.custom.html",
            "formatted_body": "Playing against {tagtwo}",
            "m.new_content": {
                "body": f"{player_one} bet <b>{amount}</b> DOGE in a coinflip game. Playing against {event.sender}\n\n"
                        f"Game hash: `{randomclass.server_seed_hash}`\nClient seed: `{randomclass.client_seed}`",
                "format": "org.matrix.custom.html",
                "formatted_body": f"{tagone} bet <b>{amount}</b> DOGE in a coinflip game. Playing against {tagtwo}"
                                  f"<br/><br/>Game hash: <code>{randomclass.server_seed_hash}</code><br/>"
                                  f"Client seed: <code>{randomclass.client_seed}</code>",
                "msgtype": "m.notice"
            },
            "m.relates_to": {
                "event_id": reacted_to,
                "rel_type": "m.replace"
            },
            "msgtype": "m.notice"
        })

        await g_bot.room_redact(room.room_id, game['react_evid'])
        # Remove the balances from players
        await balance.bulk_take([player_one, event.sender], amount)

        # Reaction countdown. This could be simplified into a for loop
        dat: RoomSendResponse = await g_bot.message(room.room_id, "I flip a coin and...")

        await g_bot.room_send(room.room_id, "m.reaction", {
            "m.relates_to": {
                "rel_type": "m.annotation",
                "event_id": dat.event_id,
                "key": f"\U0001FA99"
            }
        })

        # Suspense loop
        for i in range(5, 0, -1):
            p_react = await g_bot.room_send(room.room_id, "m.reaction", {
                "m.relates_to": {
                    "rel_type": "m.annotation",
                    "event_id": dat.event_id,
                    "key": f"{i}\U0000FE0F\U000020E3"
                }
            })
            await asyncio.sleep(1)
            await g_bot.room_redact(room.room_id, p_react.event_id)

        flip = randomclass.choice([event.sender, player_one])
        server_seed = randomclass.invalidate()
        tag = await g_bot.source_tag(flip)
        await g_bot.room_send(room.room_id, 'm.room.message', {
            "body": f"The winner is {flip}! You won \002{amount * 2}\002 DOGE.\n\nGame seed: {server_seed}",  # noqa
            "format": "org.matrix.custom.html",
            "formatted_body": f"The winner is {tag}! You won <b>{amount * 2}</b> DOGE.<br/><br/>"
                              f"Game seed: <code>{server_seed}</code>",
            "m.new_content": {
                "body": f"I flip a coin and...\n\nthe winner is {flip}! You won {amount * 2} DOGE.\n\n"
                        f"Game seed: {server_seed}",
                "format": "org.matrix.custom.html",
                "formatted_body": f"I flip a coin and...<br/><br/>the winner is {tag}! You won <b>{amount * 2}</b> "
                              f"DOGE.<br/>Game seed: <code>{server_seed}</code>",
                "msgtype": "m.notice"
            },
            "m.relates_to": {
                "event_id": dat.event_id,
                "rel_type": "m.replace"
            },
            "msgtype": "m.notice"
        })
        await balance.give(flip, amount * 2)


@command_hook(['coinflip2', 'flip'])
async def coinflip(bot: Jenny, room: MatrixRoom, event: HookMessage):
    global open_games
    if len(event.args) < 1:
        return await bot.say("Usage: .coinflip <amount>")

    try:
        amount = float(event.args[0])
    except ValueError:
        return await bot.reply("Invalid amount.")
    if amount < 1:
        return await bot.reply("Minimum amount is 1.")

    if event.sender in open_games:
        await bot.say(f"Cancelling previous open game for \002{open_games[event.sender]['amount']}\002 DOGE.")

    amount = round(amount, 2)

    if await balance.get_balance(event.sender) < amount:
        return await bot.reply("Not enough balance!")

    randinst = ProvablyFair()

    open_games[event.sender] = {
        "amount": amount,
        "room": room.room_id,
        "time": time.time(),
        "rand": randinst,
        "1h_seed": event.args[1:] if len(event.args) > 1 else event.sender
    }

    tag = await bot.source_tag(event.sender)
    msgdata = await bot.message(room.room_id, f"{tag} bet \002{amount}\002 DOGE in a coinflip game. To accept, "
                                              "click on the reaction<br/><br/>"
                                              f"Game hash: <code>{randinst.server_seed_hash}</code>", p_html=True)
    p_react = await bot.room_send(room.room_id, "m.reaction", {
        "m.relates_to": {
            "rel_type": "m.annotation",
            "event_id": msgdata.event_id,
            "key": "✅"
        }
    })

    open_games[event.sender]['accept_evid'] = msgdata.event_id
    open_games[event.sender]['react_evid'] = p_react.event_id


class ProvablyFair(random.Random):
    """An object that represents a provably fair algorithm"""

    def __init__(self, client_seed: str = None, *, server_seed: str = None):
        self.valid = True
        self.nonce = -1
        self.client_seed = client_seed if client_seed else secrets.token_hex(10)
        if not server_seed:
            data = self.generate_server_seed()
        else:
            data = self._hash_server_seed(server_seed)
        self._server_seed, self.server_seed_hash = data
        self.last_rolled_data = None

    @classmethod
    def verify_roll(cls, server_seed, server_seed_hash, client_seed, nonce, roll):
        """Verifies that a roll passed successfully
        Returns True if all was well, otherwise raising AssertionError"""

        instance = cls(client_seed, server_seed=server_seed)
        instance_roll = instance.random(nonce=nonce)
        instance_data = instance.last_rolled_data
        assert instance._server_seed == server_seed
        assert instance.server_seed_hash == server_seed_hash
        assert instance_data['nonce'] == nonce
        assert instance_data['roll'] == roll
        return True

    @staticmethod
    def generate_server_seed():
        """Generates a new server seed to use for future rolls"""

        server_seed = secrets.token_hex(20)
        server_seed_hash_object = hashlib.sha256(server_seed.encode())
        server_seed_hash = server_seed_hash_object.hexdigest()
        return server_seed, server_seed_hash

    @staticmethod
    def _hash_server_seed(server_seed):
        """Hashes and stores a given server seed"""

        server_seed_hash_object = hashlib.sha256(server_seed.encode())
        server_seed_hash = server_seed_hash_object.hexdigest()
        return server_seed, server_seed_hash

    def invalidate(self):
        """Marks this instance as invalid and returns the server seed to you"""

        self.valid = False
        return self._server_seed

    def random(self, *, nonce=None):
        """Generates a provably random number given a client seed and a
        pre-generated server seed hash"""

        # Make sure it's still valid
        if not self.valid:
            raise Exception('This server seed is no longer valid.')

        # Get a nonce to use
        if nonce:
            self.nonce = nonce
        else:
            self.nonce += 1

        # HMAC it up
        msg_str = '{}-{}'.format(self.client_seed, self.nonce)
        key = self._server_seed.encode()
        msg = msg_str.encode()
        dig = hmac.new(key, msg=msg, digestmod=hashlib.sha512)

        # Get the number
        full_number = dig.hexdigest()
        counter = 0
        while True:
            number_str = full_number[counter:counter+5]
            number = int(number_str, 16)
            if number > 999_999:
                counter += 5
            else:
                break

        # Return results
        roll = (number % (10**4)) / 100
        self.last_rolled_data = {
            'roll': roll,
            'nonce': self.nonce,
            'server_seed_hash': self.server_seed_hash,
            'client_seed': self.client_seed
        }
        return roll / 100

    def seed(self, *args, **kwds):
        """Stub method. Not used for provably fair systems, since the seed is passed on initialization"""

        return None

    def getstate(self):
        return self.nonce, self.client_seed, self._server_seed

    def setstate(self, state):
        self.nonce, self.client_seed, self._server_seed = state

    def _randbelow(self, n):
        return int(self.random() * n)
