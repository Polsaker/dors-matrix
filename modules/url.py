from dors import message_hook
import config
import re
import urllib.request, urllib.error, urllib.parse
import time
from bs4 import BeautifulSoup
import requests
import traceback
import datetime
from babel.dates import format_timedelta


url_finder = re.compile('(?iu)(\!?(http|https|ftp)(://\S+\.?\S+/?\S+?))')
r_entity = re.compile(r'&[A-Za-z0-9#]+;')
HTML_ENTITIES = { 'apos': "'" }


def remove_nonprint(text):
    new = str()
    for char in text:
        x = ord(char)
        if x > 32 and x <= 126:
            new += char
    return new

def fetch_twitter_url(url):
    # 1 - Try to fetch whole tweet using mobile.twitter.com
    mobile_url = url.replace('//twitter.com/', '//mobile.twitter.com/')
    if mobile_url != url:
        try:
            r = requests.get(mobile_url)
            soup = BeautifulSoup(r.text, 'lxml')
            tweet_text = soup.find('div', {"class": "dir-ltr"}).getText().strip()
            tweet_user = soup.find('span', {"class": "username"}).getText().strip()
            return "[\002Twitter\002] {0}: {1}".format(tweet_user, tweet_text)
        except Exception as e:
            print("Error on twitter mobile fetch", e)
    r = requests.get(url)
    soup = BeautifulSoup(r.text, 'lxml')
    title = str(soup.title.string)
    title = title.replace('\n', ' ').replace('\r', '')
    title = title.replace('"', '')
    title = title.replace("on Twitter", "")
    return "[\002Twitter\002] {0}".format(title)


def fetch_throat_url(ti, ma):
    if ma.group(2):
        req = requests.get("https://{0}/api/getComment/{1}".format(ti, ma.group(2)))
        if req.status_code == requests.codes.ok:
            req = req.json()
            comment = req['comment']
            regist = datetime.datetime.strptime(comment['time'], "%a, %d %b %Y %H:%M:%S %Z")
            del_regist = datetime.datetime.utcnow() - regist
            content = comment['content']
            if len(content) > 200:
                content = content[0:200] + "..."
            return '[\002{0}\002 comment] \002{1}\002 points. Created by \002{2}\002, {3} ago.<br>{4}'.format(config.throat_instances[ti], comment['score'], comment['user'], format_timedelta(del_regist, locale='en_US'), content)
    else:
        req = requests.get("https://{0}/api/getPost/{1}".format(ti, ma.group(1)))
        if req.status_code == requests.codes.ok:
            req = req.json()
            post = req['post']
            regist = datetime.datetime.strptime(post['posted'], "%a, %d %b %Y %H:%M:%S %Z")
            del_regist = datetime.datetime.utcnow() - regist
            post_type = "UNKNOWN, STRANGE"
            if post['ptype'] == 0:
                post_type = "text post"
            elif post['ptype'] == 1:
                post_type = "link post"
            elif post['ptype'] == 3:
                post_type = "poll"
            msg =  "[\002{0}\002 {1}] {2} - \002{3}\002 points (+{4}|-{5}). Created by \002{6}\002, {7} ago. {8}".format(config.throat_instances[ti], post_type, post['title'], post['score'], post['upvotes'], post['downvotes'], post['user'], format_timedelta(del_regist, locale='en_US'), post['link'] if post['link'] else '')
            
            return msg
            

def find_title(url, bot):
    for item in config.urlblacklist:
        if item in url:
            return False, False
    
    if not re.search('^((https?)|(ftp))://', url):
        url = 'http://' + url
    
    if '/#!' in url:
        url = url.replace('/#!', '/?_escaped_fragment_=')

    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/73.0.3683.75 Safari/537.36',
               'Accept': '*/*'}
    
    if 'store.steampowered.com/app' in url and 'steam' in bot.plugins:
        appid = re.search('.*store.steampowered.com/app/(\d+).*', url)
        furl = bot.plugins['steam'].getAppInfo(appid.group(1), False)
        if furl:
            return "[\002Steam\002] " + furl, False
    
    if 'twitter.com' in url:
        if 'twitter' in bot.plugins:
            m = re.match('.*twitter.com/(.+?)(?:/status/(\d*)/?.*|$)', url)
            if m:
                if m.group(2):
                    furl = bot.plugins['twitter'].getTweet(m.group(2))
                else:
                    furl = bot.plugins['twitter'].getUser(m.group(1))
                if furl:
                    return furl, True
        return fetch_twitter_url(url), True
    
    if ('youtu.be' or 'youtube.com' in url) and 'youtube' in bot.plugins:
        furl = bot.plugins['youtube'].fetchUrl(url)
        if furl:
            return "[\002Youtube\002] " + furl, False
    
    if '.wikipedia.org/wiki/' in url:
        # get the wiki's language
        wl = re.match('.*(...?)\.wikipedia\.org/wiki/(.*)', url)
        if wl:
            wiki = "https://{0}.wikipedia.org/w/api.php?format=json&action=query&prop=extracts&exsentences=1&exlimit=1&exintro=&explaintext=&titles={1}&redirects".format(wl.group(1), wl.group(2))
            wk = requests.get(wiki)
            try:
                extract = list(wk.json()['query']['pages'].values())[0]['extract']
                return "[Wikipedia] {0}".format(extract), False
            except:
                pass
    
    for ti in getattr(config, 'throat_instances', []):
        if ti in url:
            ma = re.match('.*/s/.+?/(\d+)(?:/([a-z0-9-]{36,36}))?', url)
            if ma:
                pu = fetch_throat_url(ti, ma)
                if pu:
                    return pu, True

                
    r = requests.get(url, headers=headers)
    soup = BeautifulSoup(r.text, 'lxml')
    title = str(soup.title.string)
    title = title.replace('\n', '').replace('\r', '')

    def remove_spaces(x):
        if '  ' in x:
            x = x.replace('  ', '')
            return remove_spaces(x)
        else:
            return x

    title = remove_spaces(title)

    if len(title) > 200 and 'twitter.com' not in url:
        title = title[:200] + '...'
    return "[url] {0}".format(title), False
        


def getTLD(url):
    url = url.strip()
    url = remove_nonprint(url)
    idx = 7
    if url.startswith('https://'):
        idx = 8
    elif url.startswith('ftp://'):
        idx = 6
    u = url[idx:]
    f = u.find('/')
    if f != -1:
        u = u[0:f]
    return remove_nonprint(u)


def get_results(text, irc, manual=False):
    if not text:
        return False, list()
    a = re.findall(url_finder, text)
    k = len(a)
    i = 0
    display = list()
    passs = False

    while i < k:
        url = a[i][0].encode()
        url = url.decode()
        url = remove_nonprint(url)
        domain = getTLD(url)
        if '//' in domain:
            domain = domain.split('//')[1]

        bitly = url
        
        title = find_title(url, irc)
        if title:
            display.append(title)
        
        i += 1
        
    return display


@message_hook('(?iu).*(\!?(http|https)(://\S+)).*')
def show_title_auto(irc, ev):
    try:
        results = get_results(ev.message, irc)
    except Exception as e:
        print(traceback.format_exc())
        return

    k = 1
    print("ur, res", results)
    for (r, trust) in results:
        if not r:
            continue
        ## loop through link, shorten pairs, and titles
        if k > 3:
            ## more than 3 titles to show from one line of text?
            ## let's just show only the first 3.
            break
        k += 1

        irc.message(ev.replyto, r, p_html=trust)

