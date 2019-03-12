from dors import commandHook
import twitter
import config
from datetime import datetime
from babel.dates import format_timedelta

api = twitter.Api(consumer_key=config.twitter_consumer_key, consumer_secret=config.twitter_consumer_secret, application_only_auth=True)

def getTweet(status_id):
    global api
    try:
        status = api.GetStatus(status_id)
        del_regist = datetime.utcnow() - datetime.strptime(status.created_at, '%a %b %d %H:%M:%S +0000 %Y')
        text = status.text
        # Find all hashtags and replace them
        for h in status.hashtags:
            text = text.replace('#' + h.text, '<a href="https://twitter.com/hashtag/{0}">#{0}</a>'.format(h.text))
        message = "[\002Tweet\002] {0}{1} (@{2}) - <b>{3}</b> Retweets - <b>{4}</b> Likes - Posted {5} ago <br>{6}"
        return message.format("\u2705 " if status.user.verified else "", status.user.name, status.user.screen_name, 
                              status.retweet_count, status.favorite_count, format_timedelta(del_regist, locale='en_US'), text)
    except:
        return False


def getUser(screenname):
    try:
        return api.GetUser(screen_name=screenname)
    except:
        return False


@commandHook(['twitter'])
def twitterUser(bot, ev):
    if len(ev.args) == 0:
        return bot.say('Usage: .twitter <status ID|@user>')
    
    try:
        int(ev.args[0])
        an = True
    except ValueError:
        an = False
        
    if ev.args[0][0] == '@' or not an:
        user = getUser(ev.args[0].replace('@', ''))
        if not user:
            return bot.say("Couldn't fetch user")
        
        message = "{0}<b>{1}</b> (@{2}): {3}  - Joined: {8} - https://twitter.com/{2}<br><b>{4:,}</b> Tweets - <b>{5:,}</b> Following - <b>{6:,}</b> Followers - <b>{7:,}</b> Likes<br><p>{9}</p>"
        joined = datetime.strptime(user.created_at, '%a %b %d %H:%M:%S +0000 %Y')
        message = message.format("\u2705 " if user.verified else "", user.name, user.screen_name, user.location,
                                 user.statuses_count, user.friends_count, user.followers_count, user.favourites_count, joined.strftime('%b %d %Y %H:%M:%S'), user.description)
        bot.message(ev.target, message, p_html=True)
    else: # assume it's a status
        status = getTweet(ev.args[0])
        if not status:
            return bot.say("Couldn't fetch status")
        
        bot.message(ev.target, status, p_html=True)
    
    
