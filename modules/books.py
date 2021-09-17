from nio import MatrixRoom

from dors import command_hook, Jenny, HookMessage
import requests
import urllib.parse
import re
import config
import pycountry


@command_hook(['book'])
async def book(bot: Jenny, room: MatrixRoom, event: HookMessage):
    if len(event.args) > 0:
        stext = " ".join(event.args)
    else:
        return await bot.say('Usage: .book <query>  -- Queries Google books')
    
    foo = re.search("( |^)lang:(.+)( |$)", stext)
    lang = "en"
    if foo:
        stext = stext.replace(foo.group(0), "")
        lang = foo.group(2)
    stext = urllib.parse.quote_plus(stext)
    
    if re.search("isbn", stext):
        stext = stext.replace("-", "")

    # TODO: ASYNC REQUESTS
    search = requests.get(f"https://www.googleapis.com/books/v1/volumes?q={stext}&langRestrict={lang}&country=US"
                          f"&key={config.google_apikey}&maxResults=3").json()
    if search['totalItems'] == 0:
        await bot.say("Couldn't find any matching book")
        return

    for b in search['items']:
        resp = "\002{0}\002, ".format(b['volumeInfo']['title'])
        try:
            resp += "Author(s): \002{0}\002. ".format(", ".join(b['volumeInfo']['authors']))
        except KeyError:
            pass
        try:
            resp += "Published: \002{0}\002. ".format(b['volumeInfo']['publishedDate'])
        except KeyError:
            pass
        try:
            resp += "\002{0}\002 pages. ".format(b['volumeInfo']['pageCount'])
        except KeyError:
            pass
        
        try:
            idi = pycountry.languages.lookup(b['volumeInfo']['language']).name
            resp += "Language: \002{0}\002. ".format(idi)
        except KeyError:
            pass
            
        for l in b['volumeInfo'].get('industryIdentifiers', []):
            if l['type'] == "ISBN_13":
                resp += "ISBN-13: \002{0}\002. ".format(l['identifier'])
            elif l['type'] == "ISBN_10":
                resp += "ISBN-10: \002{0}\002. ".format(l['identifier'])
        resp += "\00311https://books.google.com/books?id={0}\003".format(b['id'])
        
        await bot.say(resp)
