#!/usr/bin/env python3
"""
comprehensive_morning_update.py - Generate complete morning check-in with all data
Properly formatted HTML for email, clean text for Telegram
"""

import json
from pathlib import Path
from datetime import datetime
import sys

sys.path.insert(0, '/home/ubuntu/.openclaw/workspace/scripts')

def generate_comprehensive_morning_update():
    """Generate morning update with all data sources"""
    
    # Get current time in PT
    from datetime import datetime
    import pytz
    pt = pytz.timezone('America/Los_Angeles')
    pt_now = datetime.now(pt)
    
    # Fetch fresh data
    try:
        from fetch_stock_data import get_stock_summary
        stock_summary = get_stock_summary()
    except:
        stock_summary = "📈 **Markets:** Data unavailable\n"
    
    try:
        from fetch_weather import get_weather_summary
        weather_summary = get_weather_summary()
    except:
        weather_summary = "🌤️ **Weather:** Data unavailable\n"
    
    # Fetch Todoist tasks
    try:
        from fetch_todoist_tasks import get_todoist_summary, get_todoist_html
        todoist_summary = get_todoist_summary()
        todoist_html = get_todoist_html()
    except:
        todoist_summary = "📋 **Tasks:** Todoist data unavailable\n"
        todoist_html = "<h3>📋 Today's Tasks</h3><p>Todoist data unavailable</p>"
    
    # Calendar data
    calendar_file = Path("/home/ubuntu/.openclaw/workspace/config/calendar-events.json")
    calendar_html = "<h3>📅 Today's Calendar</h3><ul>"
    calendar_text = "📅 **Today's Calendar**\n"
    
    location = "Los Angeles"  # Default
    
    if calendar_file.exists():
        try:
            with open(calendar_file) as f:
                events = json.load(f)
            if events and len(events) > 0:
                for event in events[:5]:
                    summary = event.get('summary', 'Event')
                    calendar_html += f"<li>{summary}</li>"
                    calendar_text += f"• {summary}\n"
                    if event.get('location'):
                        location = event.get('location')
            else:
                calendar_html += "<li>No events scheduled</li>"
                calendar_text += "No events scheduled\n"
        except:
            calendar_html += "<li>Calendar data unavailable</li>"
            calendar_text += "Calendar data unavailable\n"
    else:
        calendar_html += "<li>Calendar data unavailable</li>"
        calendar_text += "Calendar data unavailable\n"
    
    calendar_html += "</ul>"
    
    # Whoop data
    whoop_file = Path("/home/ubuntu/.openclaw/workspace/data/whoop/latest-summary.txt")
    whoop_html = "<h3>💪 Health (Whoop)</h3><pre style='background:#f0f0f0;padding:10px;border-radius:5px;'>"
    whoop_text = "💪 **Health (Whoop)**\n"
    
    if whoop_file.exists():
        try:
            with open(whoop_file) as f:
                whoop_data = f.read()
            whoop_html += whoop_data.replace('\n', '<br>') + "</pre>"
            whoop_text += whoop_data + "\n"
        except:
            whoop_html += "Data unavailable</pre>"
            whoop_text += "Data unavailable\n"
    else:
        whoop_html += "Data unavailable</pre>"
        whoop_text += "Data unavailable\n"
    
    # Stock data (convert markdown to HTML)
    stock_html = "<h3>📈 Markets</h3><pre style='background:#f0f0f0;padding:10px;border-radius:5px;'>"
    stock_html += stock_summary.replace('\n', '<br>') + "</pre>"
    stock_text = stock_summary + "\n"
    
    # Weather data
    weather_html = "<h3>🌤️ Weather</h3><pre style='background:#f0f0f0;padding:10px;border-radius:5px;'>"
    weather_html += weather_summary.replace('\n', '<br>') + "</pre>"
    weather_text = weather_summary + "\n"
    
    # Location
    location_html = f"<h3>📍 Location</h3><p>{location}</p>"
    location_text = f"📍 **Location:** {location}\n"
    
    # System TODO List
    todo_file = Path("/home/ubuntu/.openclaw/workspace/TODO.md")
    todo_html = ""
    todo_text = ""
    
    if todo_file.exists():
        try:
            with open(todo_file) as f:
                todo_content = f.read()
            
            # Extract critical items (lines with 🔴)
            critical_lines = [line for line in todo_content.split('\n') if '🔴' in line or '###' in line]
            
            if critical_lines:
                todo_html = "<h3>🔧 System Status</h3><ul style='font-size: 13px; color: #666;'>"
                todo_text = "\n🔧 **System Status**\n"
                
                for line in critical_lines[:5]:  # Top 5 items
                    clean_line = line.strip().replace('🔴', '❌').replace('###', '•')
                    if clean_line and len(clean_line) > 5:
                        todo_html += f"<li>{clean_line}</li>"
                        todo_text += f"{clean_line}\n"
                
                todo_html += "</ul>"
                todo_text += "\n"
        except:
            pass
    
    # Determine if this is the first email of the day (before noon PT)
    is_first_email = pt_now.hour < 12
    
    # Build HTML email - NEW ORDER:
    # 1. Location (at top)
    # 2. Calendar (first section)
    # 3. Markets (in every email)
    # 4. Weather (only in first email)
    # 5. TODO list
    # 6. Health data (at bottom)
    
    weather_section_html = weather_html if is_first_email else ""
    weather_section_text = weather_text if is_first_email else ""
    
    html_email = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px; background: #f5f5f5; }}
        .container {{ background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        .header {{ border-bottom: 3px solid #4a90d9; padding-bottom: 15px; margin-bottom: 25px; }}
        .header h1 {{ margin: 0; color: #4a90d9; font-size: 28px; }}
        .header p {{ margin: 5px 0 0 0; color: #666; font-size: 16px; }}
        .location-bar {{ background: #e8f4f8; padding: 12px 15px; border-radius: 8px; margin-bottom: 20px; font-size: 15px; color: #333; border-left: 4px solid #4a90d9; }}
        h3 {{ color: #333; margin-top: 25px; margin-bottom: 10px; font-size: 18px; border-left: 4px solid #4a90d9; padding-left: 10px; }}
        ul {{ margin: 10px 0; padding-left: 20px; }}
        li {{ margin: 5px 0; }}
        pre {{ font-family: 'Monaco', 'Menlo', monospace; font-size: 14px; overflow-x: auto; }}
        .health-section {{ background: #f0f8f0; padding: 15px; border-radius: 8px; margin-top: 25px; border-left: 4px solid #28a745; }}
        .question {{ background: #e8f4f8; padding: 15px; border-radius: 8px; margin-top: 25px; }}
        .footer {{ margin-top: 30px; padding-top: 20px; border-top: 2px solid #eee; font-size: 14px; color: #666; text-align: center; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🌅 Morning Check-In</h1>
            <p>{pt_now.strftime('%A, %B %d, %Y')}</p>
        </div>
        
        <div class="location-bar">
            📍 <strong>Location:</strong> {location}
        </div>
        
        <p style="font-size: 16px; color: #555;">Good morning! Here's your day ahead:</p>
        
        {calendar_html}
        
        {todoist_html}
        
        {stock_html}
        
        {weather_section_html}
        
        {todo_html}
        
        <div class="health-section">
            {whoop_html}
        </div>
        
        <div class="question">
            <h3>What's your focus for today?</h3>
        </div>
        
        <div class="footer">
            <p>—<br><strong>Cicero 🏛️</strong></p>
            <p style="font-size: 12px; color: #999;">To respond, message me on Telegram: @geoffclapp</p>
        </div>
    </div>
</body>
</html>"""
    
    # Build Telegram text - NEW ORDER
    telegram_text = f"""🌅 **Morning Check-In** — {pt_now.strftime('%A, %B %d')}

📍 **Location:** {location}

Good morning! Here's your day ahead:

{calendar_text}
{todoist_summary}
{stock_text}
{weather_section_text}{todo_text}
💪 **Health Data (Whoop)**
{whoop_text}
What's your focus for today?

—
🏛️ Cicero"""
    
    return {
        'html': html_email,
        'text': telegram_text,
        'subject': f"Cicero Check-In: Morning — {pt_now.strftime('%A, %B %d')}"
    }

if __name__ == "__main__":
    update = generate_comprehensive_morning_update()
    print("HTML Email Preview (first 500 chars):")
    print(update['html'][:500])
    print("\n" + "="*50)
    print("\nTelegram Text:")
    print(update['text'])
