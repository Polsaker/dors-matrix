from dors import commandHook
import re
import requests

# Ported from jenni

exp = re.compile(r'<div class="dropshadow1">\n<p>(.*?)</p>\n</div>')

@commandHook(['pun', 'badpun'], help="Gives a bad pun.")
def puns(irc, event):
    url = 'http://www.punoftheday.com/cgi-bin/randompun.pl'
    page = requests.get(url).content.decode()

    result = exp.search(page)
    if result:
        pun = result.groups()[0]
        return irc.say(pun)
    else:
        return irc.say("I'm afraid I'm not feeling punny today!")
