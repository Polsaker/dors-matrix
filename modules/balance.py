import re
from typing import List

import requests
from nio import MatrixRoom
import aiosqlite

from dors import command_hook, HookMessage, Jenny, startup_hook


@startup_hook()
async def __setup_db(bot: Jenny):
    async with aiosqlite.connect("./balance.db") as db:
        await db.execute("CREATE TABLE IF NOT EXISTS balance (id INTEGER PRIMARY KEY AUTOINCREMENT, "
                         "username VARCHAR(255), balance REAL)")
        await db.commit()


# Utility functions for external use
async def transfer(user_from: str, user_to: str, amount: float) -> bool:
    """ Transfers currency from one user to the other. Returns False if user_from does not have enough balance """
    amount = round(amount, 8)

    async with aiosqlite.connect("./balance.db") as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM balance WHERE username = ?", [user_from]) as cursor:
            row = await cursor.fetchone()
            if not row or row['balance'] < amount:
                return False

        await _create_if_not_exists(db, user_to)

        # Do the transfer
        await db.execute("UPDATE balance SET balance = balance - ? WHERE username = ?", [amount, user_from])
        await db.execute("UPDATE balance SET balance = balance + ? WHERE username = ?", [amount, user_to])
        await db.commit()
    return True


async def get_balance(user: str) -> float:
    """ Returns the balance for a user. """
    async with aiosqlite.connect("./balance.db") as db:
        db.row_factory = aiosqlite.Row
        await _create_if_not_exists(db, user)
        async with db.execute("SELECT * FROM balance WHERE username = ?", [user]) as cursor:
            row = await cursor.fetchone()
            return round(row['balance'], 8)


async def give(user: str, amount: float):
    """ Give money to a user. """
    return await bulk_give([user], amount)


async def take(user: str, amount: float):
    """ Give take money from a user. """
    return await bulk_take([user], amount)


async def bulk_take(user_list: List[str], amount: float):
    amount = round(amount, 8)
    if amount < 0:
        raise RuntimeError("Negative values are not allowed.")

    async with aiosqlite.connect("./balance.db") as db:
        db.row_factory = aiosqlite.Row
        for user in user_list:
            await _create_if_not_exists(db, user)
            # Do the transfer
            await db.execute("UPDATE balance SET balance = balance - ? WHERE username = ?", [amount, user])
        await db.commit()
    return True


async def bulk_give(user_list: List[str], amount: float):
    amount = round(amount, 8)
    if amount < 0:
        raise RuntimeError("Negative values are not allowed.")

    async with aiosqlite.connect("./balance.db") as db:
        db.row_factory = aiosqlite.Row
        for user in user_list:
            await _create_if_not_exists(db, user)
            # Do the transfer
            await db.execute("UPDATE balance SET balance = balance + ? WHERE username = ?", [amount, user])
        await db.commit()
    return True


# Internal helpers
async def _create_if_not_exists(db, user: str):
    async with db.execute("SELECT * FROM balance WHERE username = ?", [user]) as cursor:
        row = await cursor.fetchone()
        if not row:
            await db.execute("INSERT INTO balance (username, balance) VALUES (?, 0)", [user])
            await db.commit()


# Standard commands
@command_hook(['balance', 'bal', 'b'])
async def __cmd_balance(bot: Jenny, room: MatrixRoom, event: HookMessage):
    currency = 'USD'
    if event.args:
        currency = event.args[0].upper()

    ubalance = await get_balance(event.sender)
    info = requests.get(f"https://min-api.cryptocompare.com/data/price?fsym=DOGE&tsyms={currency}").json()
    extra = ''
    if 'Error' not in str(info):
        extra = f" (\002{round(float(info[currency]) * ubalance, 8)}\002 {currency})"

    await bot.reply(f"Your balance: \002{round(ubalance, 8)}\002 DOGE{extra}.")


@command_hook(['tip'])
async def __cmd_tip(bot: Jenny, room: MatrixRoom, event: HookMessage):
    if not event.args:
        return await bot.say("Usage: .tip <amount> <user>")

    try:
        amount = float(event.args[0])
        user = " ".join(event.args[1:])
    except ValueError:
        # Maybe the first arg is the nick?
        try:
            amount = float(event.args[-1])
            user = " ".join(event.args[0:-1])
        except ValueError:
            return await bot.reply("Invalid amount.")

    if amount <= 0:
        return await bot.reply("Invalid amount.")

    if amount < 0.01:
        return await bot.reply("Minimum tip is 0.01")

    # Find the user...
    # TODO: Make this a helper function? Will be used everywhere..
    if user.startswith("@"):
        if user not in room.users:
            return await bot.say(f"'{user}' is not in the room")
        real_user = user
    else:
        potential_users = room.user_name_clashes(user)

        if len(potential_users) > 1:
            # We will have to dissect the html thingy
            poke_re = re.compile(r"\.tip .+? <a href=\"https://matrix.to/#/(.+)\">.|")
            if match := poke_re.match(event.formatted_body):
                real_user = match.group(1)
            else:
                await bot.say(f"There is more than one {user}?!!")
                return
        else:
            if not potential_users:
                return await bot.say(f"I couldn't find any {user} here...")
            real_user = potential_users[0]

    if real_user == event.sender:
        return await bot.say("No tipping yourself.")

    if await get_balance(event.sender) < amount:
        return await bot.reply("Not enough balance!")

    await transfer(event.sender, real_user, amount)

    tag = await bot.source_tag(real_user)
    await bot.message(room.room_id, f"Sent {amount} DOGE to {tag}.", p_html=True)


@command_hook(['baltop'])
async def __cmd_baltop(bot: Jenny, room: MatrixRoom, event: HookMessage):
    resp = ""
    async with aiosqlite.connect("./balance.db") as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT SUM(balance) AS `total` FROM balance") as cursor:
            row = await cursor.fetchone()
            resp += f"Total balance: \002{round(row['total'], 8)}\002 DOGE.\n\nTop 11 balances:<ol>"
        async with db.execute("SELECT * FROM balance ORDER BY balance DESC") as cursor:
            rows = await cursor.fetchall()
            amt = 0
            for row in rows:
                if row['username'] not in room.users:
                    continue
                if amt > 10:
                    break
                amt += 1
                tag = await bot.source_tag(row['username'])
                resp += f"<li>{tag}: \002{round(row['balance'], 8)}\002 DOGE</li>"
        resp += "</ol>"

    await bot.message(room.room_id, resp, p_html=True)
