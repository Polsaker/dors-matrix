import asyncio
import copy
import hashlib
import time
from collections import defaultdict

from nio import MatrixRoom

from dors import command_hook, HookMessage, Jenny, startup_hook
from modules import balance
from modules.balance_casino import ProvablyFair

game_players = defaultdict(lambda: defaultdict(int))
game_start_at = {}
game_randomizers = {}
game_started = {}
game_cap = {}


async def start_game(bot: Jenny, room_id):
    game_started[room_id] = True
    players = game_players[room_id]
    players = dict(sorted(players.items()))  # sort by username alphabetically

    randomizer: ProvablyFair = game_randomizers[room_id]
    client_seed_s = "".join([x for x in players.keys()])
    client_seed_s = hashlib.sha256(client_seed_s.encode()).hexdigest()
    randomizer.client_seed = client_seed_s

    total = sum([x for x in players.values()])
    commission = int(round(total * 0.02, 0))
    await balance.give(bot.user_id, commission)
    total -= commission

    stakes = ", ".join([f"{await bot.source_tag(x)} (\002{y}\002 DOGE)" for x, y in players.items()])

    # calculate the winning chances for every player....
    full_c = 1000
    last_c = 0
    winning_ranges = {}  # player -> (start, end)

    actual_total = total + commission

    for player, amount in players.items():
        a_chances = int(round((amount / actual_total) * full_c, 0))
        winning_ranges[player] = (last_c, last_c + a_chances)
        last_c += a_chances

    print(winning_ranges)
    dat = await bot.message(
        room_id,
        f"Starting the Jackpot game. Total pot: \002{total}\002 DOGE<br/>Stakes: {stakes}<br/><br/>"
        f"Client seed: <code>{client_seed_s}</code>",
        p_html=True
    )

    await bot.room_send(room_id, "m.reaction", {
        "m.relates_to": {
            "rel_type": "m.annotation",
            "event_id": dat.event_id,
            "key": f"\U0001F3B2"
        }
    })

    # Suspense loop
    for i in range(9, 0, -1):
        p_react = await bot.room_send(room_id, "m.reaction", {
            "m.relates_to": {
                "rel_type": "m.annotation",
                "event_id": dat.event_id,
                "key": f"{i}\U0000FE0F\U000020E3"
            }
        })
        await asyncio.sleep(1)
        await bot.room_redact(room_id, p_react.event_id)

    result = randomizer.random() * 1000
    winner = None
    # Find who won
    for player, ranges in winning_ranges.items():
        if ranges[0] <= result < ranges[1]:
            winner = player
            break

    if not winner:
        winner = bot.user_id

    gameseed = randomizer.invalidate()

    winner_tag = await bot.source_tag(winner)
    await bot.message(
        room_id,
        f"Aaaand, the winner is.... \002{winner_tag}\002! You get the \002{total}\002 DOGE!<br/>"
        f"Game seed: <code>{gameseed}</code>", p_html=True
    )

    await balance.give(winner, total)


@startup_hook()
async def expire_games(bot: Jenny):
    while True:
        await asyncio.sleep(1)
        for channel, timestart in copy.copy(game_start_at).items():
            ctime = int(time.time())
            if ctime > timestart:
                if len(game_players[channel]) == 1:
                    for user, amt in game_players[channel].items():
                        await balance.give(user, amt)

                    del game_players[channel]
                    del game_start_at[channel]
                    await bot.message(channel, "Jackpot game cancelled - expired.")
                    continue
                await start_game(bot, channel)
                del game_players[channel]
                del game_start_at[channel]
                del game_started[channel]
                del game_cap[channel]
            elif ctime == (timestart - 30):
                await bot.message(channel, "Jackpot game will begin in <b>30 seconds</b>", p_html=True)
            elif ctime == (timestart - 5):
                await bot.message(channel, "Jackpot game will begin in <b>5 seconds</b>", p_html=True)


@command_hook('jackpot')
async def jackpot(bot: Jenny, room: MatrixRoom, event: HookMessage):
    if not event.args:
        return await bot.say("Usage: .jackpot <amount> - Join a game of Jackpot.")

    time_to_start = 60
    try:
        amount_f = float(event.args[0])
        amount = int(event.args[0])
    except ValueError:
        return await bot.reply("Invalid amount")

    if amount < 1:
        return await bot.reply("The minimum bet is 1 DOGE.")

    if amount != amount_f:
        return await bot.reply("Invalid amount - Must be a whole number")

    if game_started.get(room.room_id):
        return await bot.reply("Game currently in progress - Please wait!")

    if await balance.get_balance(event.sender) < amount:
        return await bot.reply("Not enough balance!")

    # Anti-sniping
    if game_start_at.get(room.room_id) and len(game_players[room.room_id]) > 1:
        time_left = game_start_at[room.room_id] - int(time.time())
        if time_left <= 5:
            return

    tag = await bot.source_tag(event.sender)
    prv_len = len(game_players[room.room_id])

    temp_amt = game_players[room.room_id][event.sender] + amount
    if game_cap.get(room.room_id) and temp_amt > game_cap[room.room_id]:
        return await bot.reply(f"Max bet is \002{game_cap[room.room_id]}\002 DOGE")

    game_players[room.room_id][event.sender] += amount
    total_amt = game_players[room.room_id][event.sender]

    if len(game_players[room.room_id]) == 1:
        game_randomizers[room.room_id] = ProvablyFair()
        await bot.message(room.room_id, f"{tag} bet \002{total_amt}\002 DOGE and started a game of Jackpot. "
                                        f"To join use .jackpot [amount] (Max bet: <b>{amount * 2}</b> DOGE)<br/>"
                                        f"Game Hash: <code>{game_randomizers[room.room_id].server_seed_hash}</code>",
                          p_html=True)
        game_start_at[room.room_id] = int(time.time() + 60)
        game_cap[room.room_id] = amount * 2
    else:
        await bot.message(room.room_id, f"{tag} bet \002{total_amt}\002 DOGE and joined the Jackpot game. "
                                        f"To join use .jackpot <amount>",
                          p_html=True)

    await balance.take(event.sender, amount)

    if len(game_players[room.room_id]) == 2 and prv_len != 2:
        await bot.say(f"The Jackpot game will begin in \002{time_to_start} seconds\002.")
        game_start_at[room.room_id] = int(time.time() + time_to_start)
