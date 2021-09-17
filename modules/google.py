from dors import command_hook
import requests
import urllib.parse
import re
import config
import pycountry
import html


@command_hook(['google', 'g'])
def google(cli, event):
    if len(event.args) > 0:
        stext = urllib.parse.quote_plus(" ".join(event.args))
    else:
        cli.msg("Usage: .google <search text> -- performs a search in Google")
        return 0
    search = requests.get("https://www.googleapis.com/customsearch/v1?"
     "num=3&key={0}&cx=001206920739550302428:fozo2qblwzc&q={1}&alt=json".format(config.google_apikey, stext)).json()
    
    search_cli = html.escape(" ".join(event.args))
    resp = "Google results for " + \
    " \"\2{0}\2\": <ul>".format(search_cli) \
    + "<li>\2%s\2 %s</li>" % (search['items'][0]['title'],
    search['items'][0]['link'])
    try:
        resp += "<li>\2{0}\2 {1}</li>".format(
                search['items'][1]['title'], search['items'][1]['link'])
        resp += "<li>\2{0}\2 {1}</li>".format(
                search['items'][2]['title'], search['items'][2]['link'])
    except:
        pass
    resp += "</ul>"
    cli.message(event.target, resp, p_html=True)
