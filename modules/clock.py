from dors import commandHook
import re
import datetime
import time
import locale
r_local = re.compile(r'\([a-z]+_[A-Z]+\)')

TimeZones = {'KST': 9, 'CADT': 10.5, 'EETDST': 3, 'MESZ': 2, 'WADT': 9,
            'EET': 2, 'MST': -7, 'WAST': 8, 'IST': 5.5, 'B': 2,
            'MSK': 3, 'X': -11, 'MSD': 4, 'CETDST': 2, 'AST': -4,
            'HKT': 8, 'JST': 9, 'CAST': 9.5, 'CET': 1, 'CEST': 2,
            'EEST': 3, 'EAST': 10, 'METDST': 2, 'MDT': -6, 'A': 1,
            'UTC': 0, 'ADT': -3, 'EST': -5, 'E': 5, 'D': 4, 'G': 7,
            'F': 6, 'I': 9, 'H': 8, 'K': 10, 'PDT': -7, 'M': 12,
            'L': 11, 'O': -2, 'MEST': 2, 'Q': -4, 'P': -3, 'S': -6,
            'R': -5, 'U': -8, 'T': -7, 'W': -10, 'WET': 0, 'Y': -12,
            'CST': -6, 'EADT': 11, 'Z': 0, 'GMT': 0, 'WETDST': 1,
            'C': 3, 'WEST': 1, 'CDT': -5, 'MET': 1, 'N': -1, 'V': -9,
            'EDT': -4, 'UT': 0, 'PST': -8, 'MEZ': 1, 'BST': 1,
            'ACS': 9.5, 'ATL': -4, 'ALA': -9, 'HAW': -10, 'AKDT': -8,
            'AKST': -9,
            'BDST': 2}

TZ1 = {
 'NDT': -2.5,
 'BRST': -2,
 'ADT': -3,
 'EDT': -4,
 'CDT': -5,
 'MDT': -6,
 'PDT': -7,
 'YDT': -8,
 'HDT': -9,
 'BST': 1,
 'MEST': 2,
 'SST': 2,
 'FST': 2,
 'CEST': 2,
 'EEST': 3,
 'WADT': 8,
 'KDT': 10,
 'EADT': 13,
 'NZD': 13,
 'NZDT': 13,
 'GMT': 0,
 'UT': 0,
 'UTC': 0,
 'WET': 0,
 'WAT': -1,
 'AT': -2,
 'FNT': -2,
 'BRT': -3,
 'MNT': -4,
 'EWT': -4,
 'AST': -4,
 'EST': -5,
 'ACT': -5,
 'CST': -6,
 'MST': -7,
 'PST': -8,
 'YST': -9,
 'HST': -10,
 'CAT': -10,
 'AHST': -10,
 'NT': -11,
 'IDLW': -12,
 'CET': 1,
 'MEZ': 1,
 'ECT': 1,
 'MET': 1,
 'MEWT': 1,
 'SWT': 1,
 'SET': 1,
 'FWT': 1,
 'EET': 2,
 'UKR': 2,
 'BT': 3,
 'ZP4': 4,
 'ZP5': 5,
 'ZP6': 6,
 'WST': 8,
 'HKT': 8,
 'CCT': 8,
 'JST': 9,
 'KST': 9,
 'EAST': 10,
 'GST': 10,
 'NZT': 12,
 'NZST': 12,
 'IDLE': 12
}

TZ3 = {
   'AEST': 10,
   'AEDT': 11,
   'ART': -3
}

TimeZones.update(TZ1)
TimeZones.update(TZ3)

@commandHook(['time', 't'], help=".time UTC")
def f_time(self, ev):
    """Returns the current time."""
    tz = ev.args[0] if ev.args else 'GMT'

    TZ = tz.upper()
    if len(tz) > 30: return

    if (TZ == 'UTC') or (TZ == 'Z'):
        msg = time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())
        self.message(ev.replyto, msg)
    elif r_local.match(tz): # thanks to Mark Shoulsdon (clsn)
        locale.setlocale(locale.LC_TIME, (tz[1:-1], 'UTF-8'))
        msg = time.strftime("%A, %d %B %Y %H:%M:%SZ", time.gmtime())
        self.message(ev.replyto, msg)
    elif TZ in TimeZones:
        offset = TimeZones[TZ] * 3600
        timenow = time.gmtime(time.time() + offset)
        msg = time.strftime("%a, %d %b %Y %H:%M:%S " + str(TZ), timenow)
        self.message(ev.replyto, msg)
    elif tz and tz[0] in ('+', '-') and 4 <= len(tz) <= 6:
        import re
        ## handle invalid inputs and typos
        ## ie: "--12" or "++8.5"
        find_tz = re.compile('(\+|-)([\.\d]+)')
        new_tz = find_tz.findall(tz)
        if new_tz and len(new_tz[0]) > 1:
            sign = new_tz[0][0]
            tz_found = new_tz[0][1]
            tz_final = float(tz_found) * int(str(sign) + '1')
        else:
            return ValueError
        timenow = time.gmtime(time.time() + (float(tz_final) * 3600))
        if tz_final % 1 == 0.0:
            tz_final = int(tz_final)
        if tz_final >= 100 or tz_final <= -100:
            return self.reply('Time requested is too far away.')
        msg = time.strftime("%a, %d %b %Y %H:%M:%S UTC" + "%s%s" % (str(sign), str(abs(tz_final))), timenow)
        self.message(ev.replyto, msg)
    else:
        try: t = float(tz)
        except ValueError:
            import os, re, subprocess
            r_tz = re.compile(r'^[A-Za-z]+(?:/[A-Za-z_]+)*$')
            if r_tz.match(tz) and os.path.isfile('/usr/share/zoneinfo/' + tz):
                cmd, PIPE = 'TZ=%s date' % tz, subprocess.PIPE
                proc = subprocess.Popen(cmd, shell=True, stdout=PIPE)
                self.message(ev.replyto, proc.communicate()[0])
            else:
                error = "Sorry, I don't know about the '%s' timezone." % tz
                self.message(ev.replyto, ev.source + ': ' + error)
        else:
            if t >= 100 or t <= -100:
                return self.reply('Time requested is too far away.')
            try:
                timenow = time.gmtime(time.time() + (t * 3600))
            except:
                return self.reply('Time requested is too far away.')
            if t >= 0:
                sign = '+'
            elif t < 0:
                sign = '-'
            if tz.startswith('+') or tz.startswith('-'):
                tz = tz[1:]
            #if int(tz) % 1 == 0.0:
            if type(float()) == tz:
                ## if tz is a whole number
                tz = int(tz)
            msg = time.strftime("%a, %d %b %Y %H:%M:%S UTC" + "%s%s" % (sign, str(tz)), timenow)
            self.message(ev.replyto, msg)

@commandHook('yi')
def yi(irc, ev):
    irc.message(ev.replyto, "Yi yan! Chin chong!")
