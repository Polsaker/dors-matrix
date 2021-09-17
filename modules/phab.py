from dors import message_hook, startup_hook
import re
import traceback
import requests
import copy
import time
import phabricator
import config
phab = phabricator.Phabricator(host=config.phab_host, username=config.phab_user, token=config.phab_token)

case1 = re.compile(r'(?<![/:#-])(?:^|\b)([A-Z])(\d+)(?:\b|$)')
case2 = re.compile(r'(?<![/:#-])(?:^|\b)(r[A-Z]+)([0-9a-z]{0,40})(?:\b|$)')
oldies = {}
poll_last_seen_chrono_key = 0

@message_hook('.*')
def handle_phabs(irc, ev):
    paste_ids = []
    commit_names = []
    vote_ids = []
    file_ids = []
    object_names = []
    output = {}
    # Case 1
    matches = case1.finditer(ev.message)
    for match in matches:
        if match.group(1) == "P":
            paste_ids.append(match.group(2))
        elif match.group(1) == "V":
            vote_ids.append(match.group(2))
        elif match.group(1) == "F":
            file_ids.append(match.group(2))
        else:
            name = match.group(1) + match.group(2)
            object_names.append(name)
    # Case 2
    matches = case2.finditer(ev.message)
    for match in matches:
        if match.group(2):
            commit_names.append(match.group(1) + match.group(2))
        else:
            object_names.append(match.group(1))
    # processing
    # 1 - objects:
    if object_names:
        try:
            objects = phab.phid.lookup(names=object_names)
            for name,item in objects.items():
                output[item['phid']] = item['fullName'] + ' - ' + item['uri']
        except:
            pass
    # 2 - votes
    if vote_ids:
        for vid in vote_ids:
            try:
                item = phab.slowvote.info(poll_id=int(vid))
            except:
                continue
            output[item['phid']] = "V" + vid + ": " + item['question'] + ' - ' + item['uri']
    # 3 - files
    if file_ids:
        for fid in file_ids:
            try:
                item = phab.file.info(id=fid)
            except:
                continue
            output[item['phid']] = item['objectName'] + ": " + item['uri'] + ' - ' + item['name']
    # 4 - paste
    if paste_ids:
        for fid in file_ids:
            try:
                item = phab.paste.query(ids=[fid]).popitem()
            except:
                continue

            output[item['phid']] = "V" + fid + ": " + item['uri'] + ' - ' + item['title']
            if item['language']:
                output[item['phid']] += " (" + language + ")"
            user = list(phab_query(phids=[item['authorPHID']]))
            if user:
                output[item['phid']] += " by " + user[0]['userName']
    # 5 - commit
    if commit_names:
        try:
            objects = phab.diffusion.querycommits(names=commit_names)
        except:
            objects = {'data': {}}

        for name,item in objects['data'].items():
            output[item['phid']] = item['summary']
            user = list(phab_query(phids=[item['authorPHID']]))
            if user:
                output[item['phid']] += " by " + user[0]['userName']
            output[item['phid']] += " - " + item['uri']
    
    defout = []
    for x in copy.copy(output):
        if oldies.get(x):
            if (time.time() - oldies[x]) < 600:
                del output[x]
                continue
        oldies[x] = time.time()
        defout.append(output[x])
    
    if defout:
        irc.message(ev.target, '\n'.join(defout))


@startup_hook()
def onstart(bot):
    while True:
        try:
            poll(bot)
        except:
            bot.message('!mrhgfTkELkPbTYscKH:phuks.co', traceback.format_exc())
        time.sleep(2)


def phid_info(phid):
    info = phab.phid.query(phids=[phid])
    return list(info.values())[0]

def get_user_name(phid):
    if phid == 'PHID-APPS-PhabricatorHarbormasterApplication':
        return 'Harbormaster'
    info = phab_query(phids=[phid])
    print(info, phid)
    return info[0]['userName']

def phab_query(*args, **kwargs):
    try:
        return phab.user.query(*args, **kwargs)
    except:
        return []


def poll(bot):
    global poll_last_seen_chrono_key, phid_info, get_user_name
    if poll_last_seen_chrono_key == 0:
        # First time, get the latest event and start from there
        latest = list(phab.feed.query(limit='1', view="text").values())[0]
        poll_last_seen_chrono_key = int(latest['chronologicalKey'])

    events = phab.feed.query(view='text')

    
    if not events:
        # PHP bug, what should be {} is actually []
        return
    events = list(events.values())
    # Events are in the order of most recent first to oldest, so reverse!
    events.reverse()
    for event in events:
        key = int(event['chronologicalKey'])
        if key > poll_last_seen_chrono_key:
            aphid_info = phid_info(event['objectPHID'])
            tuff = "[\002{0}\002] {1} (\00311{2}\003)".format(get_user_name(event['authorPHID']), event['text'], aphid_info['uri'])
            bot.message(config.phab_chan, tuff)
            #self.process_event(event)
            poll_last_seen_chrono_key = key

