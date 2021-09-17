from nio import MatrixRoom

from dors import command_hook, Jenny, HookMessage
import config
import requests
import datetime

dotw = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']


def wind_dir(degrees):
    """Provide a nice little unicode character of the wind direction"""
    # Taken from jenni
    if degrees == 'VRB':
        degrees = '\u21BB'  # ↻
    elif (degrees <= 22.5) or (degrees > 337.5):
        degrees = '\u2B06'  # ⬆
    elif (degrees > 22.5) and (degrees <= 67.5):
        degrees = '\u2197'  # ↗
    elif (degrees > 67.5) and (degrees <= 112.5):
        degrees = '\u27A1'  # →
    elif (degrees > 112.5) and (degrees <= 157.5):
        degrees = '\u2198'  # ↘
    elif (degrees > 157.5) and (degrees <= 202.5):
        degrees = '\u2B07'  # ⬇
    elif (degrees > 202.5) and (degrees <= 247.5):
        degrees = '\u2199'  # ↙
    elif (degrees > 247.5) and (degrees <= 292.5):
        degrees = '\u2B05'  # ←
    elif (degrees > 292.5) and (degrees <= 337.5):
        degrees = '\u2196'  # ↖

    return degrees


def speed_desc(speed):
    """Provide a more natural description of wind speed"""
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
    else:
        description = '\002\00305FUCKING HURRICANE\003\002'

    return description


def weather_desc(condition):
    emoji = ''
    if condition == "Rain":
        emoji = "🌧️ "
    elif condition == "Partly Cloudy Day":
        emoji = "🌥️ "
    elif condition == "Cloudy":
        emoji = "☁️ "
    elif condition in ("Clear Day", "Clear"):
        emoji = "🌞 "

    return f"{emoji}\002{condition}\002"


def get_forecast(weather_obj, day):
    cond = weather_obj['daily']['data'][day]['icon'].replace('-', ' ').title().strip()

    matemp = weather_obj['daily']['data'][day]['temperatureMax']
    mitemp = weather_obj['daily']['data'][day]['temperatureMin']
    matemp_f = round(matemp * 1.8 + 32)
    mitemp_f = round(mitemp * 1.8 + 32)
    dotw_day = datetime.datetime.fromtimestamp(weather_obj['daily']['data'][day]['time']).weekday()
    reply = '<li>\x0310\x02\x1F{0}\x1F\x02\x03: '.format(dotw[dotw_day] if day > 0 else 'Today')

    reply += f"{weather_desc(cond)} - Max temp: {matemp}\u00B0C ({matemp_f}\u00B0F)"
    reply += " Min temp: {0}\u00B0C ({1}\u00B0F).</li>".format(mitemp, mitemp_f)
    return reply


@command_hook(['weather', 'wx', 'w'], help="Shows the weather for a given location. Usage: weather <location>")
async def weather(bot: Jenny, room: MatrixRoom, event: HookMessage):
    if not event.args:
        return await bot.say("Usage: weather <location>")
    location = " ".join(event.args)
    
    coords = requests.get('https://maps.googleapis.com/maps/api/geocode/json?address={0}&key={1}'
                          .format(location, config.google_apikey)).json()
    
    if coords['status'] == 'ZERO_RESULTS':
        return await bot.say("Found zero results for \002{0}\002".format(location))
    elif coords['status'] != 'OK':
        return await bot.say("Unknown error.")
    
    location = coords['results'][0]['formatted_address']
    latitude = coords['results'][0]['geometry']['location']['lat']
    longitude = coords['results'][0]['geometry']['location']['lng']
    weather = requests.get('https://api.darksky.net/forecast/{0}/{1},{2}?units=si&exclude=minutely,hourly'
                           .format(config.darksky_apikey, latitude, longitude)).json()
    
    # currently
    cond = weather['currently']['icon'].replace('-', ' ').title().strip()

    reply = "Weather on \00310\002{0}\002\003: \002{1}\002: ".format(location, weather_desc(cond))
    temp = weather['currently']['temperature']
    aptemp = weather['currently']['apparentTemperature']
    temp_f = round(weather['currently']['temperature'] * 1.8 + 32)
    aptemp_f = round(weather['currently']['apparentTemperature'] * 1.8 + 32)
    reply += "\002{0}\u00B0C\002 (\002{1}\u00B0F\002)".format(temp, temp_f)
    if temp != aptemp:
        reply += " [feels like {0}\u00B0C ({1}\u00B0F)]".format(aptemp, aptemp_f)
    
    pressure = weather['currently']['pressure']
    humidity = weather['currently']['humidity']
    reply += ", humidity: \002{0}\002%".format(round(humidity*100, 2))
    reply += ", pressure: \002{0}\002hPa".format(round(pressure, 2))
    
    speed = weather['currently']['windSpeed']
    degrees = weather['currently']['windBearing']

    degrees = wind_dir(degrees)
    speed_mph = speed * 0.621371
    description = speed_desc(speed_mph)

    reply += ", wind: \002{0}\002 {1}kmh ({2}mph) ({3}). ".format(description, speed, round(speed_mph), degrees)

    reply += " \n\nForecast: <ul>"
    reply += get_forecast(weather, 0)
    reply += get_forecast(weather, 1)
    reply += get_forecast(weather, 2)
    reply += get_forecast(weather, 3)
    reply += "</ul>"
    await bot.message(room.room_id, reply, p_html=True)
