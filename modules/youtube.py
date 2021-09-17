from nio import MatrixRoom

from dors import command_hook, Jenny, HookMessage
import re
import requests
import config
from datetime import timedelta
import urllib.parse

yt_id_re = r'(?:youtube(?:-nocookie)?\.com/(?:[^/]+/.+/|(?:v|e(?:mbed)?)/|.*[?&]v=)|youtu\.be/)([^\"&?/ ]{11})'
YT_ID_REGEX = re.compile(yt_id_re)


def youtube_duration_to_time(duration):
    match = re.match(r'PT(\d+H)?(\d+M)?(\d+S)?', duration).groups()
    delta = timedelta(hours=int(match[0][:-1]) if match[0] else 0,
                      minutes=int(match[1][:-1]) if match[1] else 0,
                      seconds=int(match[2][:-1]) if match[2] else 0)
    if delta.total_seconds() > 0:
        return str(delta)
    else:
        return "LIVE"


@command_hook(['youtube', 'yt'], help="Fetches youtube video")
async def youtube(bot: Jenny, room: MatrixRoom, event: HookMessage):
    if len(event.args) == 0:
        return await bot.say("Usage: .yt <some text>")
    if " ".join(event.args) == "FIRDAY":
        return await bot.say("[\002Youtube Search\002] Rebecca Black - Friday | https://youtu.be/kfVsfOSbJY0")
    query = urllib.parse.quote_plus(" ".join(event.args))
    url = "https://www.googleapis.com/youtube/v3/search?part=snippet&maxResults=1&safeSearch=moderate" \
          f"&key={config.google_apikey}&q={query}"
    res = requests.get(url)
    if res.status_code == requests.codes.ok:
        res = res.json()
        if len(res['items']) > 0:
            try:
                title = res['items'][0]['snippet']['title']
                video_id = res['items'][0]['id']['videoId']
                return await bot.say('[\002Youtube Search\002] {0} | https://youtu.be/{1}'.format(title, video_id))
            except:
                pass
        return await bot.say('No results found')
