from dors import commandHook, startupHook
import sqlite3

def checkdb(c):
    c.execute("CREATE TABLE IF NOT EXISTS autojoin (channel text)")


@commandHook('join', help="Joins a channel. If 'auto' is used as the second "\
                          "parameter, the channel is added to the autojoin " \
                          "list. Usage: .join #channel [auto]")
def join(irc, event):
    if not irc.isadmin(event.source):
        irc.message(event.replyto, "Not authorized")
        return
    
    if not event.args:
        irc.message(event.replyto, "{0}: {1}".format(event.source, rssadmin._help))
        irc.message(event.replyto, "{0}: No parameters specified".format(event.source))
        return
    
    irc.message(event.replyto, "Trying to join \002{0}\002".format(event.args[0]))

    irc.join(event.args[0])
    
    if len(event.args) > 1 and event.args[1] == "auto":
        conn = sqlite3.connect('rss.db')
        c = conn.cursor()
        checkdb(c)
        c.execute("INSERT INTO autojoin VALUES (?)", (event.args[0].lower(),))
        conn.commit()
        c.close()
        irc.message(event.replyto, "Channel \002{0}\002 added to autojoin.".format(event.args[0]))


@commandHook('part', help="Leaves a channel. If the channel is in the autojoin "\
                          "list it will be removed. Usage: .part #channel")
def part(irc, event):
    if not irc.isadmin(event.source):
        irc.message(event.replyto, "Not authorized")
        return
    
    if not event.args:
        irc.message(event.replyto, "{0}: {1}".format(event.source, rssadmin._help))
        irc.message(event.replyto, "{0}: No parameters specified".format(event.source))
        return
    
    irc.part(event.args[0])
    irc.message(event.replyto, "Trying to leave \002{0}\002".format(event.args[0]))
    
    conn = sqlite3.connect('rss.db')
    c = conn.cursor()
    checkdb(c)
    c.execute("DELETE FROM autojoin WHERE channel = ?", (event.args[0].lower(),))
    conn.commit()
    c.close()


@startupHook()
def autojoin(irc):
    conn = sqlite3.connect('rss.db')
    c = conn.cursor()
    checkdb(c)
    c.execute("SELECT * FROM autojoin")
    for row in c:
        irc.join(row[0])
