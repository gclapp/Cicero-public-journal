#!/usr/bin/env python3
"""
Weight Loss Tracker
Logs daily weigh-ins, calculates trends, provides weekly summaries
Integrates with Whoop data for holistic health tracking
"""

import json
import os
from pathlib import Path
from datetime import datetime, timedelta
import statistics

DATA_FILE = Path.home() / ".openclaw" / "workspace" / "data" / "weight-loss" / "tracker.json"

def ensure_data_file():
    """Ensure tracker data file exists"""
    DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
    if not DATA_FILE.exists():
        with open(DATA_FILE, 'w') as f:
            json.dump({
                'start_date': '2026-02-28',
                'start_weight': None,
                'goal_weight': None,
                'goal_lbs': 20,
                'timeline_weeks': 12,
                'entries': [],
                'measurements': []
            }, f, indent=2)

def load_data():
    """Load weight loss data"""
    ensure_data_file()
    with open(DATA_FILE, 'r') as f:
        return json.load(f)

def save_data(data):
    """Save weight loss data"""
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=2)

def log_weight(weight_lbs, notes=""):
    """Log a daily weigh-in"""
    data = load_data()
    
    entry = {
        'date': datetime.now().strftime('%Y-%m-%d'),
        'weight_lbs': weight_lbs,
        'timestamp': datetime.now().isoformat(),
        'notes': notes
    }
    
    # Check if entry for today already exists
    today = datetime.now().strftime('%Y-%m-%d')
    data['entries'] = [e for e in data['entries'] if e['date'] != today]
    data['entries'].append(entry)
    
    # Sort by date
    data['entries'].sort(key=lambda x: x['date'])
    
    save_data(data)
    print(f"✅ Logged: {weight_lbs} lbs on {today}")
    
    # Show progress
    show_progress()

def log_measurements(waist_inches=None, chest=None, hips=None, notes=""):
    """Log body measurements"""
    data = load_data()
    
    measurement = {
        'date': datetime.now().strftime('%Y-%m-%d'),
        'waist_inches': waist_inches,
        'chest_inches': chest,
        'hips_inches': hips,
        'notes': notes
    }
    
    data['measurements'].append(measurement)
    save_data(data)
    print(f"✅ Measurements logged for {measurement['date']}")

def calculate_trend(weights, days=7):
    """Calculate weight trend using moving average"""
    if len(weights) < 2:
        return None, None
    
    recent = weights[-days:] if len(weights) >= days else weights
    avg = statistics.mean([w['weight_lbs'] for w in recent])
    
    # Calculate weekly rate
    if len(weights) >= 7:
        week_ago = weights[-7]['weight_lbs'] if len(weights) >= 7 else weights[0]['weight_lbs']
        current = weights[-1]['weight_lbs']
        weekly_rate = current - week_ago
    else:
        weekly_rate = None
    
    return avg, weekly_rate

def show_progress():
    """Show current progress summary"""
    data = load_data()
    entries = data['entries']
    
    if not entries:
        print("\n📊 No weigh-ins yet. Start by logging your weight!")
        print("Usage: python3 weight_loss_tracker.py log 185.5")
        return
    
    print("\n" + "="*60)
    print("📊 WEIGHT LOSS PROGRESS")
    print("="*60)
    
    # Current stats
    current = entries[-1]['weight_lbs']
    start = entries[0]['weight_lbs'] if data.get('start_weight') is None else data['start_weight']
    
    print(f"\n🎯 Goal: Lose {data['goal_lbs']} lbs in {data['timeline_weeks']} weeks")
    print(f"📅 Start: {data['start_date']}")
    
    if start:
        total_lost = start - current
        progress_pct = (total_lost / data['goal_lbs']) * 100 if data['goal_lbs'] > 0 else 0
        remaining = data['goal_lbs'] - total_lost
        
        print(f"\n⚖️  Weight:")
        print(f"   Start: {start} lbs")
        print(f"   Current: {current} lbs")
        print(f"   Lost: {total_lost:.1f} lbs ({progress_pct:.1f}% of goal)")
        print(f"   Remaining: {remaining:.1f} lbs")
    else:
        print(f"\n⚖️  Current: {current} lbs")
    
    # Trend
    if len(entries) >= 2:
        avg, weekly_rate = calculate_trend(entries)
        if avg:
            print(f"\n📈 7-Day Average: {avg:.1f} lbs")
        if weekly_rate is not None:
            direction = "↓ Losing" if weekly_rate < 0 else "↑ Gaining" if weekly_rate > 0 else "→ Stable"
            print(f"   Weekly Rate: {direction} {abs(weekly_rate):.1f} lbs/week")
            
            # Project completion
            if weekly_rate < 0 and remaining > 0:
                weeks_to_goal = remaining / abs(weekly_rate)
                target_date = datetime.now() + timedelta(weeks=weeks_to_goal)
                print(f"   ⏱️  Projected goal date: {target_date.strftime('%B %d, %Y')} ({weeks_to_goal:.1f} weeks)")
    
    # Recent entries
    print(f"\n📝 Recent Weigh-ins:")
    for entry in entries[-5:]:
        print(f"   {entry['date']}: {entry['weight_lbs']} lbs")
    
    print("\n" + "="*60)

def weekly_report():
    """Generate weekly summary report"""
    data = load_data()
    entries = data['entries']
    
    if len(entries) < 2:
        print("Not enough data for weekly report yet.")
        return
    
    # Get last 7 days
    week_ago = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
    week_entries = [e for e in entries if e['date'] >= week_ago]
    
    if len(week_entries) < 2:
        print("Need more data from this week for report.")
        return
    
    start_of_week = week_entries[0]['weight_lbs']
    end_of_week = week_entries[-1]['weight_lbs']
    change = end_of_week - start_of_week
    
    print("\n" + "="*60)
    print("📈 WEEKLY REPORT")
    print("="*60)
    print(f"\nWeek of: {week_entries[0]['date']} to {week_entries[-1]['date']}")
    print(f"Weight Change: {change:+.1f} lbs")
    
    if change < 0:
        print("✅ On track! Keep it up.")
    elif change > 0:
        print("⚠️  Weight up this week. Let's review the plan.")
    else:
        print("→ Stable this week. Small adjustments may help.")
    
    # Calculate average
    weights = [e['weight_lbs'] for e in week_entries]
    avg = statistics.mean(weights)
    print(f"\nWeekly Average: {avg:.1f} lbs")
    print(f"Weigh-ins: {len(week_entries)} days")
    
    print("\n" + "="*60)

def main():
    """Main function with CLI"""
    import sys
    
    if len(sys.argv) < 2:
        show_progress()
        return
    
    command = sys.argv[1]
    
    if command == "log" and len(sys.argv) >= 3:
        try:
            weight = float(sys.argv[2])
            notes = " ".join(sys.argv[3:]) if len(sys.argv) > 3 else ""
            log_weight(weight, notes)
        except ValueError:
            print("❌ Invalid weight. Usage: python3 weight_loss_tracker.py log 185.5")
    
    elif command == "measure" and len(sys.argv) >= 3:
        try:
            waist = float(sys.argv[2])
            notes = " ".join(sys.argv[3:]) if len(sys.argv) > 3 else ""
            log_measurements(waist_inches=waist, notes=notes)
        except ValueError:
            print("❌ Invalid measurement. Usage: python3 weight_loss_tracker.py measure 36")
    
    elif command == "weekly":
        weekly_report()
    
    elif command == "init" and len(sys.argv) >= 4:
        # Initialize with start weight and goal
        data = load_data()
        data['start_weight'] = float(sys.argv[2])
        data['goal_lbs'] = float(sys.argv[3])
        save_data(data)
        print(f"✅ Initialized: Start {sys.argv[2]} lbs, Goal {sys.argv[3]} lbs loss")
    
    else:
        print("Usage:")
        print("  python3 weight_loss_tracker.py           # Show progress")
        print("  python3 weight_loss_tracker.py log 185.5 # Log weight")
        print("  python3 weight_loss_tracker.py measure 36 # Log waist")
        print("  python3 weight_loss_tracker.py weekly    # Weekly report")
        print("  python3 weight_loss_tracker.py init 205 20 # Set start & goal")

if __name__ == "__main__":
    main()
