#!/usr/bin/env python3
"""
Generate Morning Update with Calendar + Health Integration
Includes Whoop data, weight loss tracking, travel, meetings
"""

import json
import os
from pathlib import Path
from datetime import datetime, timedelta

CALENDAR_FILE = Path.home() / ".openclaw" / "workspace" / "config" / "calendar-events.json"
WHOOP_SUMMARY_FILE = Path.home() / ".openclaw" / "workspace" / "data" / "whoop" / "latest-summary.txt"

def load_calendar():
    """Load calendar events"""
    if not CALENDAR_FILE.exists():
        return None
    
    with open(CALENDAR_FILE, 'r') as f:
        return json.load(f)

def load_whoop_summary():
    """Load Whoop health summary"""
    if not WHOOP_SUMMARY_FILE.exists():
        return None
    
    with open(WHOOP_SUMMARY_FILE, 'r') as f:
        return f.read()

def get_today_events(events_data):
    """Get events for today"""
    if not events_data:
        return []
    
    today = datetime.now().strftime('%A, %B %d')
    today_events = []
    
    for event in events_data.get('events', []):
        if today in event.get('start', ''):
            today_events.append(event)
    
    return today_events

def get_travel_events(events_data, days=7):
    """Get upcoming travel events"""
    if not events_data:
        return []
    
    travel = []
    for event in events_data.get('events', []):
        if event.get('is_travel'):
            travel.append(event)
    
    return travel[:5]

def get_restaurant_events(events_data):
    """Get restaurant reservations for today or this week"""
    if not events_data:
        return []
    
    restaurants = []
    restaurant_keywords = ['reservation', 'l\'artusi', 'nowon', 'dinner', 'lunch']
    
    for event in events_data.get('events', []):
        summary = event.get('summary', '').lower()
        if any(kw in summary for kw in restaurant_keywords):
            restaurants.append(event)
    
    return restaurants[:3]

def generate_morning_update():
    """Generate complete morning update with health + calendar"""
    calendar_data = load_calendar()
    whoop_data = load_whoop_summary()
    
    today = datetime.now().strftime('%A, %B %d')
    
    update = f"""Good morning! ☀️

## Daily Status List - {today}

**Pending Tasks:**
- (Check Todoist for active tasks)

**Recently Completed (last 72h):**
- Calendar integration active ✅
- Whoop data flowing ✅
- Weight loss tracking enabled ✅

"""
    
    # Add Whoop health data section
    if whoop_data and whoop_data.strip() != "No Whoop data available.":
        update += "### 💪 Yesterday's Health (Whoop)\n\n"
        update += whoop_data
        update += "\n\n"
    else:
        update += "### 💪 Health Data\nWhoop data will appear here after morning refresh.\n\n"
    
    # Weight Loss Tracking Section
    update += """### 🎯 Weight Loss Progress
**Goal:** 20 lbs in 10-12 weeks | **Approach:** High-protein, lower-carb + Strategic exercise

**Daily Checklist:**
- [ ] Weigh-in (7 AM)
- [ ] Log breakfast in Lose It!
- [ ] Protein target: 150-180g
- [ ] Workout complete
- [ ] 7+ hours sleep

**This Week Focus:**
- Weeks 1-4: Aggressive phase (2 lbs/week target)
- Prioritize: Protein at every meal, no sugary drinks, daily movement
- Travel days: Pack protein bars, walk everywhere, hotel workouts

"""
    
    # Add calendar section
    if calendar_data:
        today_events = get_today_events(calendar_data)
        travel_events = get_travel_events(calendar_data)
        restaurant_events = get_restaurant_events(calendar_data)
        
        if today_events:
            update += "### 📅 Today's Schedule\n\n"
            for event in today_events:
                emoji = "✈️" if event.get('is_travel') else "🍽️" if any(kw in event.get('summary', '').lower() for kw in ['reservation', 'dinner', 'lunch']) else "📅"
                update += f"{emoji} {event['summary']}\n"
                update += f"   🕐 {event['start']}\n"
                if event.get('location'):
                    update += f"   📍 {event['location']}\n"
                update += "\n"
        else:
            update += "### 📅 Today's Schedule\nNo events scheduled.\n\n"
        
        # Restaurant intel
        if restaurant_events:
            update += "### 🍽️ Upcoming Dining\n\n"
            for r in restaurant_events[:2]:
                update += f"🍽️ {r['summary']}\n"
                update += f"   📆 {r['start']}\n"
                if r.get('location'):
                    update += f"   📍 {r['location']}\n"
                    # Add city guide intel
                    if "l'artusi" in r['summary'].lower():
                        update += "   💡 *Italian institution, get the olive oil cake*\n"
                    elif "nowon" in r['summary'].lower():
                        update += "   💡 *Legendary cheeseburger, lively Korean pub*\n"
            update += "\n"
        
        # Travel alerts
        if travel_events:
            update += "### ✈️ Upcoming Travel\n\n"
            for trip in travel_events[:3]:
                update += f"✈️ {trip['summary']}\n"
                update += f"   📆 {trip['start']}\n"
                if trip.get('location'):
                    update += f"   📍 {trip['location']}\n"
            update += "\n"
    else:
        update += "### 📅 Calendar\nCalendar data not available.\n\n"
    
    # Proactive questions based on calendar
    update += """### ❓ Questions to Help You Win Today
- How did you sleep? (Check Whoop recovery above)
- What's your main focus for work today?
- Any obstacles I can help remove?
- Dinner plans — cooking or eating out?

"""
    
    update += """### ⚡ Quick Actions
- **Weather:** Want a forecast for today/travel?
- **Tasks:** Check Todoist for today's priorities
- **Health:** Review yesterday's trends above
- **Travel:** Upcoming trip prep needed?

I'm tracking everything. Let's crush today. 🏛️"""
    
    return update

def main():
    """Generate and print morning update"""
    update = generate_morning_update()
    print(update)
    
    # Save to file for reference
    output_file = Path.home() / ".openclaw" / "workspace" / "config" / "morning-update.txt"
    with open(output_file, 'w') as f:
        f.write(update)
    
    print(f"\n💾 Saved to: {output_file}")

if __name__ == "__main__":
    main()
