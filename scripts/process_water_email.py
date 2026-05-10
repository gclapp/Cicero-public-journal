#!/usr/bin/env python3
"""
Process Apple Health water data emails from gclapp@mac.com
Extracts 10-day water intake history and stores for Vitus health coaching
"""

import imaplib
import email
import json
from pathlib import Path
from datetime import datetime, timedelta
from email.utils import parsedate_to_datetime
import re

# Paths
DATA_DIR = Path.home() / ".openclaw" / "workspace" / "data"
WATER_DATA_FILE = DATA_DIR / "water-intake-history.json"
CONFIG_PATH = Path.home() / ".openclaw" / "email_config.json"

# IMAP settings
IMAP_SERVER = "imap.gmail.com"
IMAP_PORT = 993
EMAIL_USER = "[REDACTED]"

def load_email_config():
    with open(CONFIG_PATH, 'r') as f:
        return json.load(f)

def extract_water_data(msg):
    """
    Extract water intake data from email attachments.
    Files are ordered: first = oldest (10 days ago), last = today
    Filename = water amount in ounces
    
    Based on Geoff's data:
    - 48 oz = Apr 30 (index 1 in example)
    - 72 oz = May 2 (index 3)
    - 11.9 oz = May 3 (index 4)
    """
    water_readings = []
    
    if not msg.is_multipart():
        return water_readings
    
    # Collect all .txt attachments with their water amounts
    attachments = []
    for part in msg.walk():
        filename = part.get_filename()
        if filename and filename.endswith('.txt'):
            try:
                content = part.get_payload(decode=True).decode('utf-8').strip()
                # Filename IS the water amount (e.g., "48.txt" = 48 oz)
                ounces = float(filename.replace('.txt', ''))
                attachments.append(ounces)
            except:
                pass
    
    # Files are in chronological order: index 0 = oldest, index -1 = today
    # So if we have 11 files: index 0 = 10 days ago, index 10 = today
    today = datetime.now()
    num_attachments = len(attachments)
    
    for i, ounces in enumerate(attachments):
        # i=0 is 10 days ago, i=10 is today (if 11 files)
        days_ago = num_attachments - 1 - i
        date = (today - timedelta(days=days_ago)).strftime('%Y-%m-%d')
        
        water_readings.append({
            'date': date,
            'ounces': ounces,
            'liters': round(ounces * 0.0295735, 2),
            'cups': round(ounces / 8, 1),
            'days_ago': days_ago
        })
    
    return water_readings

def load_existing_data():
    """Load existing water data or create new structure"""
    if WATER_DATA_FILE.exists():
        with open(WATER_DATA_FILE, 'r') as f:
            return json.load(f)
    return {
        'daily_records': {},
        'metadata': {
            'last_updated': None,
            'total_days_tracked': 0,
            'average_daily_oz': 0,
            'emails_processed': 0
        }
    }

def save_water_data(data):
    """Save water data to JSON file"""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    
    # Calculate metadata
    daily_records = data['daily_records']
    if daily_records:
        # Only count non-zero days for average
        non_zero_days = [day['ounces'] for day in daily_records.values() if day['ounces'] > 0]
        total_oz = sum(non_zero_days)
        data['metadata']['total_days_tracked'] = len(daily_records)
        data['metadata']['average_daily_oz'] = round(total_oz / len(non_zero_days), 1) if non_zero_days else 0
        data['metadata']['last_updated'] = datetime.now().isoformat()
    
    with open(WATER_DATA_FILE, 'w') as f:
        json.dump(data, f, indent=2)

def process_water_emails():
    """Main function to check and process water update emails"""
    config = load_email_config()
    app_password = config['app_password']
    
    mail = imaplib.IMAP4_SSL(IMAP_SERVER, IMAP_PORT)
    mail.login(EMAIL_USER, app_password)
    mail.select("inbox")
    
    # Search for unread water emails from gclapp@mac.com
    status, messages = mail.search(None, '(UNSEEN FROM "gclapp@mac.com" SUBJECT "Water Update")')
    
    if status != "OK" or not messages[0]:
        print("No new water update emails found")
        mail.logout()
        return None
    
    msg_ids = messages[0].split()
    print(f"Found {len(msg_ids)} new water update email(s)")
    
    data = load_existing_data()
    new_readings_count = 0
    updated_dates = []
    
    for msg_id in msg_ids:
        status, msg_data = mail.fetch(msg_id, '(RFC822)')
        if status != "OK":
            continue
        
        raw_email = msg_data[0][1]
        msg = email.message_from_bytes(raw_email)
        
        # Get email date for reference
        email_date = parsedate_to_datetime(msg.get('Date', ''))
        
        # Extract water readings
        readings = extract_water_data(msg)
        
        for reading in readings:
            date_key = reading['date']
            existing = data['daily_records'].get(date_key, {})
            existing_oz = existing.get('ounces', 0)
            new_oz = reading['ounces']
            
            # RULE: Always update with new data from Apple Health
            # Apple Health data updates slowly - latest email has most accurate values
            # Update if:
            # 1. Date doesn't exist yet, OR
            # 2. New value is different from existing (including corrections/updates)
            should_update = False
            
            if date_key not in data['daily_records']:
                should_update = True
            elif existing_oz != new_oz:
                should_update = True
                if existing_oz == 0:
                    updated_dates.append(f"{date_key}: {existing_oz} → {new_oz} oz (filled)")
                else:
                    updated_dates.append(f"{date_key}: {existing_oz} → {new_oz} oz (updated)")
            
            if should_update:
                data['daily_records'][date_key] = reading
                new_readings_count += 1
        
        data['metadata']['emails_processed'] = data['metadata'].get('emails_processed', 0) + 1
        print(f"  Processed email {msg_id.decode()}: {len(readings)} days of data")
    
    save_water_data(data)
    mail.logout()
    
    return {
        'emails_processed': len(msg_ids),
        'new_readings': new_readings_count,
        'updated_dates': updated_dates,
        'total_days': len(data['daily_records']),
        'average_oz': data['metadata']['average_daily_oz']
    }

def get_recent_water_summary(days=7):
    """Get summary of recent water intake for Vitus coaching"""
    data = load_existing_data()
    
    summary = []
    today = datetime.now()
    
    for i in range(days):
        date_key = (today - timedelta(days=i)).strftime('%Y-%m-%d')
        if date_key in data['daily_records']:
            record = data['daily_records'][date_key]
            summary.append({
                'date': date_key,
                'ounces': record['ounces'],
                'liters': record['liters'],
                'cups': record['cups']
            })
        else:
            summary.append({
                'date': date_key,
                'ounces': 0,
                'liters': 0,
                'cups': 0,
                'missing': True
            })
    
    return summary

def get_hydration_status():
    """Get current hydration status for coaching insights"""
    recent = get_recent_water_summary(7)
    
    # Count days with actual data (not missing, not zero)
    valid_days = [day for day in recent if not day.get('missing') and day['ounces'] > 0]
    
    if not valid_days:
        return {'status': 'no_data', 'message': 'No water data available'}
    
    total_oz = sum(day['ounces'] for day in valid_days)
    avg_oz = total_oz / len(valid_days)
    
    # Hydration targets
    target_oz = 80  # ~10 cups / 2.4L recommended
    
    if avg_oz >= target_oz:
        status = 'excellent'
        message = f"Great hydration! Averaging {avg_oz:.0f} oz/day"
    elif avg_oz >= target_oz * 0.75:
        status = 'good'
        message = f"Good hydration. Averaging {avg_oz:.0f} oz/day (target: {target_oz} oz)"
    elif avg_oz >= target_oz * 0.5:
        status = 'needs_improvement'
        message = f"Below target. Averaging {avg_oz:.0f} oz/day (target: {target_oz} oz)"
    else:
        status = 'poor'
        message = f"Low hydration. Averaging {avg_oz:.0f} oz/day (target: {target_oz} oz)"
    
    return {
        'status': status,
        'message': message,
        'average_oz': round(avg_oz, 1),
        'target_oz': target_oz,
        'percent_of_target': round((avg_oz / target_oz) * 100, 1),
        'recent_days': recent,
        'days_logged': len(valid_days),
        'days_total': len(recent)
    }

def print_water_report():
    """Print a formatted water intake report"""
    data = load_existing_data()
    
    print("="*60)
    print("WATER INTAKE REPORT")
    print("="*60)
    
    # Sort by date
    sorted_dates = sorted(data['daily_records'].keys(), reverse=True)
    
    print(f"\nTotal days tracked: {len(sorted_dates)}")
    print(f"Last updated: {data['metadata'].get('last_updated', 'Never')}")
    print(f"Emails processed: {data['metadata'].get('emails_processed', 0)}")
    print()
    
    for date_key in sorted_dates[:14]:  # Last 14 days
        record = data['daily_records'][date_key]
        oz = record['ounces']
        bar = '█' * int(oz / 5)  # 1 char per 5 oz
        status = '✅' if oz >= 80 else '⚠️' if oz >= 40 else '🔴' if oz > 0 else '❓'
        print(f"{date_key} {status} {oz:>6.1f} oz {bar}")
    
    print()
    status = get_hydration_status()
    print(f"7-Day Average: {status['average_oz']} oz/day")
    print(f"Target: {status['target_oz']} oz/day ({status['percent_of_target']}%)")
    print(f"Status: {status['message']}")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == 'report':
        print_water_report()
    else:
        result = process_water_emails()
        if result:
            print(f"\n✅ Processed {result['emails_processed']} email(s)")
            print(f"   New/updated readings: {result['new_readings']}")
            if result.get('updated_dates'):
                print(f"   Updated dates: {', '.join(result['updated_dates'])}")
            print(f"   Total days tracked: {result['total_days']}")
            print(f"   Historical average: {result['average_oz']} oz/day")
            
            # Show current status
            status = get_hydration_status()
            print(f"\n💧 Current Status: {status['message']}")
        else:
            print("No new water data to process")
