#!/usr/bin/env python3
"""
Weekly Memory Consolidation Script
Consolidates daily logs into weekly summaries and updates long-term memory
"""

import os
import re
import json
from datetime import datetime, timedelta
from pathlib import Path
from collections import defaultdict

# Configuration
MEMORY_DIR = Path.home() / ".openclaw" / "workspace" / "memory"
DAILY_LOG_PATTERN = r"(\d{4})-(\d{2})-(\d{2})\.md"

def get_week_number(date):
    """Get ISO week number for a date"""
    return date.isocalendar()[1]

def get_week_start(date):
    """Get the Monday of the week for a given date"""
    return date - timedelta(days=date.weekday())

def parse_daily_log(filepath):
    """Parse a daily log file and extract key information"""
    with open(filepath, 'r') as f:
        content = f.read()
    
    # Extract date from filename
    filename = filepath.name
    match = re.match(DAILY_LOG_PATTERN, filename)
    if not match:
        return None
    
    year, month, day = match.groups()
    date = datetime(int(year), int(month), int(day))
    
    # Extract key sections
    lines = content.split('\n')
    
    summary = {
        'date': date.strftime('%Y-%m-%d'),
        'day_of_week': date.strftime('%A'),
        'events': [],
        'decisions': [],
        'people_mentioned': [],
        'places_visited': [],
        'tasks_completed': [],
        'tasks_pending': [],
        'key_facts': [],
        'raw_content': content
    }
    
    # Parse content for key information
    current_section = None
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        # Detect sections
        if line.startswith('# '):
            current_section = 'header'
        elif '**Location:**' in line or '**Day:**' in line:
            summary['places_visited'].append(line.split(':**')[-1].strip())
        elif '✅' in line or '**Completed:**' in line:
            task = line.replace('✅', '').replace('**Completed:**', '').strip()
            if task:
                summary['tasks_completed'].append(task)
        elif '⏳' in line or '**Pending:**' in line:
            task = line.replace('⏳', '').replace('**Pending:**', '').strip()
            if task:
                summary['tasks_pending'].append(task)
        elif any(name in line for name in ['Grace', 'Adam', 'Christie', 'Lisa', 'David', 'Steven', 'Pete', 'Tanisha']):
            # Extract people mentioned
            for name in ['Grace', 'Adam Dole', 'Christie', 'Lisa Suennen', 'David Sobol', 'Steven Leist', 'Pete', 'Tanisha']:
                if name in line and name not in summary['people_mentioned']:
                    summary['people_mentioned'].append(name)
        elif any(word in line.lower() for word in ['decided', 'chose', 'selected', 'agreed', 'plan', 'schedule']):
            if len(line) > 10:  # Not just a header
                summary['decisions'].append(line)
        elif any(word in line.lower() for word in ['met', 'saw', 'visited', 'dinner', 'lunch', 'breakfast']):
            if len(line) > 10:
                summary['events'].append(line)
    
    return summary

def generate_weekly_summary(week_start, daily_summaries):
    """Generate a weekly summary from daily logs"""
    week_number = get_week_number(week_start)
    year = week_start.year
    
    # Aggregate data
    all_people = set()
    all_places = set()
    all_tasks_completed = []
    all_tasks_pending = []
    all_decisions = []
    all_events = []
    
    for summary in daily_summaries:
        all_people.update(summary['people_mentioned'])
        all_places.update(summary['places_visited'])
        all_tasks_completed.extend(summary['tasks_completed'])
        all_tasks_pending.extend(summary['tasks_pending'])
        all_decisions.extend(summary['decisions'])
        all_events.extend(summary['events'])
    
    # Count mentions
    people_counts = defaultdict(int)
    place_counts = defaultdict(int)
    
    for summary in daily_summaries:
        for person in summary['people_mentioned']:
            people_counts[person] += 1
        for place in summary['places_visited']:
            place_counts[place] += 1
    
    # Generate insights
    insights = []
    
    # Pattern: Frequent contacts
    top_people = sorted(people_counts.items(), key=lambda x: x[1], reverse=True)[:3]
    if top_people:
        insights.append(f"Most contact: {', '.join([p[0] for p in top_people])}")
    
    # Pattern: Travel
    if all_places:
        insights.append(f"Locations: {len(all_places)} different places")
    
    # Pattern: Productivity
    completed = len(all_tasks_completed)
    pending = len(all_tasks_pending)
    if completed > 0:
        insights.append(f"Tasks: {completed} completed, {pending} pending")
    
    # Pattern: Weight loss tracking
    weight_mentions = [s for s in daily_summaries if 'food' in s['raw_content'].lower() or 'weight' in s['raw_content'].lower()]
    if weight_mentions:
        insights.append(f"Weight loss tracking: {len(weight_mentions)} days logged")
    
    # Generate summary markdown
    summary_content = f"""# Week {week_number}, {year} Summary
## {week_start.strftime('%B %d')} - {(week_start + timedelta(days=6)).strftime('%B %d')}

### 🎯 Week at a Glance

**Days Logged:** {len(daily_summaries)}

**Key Insights:**
{chr(10).join(['- ' + insight for insight in insights]) if insights else '- No major patterns detected'}

### 👥 People This Week

**Most Contacted:**
{chr(10).join([f'- {person} ({count} mentions)' for person, count in sorted(people_counts.items(), key=lambda x: x[1], reverse=True)]) if people_counts else '- No people mentioned'}

**All Contacts:**
{', '.join(sorted(all_people)) if all_people else 'None recorded'}

### 📍 Places & Travel

{chr(10).join([f'- {place}' for place in sorted(all_places)]) if all_places else '- No locations recorded'}

### ✅ Completed This Week

{chr(10).join([f'- {task}' for task in all_tasks_completed[:10]]) if all_tasks_completed else '- No tasks recorded'}

### ⏳ Carrying Forward

{chr(10).join([f'- {task}' for task in all_tasks_pending[:5]]) if all_tasks_pending else '- No pending tasks'}

### 🎯 Key Decisions

{chr(10).join([f'- {decision[:100]}...' if len(decision) > 100 else f'- {decision}' for decision in all_decisions[:5]]) if all_decisions else '- No major decisions recorded'}

### 📊 Patterns & Trends

**Daily Consistency:**
- Days with activity: {len(daily_summaries)}/7
- Most active day: {max(daily_summaries, key=lambda x: len(x['events']))['day_of_week'] if daily_summaries and any(s['events'] for s in daily_summaries) else 'N/A'}

**To-Do Velocity:**
- Completion rate: {len(all_tasks_completed)}/{len(all_tasks_completed) + len(all_tasks_pending)} ({round(len(all_tasks_completed) / (len(all_tasks_completed) + len(all_tasks_pending)) * 100) if (len(all_tasks_completed) + len(all_tasks_pending)) > 0 else 0}%)

### 🔗 Source Files

This summary consolidates:
{chr(10).join([f'- [{summary["date"]}]({summary["date"]}.md) - {summary["day_of_week"]}' for summary in daily_summaries])}

### 📝 Raw Notes

<details>
<summary>View daily details (click to expand)</summary>

{chr(10).join([f'**{summary["day_of_week"]} {summary["date"]}:**' + chr(10) + summary['raw_content'][:500] + '...' + chr(10) for summary in daily_summaries])}

</details>

---

*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*  
*Next consolidation: {(week_start + timedelta(days=7)).strftime('%Y-%m-%d')}*
"""
    
    return summary_content, week_number, year

def update_long_term_memory(daily_summaries):
    """Update long-term memory files with distilled learnings"""
    updates = []
    
    # Extract key facts that should go to MEMORY.md or USER.md
    for summary in daily_summaries:
        content = summary['raw_content'].lower()
        
        # Check for important updates
        if 'new system' in content or 'built' in content:
            updates.append(f"Week of {summary['date']}: Built new system/created automation")
        
        if 'friend' in content and 'profile' in content:
            updates.append(f"Week of {summary['date']}: Added friend profiles to database")
        
        if 'weight' in content or 'food' in content or 'lose it' in content:
            updates.append(f"Week of {summary['date']}: Continued weight loss tracking")
    
    return updates

def main():
    """Main consolidation function"""
    print("🔍 Weekly Memory Consolidation")
    print("=" * 50)
    
    # Find all daily log files
    daily_logs = []
    for file in MEMORY_DIR.glob("*.md"):
        match = re.match(DAILY_LOG_PATTERN, file.name)
        if match:
            daily_logs.append(file)
    
    if not daily_logs:
        print("❌ No daily log files found")
        return
    
    print(f"📁 Found {len(daily_logs)} daily log files")
    
    # Group by week
    weeks = defaultdict(list)
    for log_file in daily_logs:
        summary = parse_daily_log(log_file)
        if summary:
            date = datetime.strptime(summary['date'], '%Y-%m-%d')
            week_start = get_week_start(date)
            weeks[week_start].append(summary)
    
    print(f"📅 Organized into {len(weeks)} weeks")
    
    # Process each week
    for week_start, daily_summaries in sorted(weeks.items()):
        # Skip current week (incomplete)
        if week_start >= get_week_start(datetime.now()):
            print(f"⏭️  Skipping current week (incomplete): {week_start.strftime('%Y-%m-%d')}")
            continue
        
        # Sort by date
        daily_summaries.sort(key=lambda x: x['date'])
        
        print(f"\n📝 Processing week of {week_start.strftime('%Y-%m-%d')} ({len(daily_summaries)} days)")
        
        # Generate summary
        summary_content, week_number, year = generate_weekly_summary(week_start, daily_summaries)
        
        # Write weekly summary file
        output_file = MEMORY_DIR / f"{year}-Week-{week_number:02d}.md"
        with open(output_file, 'w') as f:
            f.write(summary_content)
        
        print(f"✅ Created: {output_file.name}")
        
        # Update long-term memory
        updates = update_long_term_memory(daily_summaries)
        if updates:
            print(f"🧠 Key learnings to add to long-term memory:")
            for update in updates:
                print(f"   - {update}")
    
    print("\n" + "=" * 50)
    print("✨ Consolidation complete!")
    print(f"📊 Generated {len(weeks)} weekly summaries")
    print(f"💾 All summaries saved to: {MEMORY_DIR}")

if __name__ == "__main__":
    main()