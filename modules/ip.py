# -*- coding: utf-8 -*-
from nio import MatrixRoom

from dors import command_hook, Jenny, HookMessage
import urllib.parse
import http.client
import urllib.request
import urllib.error
import json


@command_hook(['ip'], help="Locates a IP address.")
async def ipaddr(bot: Jenny, room: MatrixRoom, event: HookMessage):
    if not event.args:
        return await bot.reply("Usage: ip <ip address>")
    
    text = urllib.parse.quote(event.args[0])
    conn = http.client.HTTPConnection("ip-api.com")
    conn.request("GET", "/json/{0}?fields=65535".format(text))
    res = conn.getresponse().read().decode('utf-8')
    data = json.loads(res)
    if data['status'] == "success":
        resp = "IP \2{0}\2  ".format(data['query'])
        if data['reverse'] != "":
            resp += "- {0}  ".format(data['reverse'])
        if data['country'] != "":
            resp += "\2Country\2: {0}, ".format(data['country'])
        if data['region'] != "":
            resp += "\2Region\2: {0}, ".format(data['region'])
        if data['city'] != "":
            resp += "\2City\2: {0}, ".format(data['city'])
        if data['isp'] != "":
            resp += "\2ISP\2: {0}, ".format(data['isp'])
        if data['org'] != "":
            resp += "\2Organization\2: {0}, ".format(data['org'])
        if data['as'] != "":
            resp += "\2ASN\2: {0}, ".format(data['as'])
        if data['timezone'] != "":
            resp += "\2Timezone\2: {0}, ".format(data['timezone'])
        await bot.say(resp[0:len(resp)-2])
    else:
        await bot.say("\00304Error\003: Couldn't process that IP")

