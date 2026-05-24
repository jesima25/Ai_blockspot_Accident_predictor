# weather_api.py
# Purpose: Fetch live weather for any city

import requests

API_KEY = "df4526fcfb3fc2669d35ff1d7d0d0a30"

def get_weather(city):
    """Fetch live weather from OpenWeatherMap"""
    try:
        url = f"https://api.openweathermap.org/data/2.5/weather?q={city},IN&appid={API_KEY}&units=metric"
        res  = requests.get(url, timeout=5)
        data = res.json()

        if data.get('cod') != 200:
            return None

        weather_main = data['weather'][0]['main'].lower()
        visibility   = data.get('visibility', 10000)
        temp         = data['main']['temp']
        description  = data['weather'][0]['description']

        # Map to our model values
        if 'rain' in weather_main or 'drizzle' in weather_main:
            weather = 'rain'
        elif 'fog' in weather_main or 'mist' in weather_main or 'haze' in weather_main:
            weather = 'fog'
        else:
            weather = 'clear'

        # Visibility mapping
        if visibility < 1000:
            vis = 'low'
        elif visibility < 5000:
            vis = 'medium'
        else:
            vis = 'high'

        return {
            "weather"    : weather,
            "visibility" : vis,
            "temp"       : round(temp, 1),
            "description": description.title(),
            "city"       : data['name'],
            "country"    : data['sys']['country']
        }

    except Exception as e:
        print(f"Weather API error: {e}")
        return None