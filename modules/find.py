from dors import stuffHook, startupHook
import time
import sqlite3
import re

def checkdb(c):
    c.execute("CREATE TABLE IF NOT EXISTS find ( channel text,\
            nick text, line text, ts text)")
            
def load_db():
    conn = sqlite3.connect('find.db')
    c = conn.cursor()
    checkdb(c)
    conn.commit()
    
    c.execute("SELECT * FROM find")
    
    search_dict = {}
    
    for i in c:
        try:
            search_dict[i[0]]
        except KeyError:
            search_dict[i[0]] = {}
        
        try:
            search_dict[i[0]][i[1]]
        except KeyError:
            search_dict[i[0]][i[1]] = []
        try:
            search_dict[i[0]][i[1]].append([i[2], int(i[3])])
        except:
            continue
    
    return search_dict

def save_db(search_dict):
    conn = sqlite3.connect('find.db')
    c = conn.cursor()
    checkdb(c)
    conn.commit()
    
    c.execute("DELETE FROM find")
    
    for x in search_dict:
        for y in search_dict[x]:
            for z in search_dict[x][y]:
                c.execute("INSERT INTO find VALUES (?,?,?,?)", (x, y, z[0], z[1]))
        conn.commit()

@startupHook()
def startup(irc):
    irc.recent_lines = load_db()
    while True:
        time.sleep(60)
        save_db(irc.recent_lines)

@stuffHook(".+")
def collectlines(irc, ev):        
    channel = ev.target.lower()
    nick = str(ev.source).lower()
    if not channel.startswith('#'): return
    
    if channel not in irc.recent_lines:
        irc.recent_lines[channel] = {}
        
    if nick not in irc.recent_lines[channel]:
        irc.recent_lines[channel][nick] = []
        
    templist = irc.recent_lines[channel][nick]
    line = ev.message
    if line.startswith("s/"):
        return
    elif line.startswith("\x01ACTION"):
        line = line[:-1]
        templist.append([line, int(time.time())])
    else:
        templist.append([line, int(time.time())])
    del templist[:-10]
    irc.recent_lines[channel][nick] = templist

@stuffHook('(?iu)(?:([^\s:,]+)[\s:,])?\s*s\s*([^\s\w.:-])(.*)')
def findandreplace(irc, ev):
    channel = ev.target.lower()
    nick = ev.source.lower()
    if not channel.startswith('#'): return

    rnick = ev.match.group(1) or nick # Correcting other person vs self.

    # only do something if there is conversation to work with
    if channel not in irc.recent_lines or rnick not in irc.recent_lines[channel]: return

    sep = ev.match.group(2)
    rest = ev.match.group(3).split(sep)
    me = False # /me command
    flags = ''
    if len(rest) < 2:
        return # need at least a find and replacement value
    elif len(rest) > 2:
        # Word characters immediately after the second separator
        # are considered flags (only g and i now have meaning)
        flags = re.match(r'\w*',rest[2], re.U).group(0)
    #else (len == 2) do nothing special

    count = 'g' in flags and -1 or 1 # Replace unlimited times if /g, else once
    if 'i' in flags:
        regex = re.compile(re.escape(rest[0]),re.U|re.I)
        repl = lambda s: re.sub(regex,rest[1],s,count == 1)
    else:
        repl = lambda s: s.replace(rest[0],rest[1],count)

    for line in reversed(irc.recent_lines[channel][rnick]):
        line = line[0]
        if line.startswith("\x01ACTION"):
            me = True # /me command
            line = line[8:]
        else:
            me = False
        new_phrase = repl(line)
        if new_phrase != line: # we are done
            break

    if not new_phrase or new_phrase == line: return # Didn't find anything

    if len(new_phrase) > 512:
        new_phrase = new_phrase[:512]

    # Save the new "edited" message.
    templist = irc.recent_lines[channel][rnick]
    templist.append((me and '\x01ACTION ' or '') + new_phrase)
    irc.recent_lines[channel][rnick] = templist
    save_db(irc.recent_lines)

    # output
    phrase = nick + (ev.match.group(1) and ' thinks ' + rnick or '') + (me and ' ' or " \x02meant\x02 to say: ") + new_phrase
    if me and not ev.match.group(1): phrase = '\x02' + phrase + '\x02'
    irc.message(ev.replyto, phrase)
