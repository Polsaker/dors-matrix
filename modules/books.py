from dors import commandHook
import requests
import urllib.parse
import re
import config
import pycountry


@commandHook(['book'])
def book(bot, ev):
    if len(ev.args) > 0:
        stext = " ".join(ev.args)
    else:
        bot.say('Usage: .book <query>  -- Queries Google books')
    
    foo = re.search("( |^)lang:(.+)( |$)", stext)
    lang = "en"
    if foo:
        stext = stext.replace(foo.group(0), "")
        lang = foo.group(2)
    stext = urllib.parse.quote_plus(stext)
    
    if re.search("isbn", stext):
        stext = stext.replace("-", "")
    
    search = requests.get("https://www.googleapis.com/books/v1/volumes?q={0}&langRestrict={2}&country=US&key={1}&maxResults=3".format(stext, config.google_apikey, lang)).json()
    if search['totalItems'] == 0:
        cli.msg(event.target, "Couldn't find any matching book")
        return

    for b in search['items']:
        resp = "\002{0}\002, ".format(b['volumeInfo']['title'])
        try:
            resp += "Author(s): \002{0}\002. ".format(", ".join(b['volumeInfo']['authors']))
        except:
            pass
        try:
            resp += "Published: \002{0}\002. ".format(b['volumeInfo']['publishedDate'])
        except:
            pass
        try:
            resp += "\002{0}\002 pages. ".format(b['volumeInfo']['pageCount'])
        except:
            pass
        
        try:
            idi = pycountry.languages.lookup(b['volumeInfo']['language']).name
            resp += "Language: \002{0}\002. ".format(idi)
        except:
            pass
            
        for l in b['volumeInfo'].get('industryIdentifiers', []):
            if l['type'] == "ISBN_13":
                resp += "ISBN-13: \002{0}\002. ".format(l['identifier'])
            elif l['type'] == "ISBN_10":
                resp += "ISBN-10: \002{0}\002. ".format(l['identifier'])
        resp += "\00311http://books.google.com/books?id={0}\003".format(b['id'])
        
        bot.say(resp)
