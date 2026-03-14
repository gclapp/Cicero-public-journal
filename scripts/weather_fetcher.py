#!/usr/bin/env python3
"""
Weather Fetcher with Multiple Backups
Tries multiple weather APIs in order of preference
"""

import subprocess
import json
import sys
from pathlib import Path

# City coordinates for Open-Meteo
CITY_COORDS = {
    'los angeles': {'lat': 34.0522, 'lon': -118.2437},
    'new york': {'lat': 40.7128, 'lon': -74.0060},
    'san francisco': {'lat': 37.7749, 'lon': -122.4194},
    'chicago': {'lat': 41.8781, 'lon': -87.6298},
    'miami': {'lat': 25.7617, 'lon': -80.1918},
    'london': {'lat': 51.5074, 'lon': -0.1278},
    'paris': {'lat': 48.8566, 'lon': 2.3522},
    'tokyo': {'lat': 35.6762, 'lon': 139.6503},
    'sydney': {'lat': -33.8688, 'lon': 151.2093},
    'portland': {'lat': 45.5152, 'lon': -122.6784},
    'scottsdale': {'lat': 33.4942, 'lon': -111.9261},
}

def get_wttrin_weather(city):
    """Try wttr.in for weather"""
    try:
        city_encoded = city.replace(' ', '+')
        result = subprocess.run(
            ['curl', '-s', f'wttr.in/{city_encoded}?format=%l:+%c+%t+%h+%w', '--max-time', '10'],
            capture_output=True,
            text=True,
            timeout=15
        )
        if result.returncode == 0 and result.stdout and 'Unknown' not in result.stdout:
            return result.stdout.strip()
        return None
    except Exception as e:
        return None

def get_openmeteo_weather(city):
    """Try Open-Meteo as fallback"""
    try:
        city_lower = city.lower()
        coords = CITY_COORDS.get(city_lower)
        
        if not coords:
            # Try to geocode with a simple API
            return None
        
        url = f"https://api.open-meteo.com/v1/forecast?latitude={coords['lat']}&longitude={coords['lon']}&current_weather=true&temperature_unit=fahrenheit&windspeed_unit=mph"
        
        result = subprocess.run(
            ['curl', '-s', url, '--max-time', '10'],
            capture_output=True,
            text=True,
            timeout=15
        )
        
        if result.returncode == 0:
            data = json.loads(result.stdout)
            weather = data.get('current_weather', {})
            temp = weather.get('temperature', 'N/A')
            wind = weather.get('windspeed', 'N/A')
            code = weather.get('weathercode', 0)
            
            # Map weather code to emoji
            weather_emojis = {
                0: '☀️', 1: '🌤️', 2: '⛅', 3: '☁️',
                45: '🌫️', 48: '🌫️',
                51: '🌧️', 53: '🌧️', 55: '🌧️',
                61: '🌧️', 63: '🌧️', 65: '🌧️',
                71: '🌨️', 73: '🌨️', 75: '🌨️',
                95: '⛈️', 96: '⛈️', 99: '⛈️'
            }
            emoji = weather_emojis.get(code, '🌡️')
            
            return f"{city.title()}: {emoji} {temp}°F 💨 {wind}mph"
        return None
    except Exception as e:
        return None

def get_weatherapi_weather(city):
    """Try weatherapi.com (no key needed for basic)"""
    try:
        city_encoded = city.replace(' ', '%20')
        # This is a demo endpoint - may not always work
        url = f"http://api.weatherapi.com/v1/current.json?key=demo&q={city_encoded}&aqi=no"
        
        result = subprocess.run(
            ['curl', '-s', url, '--max-time', '10'],
            capture_output=True,
            text=True,
            timeout=15
        )
        
        if result.returncode == 0:
            data = json.loads(result.stdout)
            if 'current' in data:
                current = data['current']
                temp_f = current.get('temp_f', 'N/A')
                condition = current.get('condition', {}).get('text', '')
                humidity = current.get('humidity', 'N/A')
                wind = current.get('wind_mph', 'N/A')
                
                return f"{city.title()}: {condition} {temp_f}°F 💧 {humidity}% 💨 {wind}mph"
        return None
    except Exception as e:
        return None

def get_weather(city):
    """Get weather with fallback chain"""
    city = city.strip()
    
    # Try primary source
    weather = get_wttrin_weather(city)
    if weather:
        return weather
    
    # Try Open-Meteo
    weather = get_openmeteo_weather(city)
    if weather:
        return weather
    
    # Try weatherapi
    weather = get_weatherapi_weather(city)
    if weather:
        return weather
    
    return f"❌ Weather unavailable for {city}"

if __name__ == "__main__":
    if len(sys.argv) > 1:
        city = ' '.join(sys.argv[1:])
    else:
        city = "Los Angeles"
    
    print(get_weather(city))
