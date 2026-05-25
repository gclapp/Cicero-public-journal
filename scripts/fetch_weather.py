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
    """Fetch weather from wttr.in with precipitation forecast"""
    config = load_config()
    
    try:
        city = config.get('city', 'Los Angeles').replace(' ', '+')
        url = f"https://wttr.in/{city}?format=j1"
        
        req = urllib.request.Request(url, headers={'User-Agent': 'curl/7.68.0'})
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode())
        
        current = data['current_condition'][0]
        
        # Get today's hourly forecast for rain prediction
        hourly_forecast = data['weather'][0]['hourly'] if 'weather' in data and data['weather'] else []
        
        # Find chance of rain and when rain starts
        rain_info = analyze_rain_forecast(hourly_forecast)
        
        weather_data = {
            'city': config.get('city', 'Los Angeles'),
            'temp_f': int(current['temp_F']),
            'temp_c': int(current['temp_C']),
            'condition': current['weatherDesc'][0]['value'],
            'humidity': current['humidity'],
            'wind_mph': current['windspeedMiles'],
            'feels_like_f': int(current['FeelsLikeF']),
            'chance_of_rain': rain_info['chance_of_rain'],
            'rain_start_time': rain_info['rain_start_time'],
            'hourly_forecast': hourly_forecast[:12],  # Store next 12 hours
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


def analyze_rain_forecast(hourly_forecast):
    """Analyze hourly forecast to find chance of rain and when it starts"""
    if not hourly_forecast:
        return {'chance_of_rain': 0, 'rain_start_time': None}
    
    max_rain_chance = 0
    rain_start_time = None
    
    for hour in hourly_forecast:
        try:
            rain_chance = int(hour.get('chanceofrain', 0))
            if rain_chance > max_rain_chance:
                max_rain_chance = rain_chance
            
            # Find when rain starts (first hour with > 30% chance)
            if rain_chance > 30 and rain_start_time is None:
                time_val = hour.get('time', '0')
                # Convert time format (e.g., "900" -> "9:00 AM")
                hour_int = int(time_val) // 100
                ampm = "AM" if hour_int < 12 else "PM"
                display_hour = hour_int if hour_int <= 12 else hour_int - 12
                if display_hour == 0:
                    display_hour = 12
                rain_start_time = f"{display_hour}:00 {ampm}"
        except (ValueError, TypeError):
            continue
    
    return {
        'chance_of_rain': max_rain_chance,
        'rain_start_time': rain_start_time
    }

def get_weather_summary():
    """Get formatted weather summary for check-ins with precipitation info"""
    if not DATA_FILE.exists():
        fetch_weather()
    
    try:
        with open(DATA_FILE) as f:
            data = json.load(f)
        
        condition_lower = data['condition'].lower()
        if "sun" in condition_lower:
            emoji = "☀️"
        elif "cloud" in condition_lower:
            emoji = "☁️"
        elif "rain" in condition_lower or "drizzle" in condition_lower or "shower" in condition_lower:
            emoji = "🌧️"
        elif "snow" in condition_lower:
            emoji = "❄️"
        elif "fog" in condition_lower or "mist" in condition_lower:
            emoji = "🌫️"
        else:
            emoji = "🌤️"
        
        summary = f"🌤️ **Weather: {data['city']}**\n"
        summary += f"{emoji} {data['condition']}, {data['temp_f']}°F (feels like {data['feels_like_f']}°F)\n"
        summary += f"💨 Wind: {data['wind_mph']} mph | 💧 Humidity: {data['humidity']}%\n"
        
        # Add precipitation info
        chance_of_rain = data.get('chance_of_rain', 0)
        rain_start = data.get('rain_start_time')
        
        if chance_of_rain > 0:
            if rain_start:
                summary += f"🌧️ Rain: {chance_of_rain}% chance, starting around {rain_start}\n"
            else:
                summary += f"🌧️ Rain: {chance_of_rain}% chance today\n"
        else:
            summary += f"☀️ No rain expected today\n"
        
        return summary
    except Exception as e:
        return f"🌤️ **Weather:** Data unavailable ({str(e)})\n"


def get_weather_html():
    """Get HTML formatted weather section with precipitation info"""
    if not DATA_FILE.exists():
        fetch_weather()
    
    try:
        with open(DATA_FILE) as f:
            data = json.load(f)
        
        condition_lower = data['condition'].lower()
        if "sun" in condition_lower:
            emoji = "☀️"
        elif "cloud" in condition_lower:
            emoji = "☁️"
        elif "rain" in condition_lower or "drizzle" in condition_lower or "shower" in condition_lower:
            emoji = "🌧️"
        elif "snow" in condition_lower:
            emoji = "❄️"
        elif "fog" in condition_lower or "mist" in condition_lower:
            emoji = "🌫️"
        else:
            emoji = "🌤️"
        
        chance_of_rain = data.get('chance_of_rain', 0)
        rain_start = data.get('rain_start_time')
        
        # Build precipitation line
        if chance_of_rain > 0:
            if rain_start:
                precip_line = f"🌧️ <strong>Rain:</strong> {chance_of_rain}% chance, starting around {rain_start}"
                precip_color = "#dc3545" if chance_of_rain > 70 else "#fd7e14" if chance_of_rain > 40 else "#6c757d"
            else:
                precip_line = f"🌧️ <strong>Rain:</strong> {chance_of_rain}% chance today"
                precip_color = "#6c757d"
        else:
            precip_line = "☀️ <strong>No rain expected today</strong>"
            precip_color = "#28a745"
        
        html = f"""<h3>🌤️ Weather: {data['city']}</h3>
<div style="background: #f8f9fa; padding: 15px; border-radius: 8px; margin: 10px 0;">
    <div style="font-size: 18px; margin-bottom: 10px;">{emoji} <strong>{data['condition']}</strong>, {data['temp_f']}°F (feels like {data['feels_like_f']}°F)</div>
    <div style="color: #666; margin-bottom: 8px;">💨 Wind: {data['wind_mph']} mph | 💧 Humidity: {data['humidity']}%</div>
    <div style="color: {precip_color}; font-size: 14px;">{precip_line}</div>
</div>"""
        
        return html
    except Exception as e:
        return f"<h3>🌤️ Weather</h3><p>Data unavailable</p>"

if __name__ == "__main__":
    print("Fetching weather...")
    weather = fetch_weather()
    if weather:
        print(f"\n✅ Weather for {weather['city']}: {weather['condition']}, {weather['temp_f']}°F")
        print("\nWeather summary for check-in:")
        print(get_weather_summary())
    else:
        print("❌ Failed to fetch weather")
