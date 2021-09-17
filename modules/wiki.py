from dors import command_hook
import requests
import re


@command_hook(['wiki'])
def wikipedia(irc, ev):
    term = '+'.join(str(x) for x in ev.args)
    resp = requests.get("https://en.wikipedia.org/w/api.php?action=query&prop=extracts&exintro=&titles=" + term + "&format=json&exsentences=3&redirects").json()
    tmp = str(resp['query']['pages'])
    pageid = tmp.split(':', 1)[0]
    pageid = re.findall(r'\d+', pageid)[0]
    message = resp['query']['pages'][pageid]['extract'].strip()
    link = '_'.join(str(x) for x in ev.args)
    flink =  'https://en.wikipedia.org/wiki/' + link

    irc.message(ev.replyto, message + '\n' + flink, p_html=True)


@command_hook(['wikisearch'])
def wikipediasearch(irc, ev):
    term = '+'.join(str(x) for x in ev.args)
    resp = requests.get("https://en.wikipedia.org/w/api.php?action=query&list=search&srsearch=" + term + "&utf8=&format=json").json()
    message = ''
    for entry in resp['query']['search'][0:5]:
        link = re.sub(' ', '_', entry['title'])
        message += 'https://en.wikipedia.org/wiki/' + link + ' | '
    irc.message(ev.replyto, ev.source + ": " + message[0:-3])
