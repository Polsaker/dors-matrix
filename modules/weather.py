from dors import commandHook
import config
import requests
import datetime

dotw = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']

def wind_dir(degrees):
    '''Provide a nice little unicode character of the wind direction'''
    # Taken from jenni
    if degrees == 'VRB':
        degrees = '\u21BB'
    elif (degrees <= 22.5) or (degrees > 337.5):
        degrees = '\u2191'
    elif (degrees > 22.5) and (degrees <= 67.5):
        degrees = '\u2197'
    elif (degrees > 67.5) and (degrees <= 112.5):
        degrees = '\u2192'
    elif (degrees > 112.5) and (degrees <= 157.5):
        degrees = '\u2198'
    elif (degrees > 157.5) and (degrees <= 202.5):
        degrees = '\u2193'
    elif (degrees > 202.5) and (degrees <= 247.5):
        degrees = '\u2199'
    elif (degrees > 247.5) and (degrees <= 292.5):
        degrees = '\u2190'
    elif (degrees > 292.5) and (degrees <= 337.5):
        degrees = '\u2196'

    return degrees
    
def speed_desc(speed):
    '''Provide a more natural description of wind speed'''
    # taken from jennifer

    if speed < 1:
        description = 'Calm'
    elif speed < 4:
        description = 'Light air'
    elif speed < 7:
        description = 'Light breeze'
    elif speed < 11:
        description = 'Gentle breeze'
    elif speed < 16:
        description = 'Moderate breeze'
    elif speed < 22:
        description = 'Fresh breeze'
    elif speed < 28:
        description = 'Strong breeze'
    elif speed < 34:
        description = 'Near gale'
    elif speed < 41:
        description = 'Gale'
    elif speed < 48:
        description = 'Strong gale'
    elif speed < 56:
        description = 'Storm'
    elif speed < 64:
        description = 'Violent storm'
    else: description = 'Hurricane'

    return description


def getForecast(weather, day):
    cond = weather['daily']['data'][day]['icon'].replace('-', ' ').title()
    cond = cond.replace('Day', '').replace('Night', '')

    matemp = weather['daily']['data'][day]['temperatureMax']
    mitemp = weather['daily']['data'][day]['temperatureMin']
    matemp_f = round(matemp * 1.8 + 32)
    mitemp_f = round(mitemp * 1.8 + 32)
    dotw_day = datetime.datetime.fromtimestamp(weather['daily']['data'][day]['time']).weekday()
    reply = '\x0310\x02\x1F{0}\x1F\x02\x03: '.format(dotw[dotw_day])

    reply += "\002{0}\002 - Max temp: {1}\u00B0C ({2}\u00B0F)".format(cond, matemp, matemp_f)
    reply += " Min temp: {0}\u00B0C ({1}\u00B0F). ".format(mitemp, mitemp_f)
    return reply

@commandHook(['weather', 'wx', 'w'], help="Shows the weather for a given location. Usage: weather <location>")
def weather(irc, ev):
    if not ev.args:
        return irc.message(ev.replyto, "Usage: weather <location>")
    location = " ".join(ev.args)
    
    coords = requests.get('https://maps.googleapis.com/maps/api/geocode/json?address={0}&key={1}'
                          .format(location, config.google_apikey)).json()
    
    if coords['status'] == 'ZERO_RESULTS':
        return irc.message(ev.replyto, "Found zero results for \002{0}\002".format(location))
    elif coords['status'] != 'OK':
        return irc.message(ev.replyto, "Unknown error.")
    
    location = coords['results'][0]['formatted_address']
    latitude = coords['results'][0]['geometry']['location']['lat']
    longitude = coords['results'][0]['geometry']['location']['lng']
    weather = requests.get('https://api.darksky.net/forecast/{0}/{1},{2}?units=si&exclude=minutely,hourly'
                           .format(config.darksky_apikey, latitude, longitude)).json()
    
    # currently
    cond = weather['currently']['icon'].replace('-', ' ').title()
    cond = cond.replace('Day', '').replace('Night', '')
    reply = "Weather on \00310\002{0}\002\003: \002{1}\002; ".format(location, cond)
    temp = weather['currently']['temperature']
    aptemp = weather['currently']['apparentTemperature']
    temp_f = round(weather['currently']['temperature'] * 1.8 + 32)
    aptemp_f = round(weather['currently']['apparentTemperature'] * 1.8 + 32)
    reply += "\002{0}\u00B0C\002 (\002{1}\u00B0F\002)".format(temp, temp_f)
    if temp != aptemp:
        reply += " [feels like {0}\u00B0C ({1}\u00B0F)".format(aptemp, aptemp_f)
    
    pressure = weather['currently']['pressure']
    humidity = weather['currently']['humidity']
    reply += ", humidity: \002{0}\002%".format(humidity*100)
    reply += ", pressure: \002{0}\002hPa".format(pressure)
    
    speed = weather['currently']['windSpeed']
    degrees = weather['currently']['windBearing']

    degrees = wind_dir(degrees)
    speed_mph = speed * 0.621371
    description = speed_desc(speed_mph)

    reply += ", wind: \002{0}\002 {1}kmh ({2}mph) ({3}). ".format(description, speed, round(speed_mph), degrees)

    reply += " Forecast: {0}".format(getForecast(weather, 0))
    reply += getForecast(weather, 1)
    reply += getForecast(weather, 2)
    irc.say(reply)
