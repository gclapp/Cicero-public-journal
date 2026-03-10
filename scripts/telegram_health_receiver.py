#!/usr/bin/env python3
"""
Telegram Health Data Receiver
Receives weight and steps data via Telegram messages from iPhone Shortcuts
"""

import json
import re
from datetime import datetime
from pathlib import Path

# Storage file for health data
HEALTH_DATA_FILE = Path.home() / ".openclaw" / "workspace" / "data" / "health-data.json"

def parse_health_message(text):
    """Parse health data from Telegram message"""
    data = {
        "weight": None,
        "steps": None,
        "date": None,
        "timestamp": datetime.now().isoformat()
    }
    
    # Extract weight
    weight_match = re.search(r'WEIGHT[:\s]+(\d+\.?\d*)', text, re.IGNORECASE)
    if weight_match:
        data["weight"] = float(weight_match.group(1))
    
    # Extract steps
    steps_match = re.search(r'STEPS[:\s]+(\d+)', text, re.IGNORECASE)
    if steps_match:
        data["steps"] = int(steps_match.group(1))
    
    # Extract date
    date_match = re.search(r'DATE[:\s]+(\d{4}-\d{2}-\d{2})', text, re.IGNORECASE)
    if date_match:
        data["date"] = date_match.group(1)
    else:
        data["date"] = datetime.now().strftime('%Y-%m-%d')
    
    return data if (data["weight"] or data["steps"]) else None

def store_health_data(data):
    """Store health data to JSON file"""
    HEALTH_DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
    
    # Load existing data
    all_data = []
    if HEALTH_DATA_FILE.exists():
        with open(HEALTH_DATA_FILE, 'r') as f:
            all_data = json.load(f)
    
    # Add new entry
    all_data.append(data)
    
    # Save
    with open(HEALTH_DATA_FILE, 'w') as f:
        json.dump(all_data, f, indent=2)
    
    return len(all_data)

def process_health_message(message_text):
    """Main entry point for processing health messages"""
    data = parse_health_message(message_text)
    
    if not data:
        return None, "Could not parse health data from message"
    
    count = store_health_data(data)
    
    response = f"✅ Health data recorded!\n"
    if data["weight"]:
        response += f"📊 Weight: {data['weight']} lbs\n"
    if data["steps"]:
        response += f"👟 Steps: {data['steps']:,}\n"
    response += f"📅 Date: {data['date']}\n"
    response += f"💾 Total entries: {count}"
    
    return data, response

if __name__ == "__main__":
    # Test
    test_msg = """WEIGHT: 238.5
STEPS: 8432
DATE: 2026-03-08"""
    
    data, response = process_health_message(test_msg)
    print(response)
