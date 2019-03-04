from dors import commandHook
import requests
import re


@commandHook(['wiki'])
def wikipedia(irc, ev):
    term = '+'.join(str(x) for x in ev.args)
    resp = requests.get("https://en.wikipedia.org/w/api.php?action=query&prop=extracts&exintro=&titles=" + term + "&format=json&exsentences=3").json()
    tmp = str(resp['query']['pages'])
    pageid = tmp.split(':', 1)[0]
    pageid = re.findall(r'\d+', pageid)[0]
    message = resp['query']['pages'][pageid]['extract']
    message = re.sub('<[^<]+?>', '', message) # dirty strip html tags
    if len(message) > 400:
        message = message[:400] + "…"
    link = '_'.join(str(x) for x in ev.args)
    flink =  'https://en.wikipedia.org/wiki/' + link
    if float(len(message) + len(flink)) < 400:
        message += ' | ' + flink
    else:
        message += ' \n' + flink
    irc.message(ev.replyto, ev.source + ": " + message)


@commandHook(['wikisearch'])
def wikipediasearch(irc, ev):
    term = '+'.join(str(x) for x in ev.args)
    resp = requests.get("https://en.wikipedia.org/w/api.php?action=query&list=search&srsearch=" + term + "&utf8=&format=json").json()
    message = ''
    for entry in resp['query']['search'][0:5]:
        link = re.sub(' ', '_', entry['title'])
        message += 'https://en.wikipedia.org/wiki/' + link + ' | '
    irc.message(ev.replyto, ev.source + ": " + message[0:-3])
