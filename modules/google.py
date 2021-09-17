from nio import MatrixRoom

from dors import command_hook, Jenny, HookMessage
import requests
import urllib.parse
import config
import html


@command_hook(['google', 'g'])
async def google(bot: Jenny, room: MatrixRoom, event: HookMessage):
    if len(event.args) > 0:
        stext = urllib.parse.quote_plus(" ".join(event.args))
    else:
        await bot.say("Usage: .google <search text> -- performs a search in Google")
        return 0
    search = requests.get(f"https://www.googleapis.com/customsearch/v1?num=3&key={config.google_apikey}"
                          f"&cx=001206920739550302428:fozo2qblwzc&q={stext}&alt=json").json()
    
    search_cli = html.escape(" ".join(event.args))
    resp = f"Google results for \"\2{search_cli}\2\": <ul>"

    for search_item in search['items'][0:3]:
        search_link = search_item['link']
        search_title = search_item['title']
        resp += f"<li>\2{search_title}\2 {search_link}</li>"

    resp += "</ul>"
    await bot.message(room.room_id, resp, p_html=True)
