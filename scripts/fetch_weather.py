#!/usr/bin/env python3
"""
fetch_weather.py - Fetch weather for current location
Uses OpenWeatherMap API (free tier: 1000 calls/day)
"""

import json
import urllib.request
from pathlib import Path
from datetime import datetime

DATA_FILE = Path.home() / ".openclaw" / "workspace" / "data" / "weather-data.json"
CONFIG_FILE = Path.home() / ".openclaw" / "config" / "weather-config.json"

# Default to Los Angeles if no config
DEFAULT_LOCATION = {
    "city": "Los Angeles",
    "lat": 34.0522,
    "lon": -118.2437,
    "units": "imperial"  # Fahrenheit
}

def load_config():
    """Load weather configuration"""
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE) as f:
            return json.load(f)
    return DEFAULT_LOCATION

def fetch_weather():
    """Fetch weather from OpenWeatherMap"""
    config = load_config()
    
    # For now, using a simple approach without API key
    # In production, you'd use: api.openweathermap.org with API key
    # For demo, using wttr.in (free, no API key needed)
    
    try:
        city = config.get('city', 'Los Angeles').replace(' ', '+')
        url = f"https://wttr.in/{city}?format=j1"
        
        req = urllib.request.Request(url, headers={'User-Agent': 'curl/7.68.0'})
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode())
        
        current = data['current_condition'][0]
        
        weather_data = {
            'city': config.get('city', 'Los Angeles'),
            'temp_f': int(current['temp_F']),
            'temp_c': int(current['temp_C']),
            'condition': current['weatherDesc'][0]['value'],
            'humidity': current['humidity'],
            'wind_mph': current['windspeedMiles'],
            'feels_like_f': int(current['FeelsLikeF']),
            'timestamp': datetime.now().isoformat()
        }
        
        # Save to file
        DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(DATA_FILE, 'w') as f:
            json.dump(weather_data, f, indent=2)
        
        return weather_data
        
    except Exception as e:
        print(f"Error fetching weather: {e}")
        return None

def get_weather_summary():
    """Get formatted weather summary for check-ins"""
    if not DATA_FILE.exists():
        fetch_weather()
    
    try:
        with open(DATA_FILE) as f:
            data = json.load(f)
        
        emoji = "☀️" if "sun" in data['condition'].lower() else "☁️" if "cloud" in data['condition'].lower() else "🌧️" if "rain" in data['condition'].lower() else "🌤️"
        
        summary = f"🌤️ **Weather: {data['city']}**\n"
        summary += f"{emoji} {data['condition']}, {data['temp_f']}°F (feels like {data['feels_like_f']}°F)\n"
        summary += f"💨 Wind: {data['wind_mph']} mph | 💧 Humidity: {data['humidity']}%\n"
        
        return summary
    except:
        return "🌤️ **Weather:** Data unavailable\n"

if __name__ == "__main__":
    print("Fetching weather...")
    weather = fetch_weather()
    if weather:
        print(f"\n✅ Weather for {weather['city']}: {weather['condition']}, {weather['temp_f']}°F")
        print("\nWeather summary for check-in:")
        print(get_weather_summary())
    else:
        print("❌ Failed to fetch weather")
