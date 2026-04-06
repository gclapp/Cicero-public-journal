#!/usr/bin/env python3
"""
Health Export Parser
Parses iPhone Health export emails for check-in integration
"""

import re
import json
from datetime import datetime
from pathlib import Path

def parse_health_export_email(body, subject=None):
    """
    Parse iPhone Health export email
    
    Expected format:
    Health Export - Monday, April 6, 2026
    
    Steps: 8,432 steps
    Water: 64 oz
    Sleep: 7.2 hours
    
    Data from Apple Health
    """
    data = {
        'date': None,
        'steps': None,
        'water_oz': None,
        'sleep_hours': None,
        'source': 'Apple Health',
        'parsed_at': datetime.now().isoformat()
    }
    
    # Extract date from subject or body
    if subject:
        date_match = re.search(r'Health Export - (.+)$', subject)
        if date_match:
            data['date'] = date_match.group(1).strip()
    
    if not data['date']:
        # Try to parse from body
        date_match = re.search(r'Health Export - (.+?)\n', body)
        if date_match:
            data['date'] = date_match.group(1).strip()
    
    # Extract steps
    steps_match = re.search(r'Steps:\s*([\d,]+)\s*steps?', body, re.IGNORECASE)
    if steps_match:
        data['steps'] = int(steps_match.group(1).replace(',', ''))
    
    # Extract water
    water_match = re.search(r'Water:\s*([\d.]+)\s*oz', body, re.IGNORECASE)
    if water_match:
        data['water_oz'] = float(water_match.group(1))
    
    # Extract sleep
    sleep_match = re.search(r'Sleep:\s*([\d.]+)\s*hours?', body, re.IGNORECASE)
    if sleep_match:
        data['sleep_hours'] = float(sleep_match.group(1))
    
    return data

def format_for_checkin(health_data):
    """Format health data for morning check-in"""
    lines = ["📱 Health (Apple)"]
    
    if health_data.get('steps'):
        lines.append(f"• Steps: {health_data['steps']:,}")
    
    if health_data.get('water_oz'):
        lines.append(f"• Water: {health_data['water_oz']:.0f} oz")
    
    if health_data.get('sleep_hours'):
        lines.append(f"• Sleep: {health_data['sleep_hours']:.1f} hrs")
    
    return "\n".join(lines)

def save_health_data(health_data):
    """Save health data for check-in integration"""
    health_file = Path.home() / ".openclaw" / "workspace" / "data" / "latest-health-export.json"
    
    health_file.parent.mkdir(parents=True, exist_ok=True)
    with open(health_file, 'w') as f:
        json.dump(health_data, f, indent=2)
    
    return True

def is_health_export_email(subject, body):
    """Check if email is iPhone Health export"""
    return 'Health Export' in subject or 'Health Export' in body

if __name__ == "__main__":
    # Test
    test_body = """Health Export - Monday, April 6, 2026

Steps: 8,432 steps
Water: 64 oz
Sleep: 7.2 hours

Data from Apple Health"""
    
    data = parse_health_export_email(test_body, "Health Export - Monday, April 6, 2026")
    print("Parsed:", data)
    print("\nFormatted:")
    print(format_for_checkin(data))