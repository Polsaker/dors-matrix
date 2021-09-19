import datetime
import time
from typing import Optional

import aiohttp
from nio import MatrixRoom

import config
from dors import command_hook, Jenny, HookMessage

dotw = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']


async def fetch(session, url):
    async with session.get(url) as response:
        return await response.json()


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


def moon_to_emoji(phase: float) -> str:
    if phase == 0 or phase == 1:
        return "\U0001F311"  # New moon
    elif 0 < phase < 0.25:
        return "\U0001F312"  # Waxing crascent
    elif phase == 0.25:
        return "\U0001F313"  # First quarter moon
    elif 0.25 < phase < 0.5:
        return "\U0001F314"  # Waxing gibbous
    elif phase == 0.5:
        return "\U0001F315"  # full moon
    elif 0.5 < phase < 0.75:
        return "\U0001F316"  # Waning gibbous
    elif phase == 0.75:
        return "\U0001F317"  # Last quarter moon
    elif 0.75 < phase < 1:
        return "\U0001F318"  # Waning crescent


def get_condition(data, is_night: bool, moon_phase: Optional[int] = None):
    if data['id'] == 200:  # 2xx: Thunderstorm
        return "⛈ Thunderstorm with light rain"
    elif data['id'] == 201:
        return "⛈ Thunderstorm with rain"
    elif data['id'] == 202:
        return "⛈ Thunderstorm with heavy rain"
    elif data['id'] == 210:
        return "⛈ Light thunderstorm"
    elif data['id'] == 211:
        return "⛈ Thunderstorm"
    elif data['id'] == 212:
        return "⛈⛈ Heavy thunderstorm"
    elif data['id'] == 221:
        return "⛈ Ragged thunderstorm"
    elif data['id'] == 230:
        return "⛈ Thunderstorm with light drizzle"
    elif data['id'] == 231:
        return "⛈ Thunderstorm with drizzle"
    elif data['id'] == 232:
        return "⛈ 🌬🪨🚗 <font color=\"red\">Thunderstorm heavy drizzle</font>"
    elif data['id'] == 300:
        return "☁ Light intensity drizzle"
    elif data['id'] == 301:
        return "☁ Drizzle"
    elif data['id'] == 302:
        return "☁🌬🪨🚗 <font color=\"red\">Heavy intensity drizzle</font>"
    elif data['id'] == 310:
        return "🌧 Light intensity drizzle rain"
    elif data['id'] == 311:
        return "🌧 Drizzle rain"
    elif data['id'] == 312:
        return "🌧🌬🪨🚗 <font color=\"red\">Heavy intensity drizzle rain</font>"
    elif data['id'] == 313:
        return "🌧 Shower rain and drizzle"
    elif data['id'] == 314:
        return "🌧🌧 Heavy shower rain and drizzle"
    elif data['id'] == 321:
        return "🌧🌧 Shower drizzle"
    elif data['id'] == 500:  # 5xx: Rain
        return "🌧 Light rain"
    elif data['id'] == 501:
        return "🌧 Moderate rain"
    elif data['id'] == 502:
        return "🌧🌧 Heavy intensity rain"
    elif data['id'] == 503:
        return "🌧🌧🌧 <font color=\"red\">Very heavy rain</font>"
    elif data['id'] == 504:
        return "🌧🌧🌧 <font color=\"red\">EXTREME RAIN</font>"
    elif data['id'] == 511:
        return "🌧❄ Freezing rain"
    elif data['id'] == 520:
        return "🌧 Light intensity shower rain"
    elif data['id'] == 521:
        return "🌧 Shower rain"
    elif data['id'] == 522:
        return "🌧🌧 Heavy intensity shower rain"
    elif data['id'] == 531:
        return "🌧 Ragged shower rain"
    elif data['id'] == 600:  # 6xx: Snow
        return "🌨 Light snow"
    elif data['id'] == 601:
        return "🌨 Snow"
    elif data['id'] == 602:
        return "🌨🌨 Heavy snow"
    elif data['id'] == 611:
        return "🌨 Sleet"
    elif data['id'] == 612:
        return "🌨 Light shower sleet"
    elif data['id'] == 613:
        return "🌨 Shower sleet"
    elif data['id'] == 615:
        return "🌨 Light rain and snow"
    elif data['id'] == 616:
        return "🌨 Rain and snow"
    elif data['id'] == 620:
        return "🌨 Light shower snow"
    elif data['id'] == 621:
        return "🌨 Shower snow"
    elif data['id'] == 622:
        return "🌨🌨 Heavy shower snow"
    elif data['id'] == 701:  # 7xx: Atmosphere
        return "🌫 Mist"
    elif data['id'] == 711:
        return "🌁 Smoke"
    elif data['id'] == 721:
        return "🌁 Haze"
    elif data['id'] == 731:
        return "🌫 Dust"
    elif data['id'] == 741:
        return "🌫 Fog"
    elif data['id'] == 751:
        return "🌫 Sand"
    elif data['id'] == 761:
        return "🌫 Dust"
    elif data['id'] == 762:
        return "🌋🌫 Volcanic ash"
    elif data['id'] == 771:
        return "🌬 Squall"
    elif data['id'] == 781:
        return "🌪 <font color=\"red\">FUCKING TORNADO</font>"
    elif data['id'] == 800:  # 800: Clear
        return "🌞 Clear" if not is_night else (moon_to_emoji(moon_phase) + " Clear night")
    elif data['id'] == 801:
        return "🌤 Few clouds"
    elif data['id'] == 802:
        return "🌤 Scattered clouds"
    elif data['id'] == 803:
        return "🌥 Broken clouds"
    elif data['id'] == 804:
        return "🌥 Overcast clouds"
    else:
        return "I don't even know D:"


def get_uvi(uvi):
    if 0 < uvi < 3:
        return f"<b><font color=\"green\">Low</font></b> ({uvi})"
    elif 3 < uvi < 6:
        return f"<b><font color=\"yellow\">Moderate</font></b> ({uvi})"
    elif 6 < uvi < 8:
        return f"<b><font color=\"orange\">High</font></b> ({uvi})"
    elif 8 < uvi < 11:
        return f"<b><font color=\"red\">Very high</font></b> ({uvi})"
    elif uvi > 11:
        return f"<b><font color=\"violet\">Extreme</font></b> ({uvi})"


def get_f(temp):
    return f"{round((temp - 273.15) * 9 / 5 + 32)}\u00B0F"


def get_c(temp):
    return f"{round(temp - 273.15, 1)}\u00B0C"


def get_mph(speed):
    return f"{round(speed / 1.609, 2)}"


def get_conditions(data, is_night: bool, moon_phase: Optional[int] = None):
    resp = ""
    for i in data:
        print(data)
        resp += get_condition(i, is_night, moon_phase) + " "

    return resp


def get_forecast(data):
    dotw_now = datetime.datetime.now().weekday()
    dotw_day = datetime.datetime.fromtimestamp(data['dt']).weekday()
    dotw_day = dotw[dotw_day] if dotw_day != dotw_now else "Today"
    reply = f"\x0310\x02\x1F{dotw_day}\x1F\x02\x03: <b>{get_conditions(data['weather'], False, None)}</b>. "
    reply += f"Min temp: {get_c(data['temp']['min'])} ({get_f(data['temp']['min'])}). "
    reply += f"Min temp: {get_c(data['temp']['max'])} ({get_f(data['temp']['max'])}). "
    reply += f"Humidity: <b>{data['humidity']}</b>%. UV Index: {get_uvi(data['uvi'])}."
    return reply


@command_hook('w2')
async def weather2(bot: Jenny, room: MatrixRoom, event: HookMessage):
    if not event.args:
        return await bot.say("Usage: weather <location>")
    location = " ".join(event.args)

    await bot.room_typing(room.room_id, True, 10000)
    async with aiohttp.ClientSession() as session:
        coords = await fetch(session, "https://maps.googleapis.com/maps/api/geocode/json"
                                      f"?address={location}&key={config.google_apikey}")

        if coords['status'] == 'ZERO_RESULTS':
            return await bot.say("Found zero results for \002{0}\002".format(location))
        elif coords['status'] != 'OK':
            return await bot.say("Unknown error.")

        location = coords['results'][0]['formatted_address']
        latitude = coords['results'][0]['geometry']['location']['lat']
        longitude = coords['results'][0]['geometry']['location']['lng']

        weather_data = await fetch(session, "https://api.openweathermap.org/data/2.5/onecall"
                                            f"?lat={latitude}&lon={longitude}&appid={config.openweather_apikey}")

    await bot.room_typing(room.room_id, False)
    resp = f"Weather in <b>\00310{location}\003</b>: "
    curr_weather = weather_data['current']
    curr = get_conditions(curr_weather['weather'],
                          time.time() > curr_weather['sunset'],
                          moon_phase=weather_data['daily'][0]['moon_phase'])
    resp += f"<b>{curr}</b> - <b>{get_c(curr_weather['temp'])}</b> (<b>{get_f(curr_weather['temp'])}</b>)"
    resp += f" - Feels like <b>{get_c(curr_weather['feels_like'])}</b> (<b>{get_f(curr_weather['feels_like'])}</b>). "
    resp += f" Humidity: <b>{curr_weather['humidity']}</b>%, pressure: <b>{curr_weather['pressure']}</b>hPa.<br/>"
    resp += f"Wind: <b>{curr_weather['wind_speed']}</b> km/h ({get_mph(curr_weather['wind_speed'])} mph) "
    resp += f"<b>{speed_desc(curr_weather['wind_speed'])}</b> ({wind_dir(curr_weather['wind_deg'])})."
    resp += "<br><br>Forecast:<ul>"
    resp += f"<li>{get_forecast(weather_data['daily'][0])}</li>"
    resp += f"<li>{get_forecast(weather_data['daily'][1])}</li>"
    resp += f"<li>{get_forecast(weather_data['daily'][2])}</li>"
    resp += f"<li>{get_forecast(weather_data['daily'][3])}</li>"
    resp += "</ul>"
    await bot.message(room.room_id, resp, p_html=True)
