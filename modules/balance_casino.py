import asyncio
import copy
import random
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

        if event.sender == player_one:
            return

        if await balance.get_balance(event.sender) < amount:
            return
        del open_games[player_one]

        tagone = await g_bot.source_tag(player_one)
        tagtwo = await g_bot.source_tag(event.sender)

        # Edit the message. This is a bit cumbersome :/
        await g_bot.room_send(room.room_id, 'm.room.message', {
            "body": f"Playing against {event.sender}",
            "format": "org.matrix.custom.html",
            "formatted_body": "Playing against {tagtwo}",
            "m.new_content": {
                "body": f"{player_one} bet <b>{amount}</b> DOGE in a coinflip game. Playing against {event.sender}",
                "format": "org.matrix.custom.html",
                "formatted_body": f"{tagone} bet <b>{amount}</b> DOGE in a coinflip game. Playing against {tagtwo}",
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

        flip = random.choice([event.sender, player_one])
        tag = await g_bot.source_tag(flip)
        await g_bot.room_send(room.room_id, 'm.room.message', {
            "body": f"The winner is {flip}! You won \002{amount * 2}\002 DOGE.",
            "format": "org.matrix.custom.html",
            "formatted_body": f"The winner is {tag}! You won <b>{amount * 2}</b> DOGE.",
            "m.new_content": {
                "body": f"I flip a coin and...\n\nthe winner is {flip}! You won {amount * 2} DOGE.",
                "format": "org.matrix.custom.html",
                "formatted_body": f"I flip a coin and...<br/><br/>the winner is {tag}! You won <b>{amount * 2}</b> DOGE.",
                "msgtype": "m.notice"
            },
            "m.relates_to": {
                "event_id": dat.event_id,
                "rel_type": "m.replace"
            },
            "msgtype": "m.notice"
        })
        await balance.give(flip, amount * 2)


@command_hook(['coinflip', 'flip'])
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

    open_games[event.sender] = {
        "amount": amount,
        "room": room.room_id,
        "time": time.time()
    }

    tag = await bot.source_tag(event.sender)
    msgdata = await bot.message(room.room_id, f"{tag} bet \002{amount}\002 DOGE in a coinflip game. To accept, "
                                              f"click on the reaction", p_html=True)
    p_react = await bot.room_send(room.room_id, "m.reaction", {
        "m.relates_to": {
            "rel_type": "m.annotation",
            "event_id": msgdata.event_id,
            "key": "✅"
        }
    })

    open_games[event.sender]['accept_evid'] = msgdata.event_id
    open_games[event.sender]['react_evid'] = p_react.event_id
