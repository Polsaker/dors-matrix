from dors import commandHook
import re
import requests
import config
from datetime import timedelta
import urllib.parse

YT_ID_REGEX = re.compile('(?:youtube(?:-nocookie)?\.com/(?:[^/]+/.+/|(?:v|e(?:mbed)?)/|.*[?&]v=)|youtu\.be/)([^\"&?/ ]{11})')

def youtube_duration_to_time(duration):
    match = re.match('PT(\d+H)?(\d+M)?(\d+S)?', duration).groups()
    delta = timedelta(hours=int(match[0][:-1]) if match[0] else 0,
                      minutes=int(match[1][:-1]) if match[1] else 0,
                      seconds=int(match[2][:-1]) if match[2] else 0)
    if delta.total_seconds() > 0:
        return str(delta)
    else:
        return "LIVE"


def fetchUrl(url):
    m = YT_ID_REGEX.search(url)
    if not m:
        return False
    
    tr = requests.get('https://www.googleapis.com/youtube/v3/videos?key={0}&part=snippet,statistics,contentDetails&maxResults=1&id={1}'.format(config.google_apikey, m.group(1)))
    
    if tr.status_code == requests.codes.ok:
        tr = tr.json()
        if tr:
            if tr["pageInfo"]["totalResults"] > 0:
                # From limnoria's SpiffyTitles
                video = tr["items"][0]
                snippet = video["snippet"]
                
                title = snippet["title"]
                
                statistics = video["statistics"]

                channel_title = snippet["channelTitle"]
                video_duration = video["contentDetails"]["duration"]
                duration = youtube_duration_to_time(video_duration)

                return "{} (by {}) | Duration: {} | Views: {:,} | {:,} Likes / {:,} Dislikes".format(title, channel_title, duration,
                                    int(statistics["viewCount"]), int(statistics["likeCount"]), int(statistics["dislikeCount"]))
                
    
    

@commandHook(['youtube', 'yt'], help="Fetches youtube video")
def youtube(bot, ev):
    if len(ev.args) == 0:
        return bot.say("Usage: .yt <some text>")
    
    query = urllib.parse.quote_plus(" ".join(ev.args))
    url = "https://www.googleapis.com/youtube/v3/search?part=snippet&maxResults=1&safeSearch=moderate&key={0}&q={1}".format(config.google_apikey, query)
    res = requests.get(url)
    if res.status_code == requests.codes.ok:
        res = res.json()
        if len(res['items']) > 0:
            try:
                title = res['items'][0]['snippet']['title']
                video_id = res['items'][0]['id']['videoId']
                return bot.say('[\002Youtube Search\002] {0} | https://youtu.be/{1}'.format(title, video_id))
            except:
                pass
        return bot.say('No results found')
    

