# -*- coding: utf-8 -*-
from dors import commandHook
import urllib.parse
import http.client
import urllib.request
import urllib.error
import json

@commandHook(['ip'], help="Locates a IP address.")
def ipaddr(irc, ev):
    if not ev.args:
        return irc.reply("Usage: ip <ip address>")
    
    text = urllib.parse.quote(ev.args[0])
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
        irc.say(resp[0:len(resp)-2])
    else:
        irc.say("\00304Error\003: Couldn't process that IP")

