#!/usr/bin/env python3
"""
Health Email Processor v2 - Bulletproof
Processes ALL emails, tracks by Message-ID, overwrites with latest data
"""

import imaplib
import email
import json
import re
from pathlib import Path
from datetime import datetime, timedelta
import pytz
from email.utils import parsedate_to_datetime

# Paths
DATA_DIR = Path.home() / ".openclaw" / "workspace" / "data"
STEPS_FILE = DATA_DIR / "steps-history.json"
WATER_FILE = DATA_DIR / "water-intake.json"
PROCESSED_FILE = DATA_DIR / ".processed-message-ids.json"
CONFIG_PATH = Path.home() / ".openclaw" / "email_config.json"

# IMAP settings
IMAP_SERVER = "imap.gmail.com"
IMAP_PORT = 993
EMAIL_USER = "[REDACTED]"

# Settings
PACIFIC_TZ = pytz.timezone('America/Los_Angeles')
STEPS_TARGET = 10000

def load_email_config():
    with open(CONFIG_PATH) as f:
        return json.load(f)

def load_processed_ids():
    """Load set of processed message IDs"""
    if PROCESSED_FILE.exists():
        with open(PROCESSED_FILE) as f:
            data = json.load(f)
            return set(data.get('message_ids', []))
    return set()

def save_processed_ids(message_ids):
    """Save processed message IDs"""
    PROCESSED_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(PROCESSED_FILE, 'w') as f:
        json.dump({
            'message_ids': list(message_ids),
            'last_updated': datetime.now().isoformat()
        }, f, indent=2)

def extract_steps_from_attachments(msg):
    """Extract steps from .txt attachment filenames"""
    steps_data = {}
    
    if not msg.is_multipart():
        return steps_data
    
    # Get email sent date
    email_sent_date = None
    try:
        date_str = msg.get('Date')
        if date_str:
            email_sent_date = parsedate_to_datetime(date_str)
            if email_sent_date.tzinfo is None:
                email_sent_date = pytz.utc.localize(email_sent_date)
            email_sent_date = email_sent_date.astimezone(PACIFIC_TZ)
    except:
        pass
    
    # Collect attachments
    attachments = []
    for part in msg.walk():
        filename = part.get_filename()
        if filename and filename.endswith('.txt'):
            try:
                steps = float(filename.replace('.txt', ''))
                attachments.append(steps)
            except:
                pass
    
    if not attachments:
        return steps_data
    
    # Calculate dates (most recent = email sent date or today)
    if email_sent_date:
        today = email_sent_date
    else:
        today = datetime.now(pytz.utc).astimezone(PACIFIC_TZ)
    
    num_attachments = len(attachments)
    
    for i, steps in enumerate(attachments):
        days_ago = num_attachments - 1 - i
        date = (today - timedelta(days=days_ago)).strftime('%Y-%m-%d')
        
        steps_data[date] = {
            'date': date,
            'steps': int(steps),
            'miles': round(steps * 0.0005, 2),
            'calories': round(steps * 0.04, 0),
            'percent_of_goal': round((steps / STEPS_TARGET) * 100, 1),
            'email_sent': today.isoformat(),
            'source': 'attachment'
        }
    
    return steps_data

def extract_water_from_body(msg):
    """Extract water intake from email body"""
    water_data = {}
    
    # Get email sent date
    email_sent_date = None
    try:
        date_str = msg.get('Date')
        if date_str:
            email_sent_date = parsedate_to_datetime(date_str)
            if email_sent_date.tzinfo is None:
                email_sent_date = pytz.utc.localize(email_sent_date)
            email_sent_date = email_sent_date.astimezone(PACIFIC_TZ)
    except:
        pass
    
    # Get body
    body = ''
    if msg.is_multipart():
        for part in msg.walk():
            if part.get_content_type() == 'text/plain':
                try:
                    body = part.get_payload(decode=True).decode('utf-8')
                    break
                except:
                    pass
    else:
        try:
            body = msg.get_payload(decode=True).decode('utf-8')
        except:
            pass
    
    # Parse water amount
    try:
        water_oz = float(body.strip())
        if email_sent_date:
            date = email_sent_date.strftime('%Y-%m-%d')
            water_data[date] = {
                'date': date,
                'water_oz': water_oz,
                'email_sent': email_sent_date.isoformat()
            }
    except:
        pass
    
    return water_data

def load_existing_data(filepath):
    """Load existing data file"""
    if filepath.exists():
        with open(filepath) as f:
            return json.load(f)
    return {'daily_records': {}, 'metadata': {}}

def save_data(filepath, daily_records):
    """Save data with metadata"""
    filepath.parent.mkdir(parents=True, exist_ok=True)
    
    # Calculate metadata
    if daily_records:
        steps_values = [d['steps'] for d in daily_records.values() if 'steps' in d]
        avg_steps = int(sum(steps_values) / len(steps_values)) if steps_values else 0
    else:
        avg_steps = 0
    
    data = {
        'daily_records': daily_records,
        'metadata': {
            'last_updated': datetime.now().isoformat(),
            'total_days_tracked': len(daily_records),
            'average_daily_steps': avg_steps
        }
    }
    
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=2)

def process_health_emails():
    """Main function - processes all emails, overwrites with latest data"""
    print("=" * 60)
    print("Health Email Processor v2")
    print("=" * 60)
    print()
    
    config = load_email_config()
    processed_ids = load_processed_ids()
    
    mail = imaplib.IMAP4_SSL(IMAP_SERVER, IMAP_PORT)
    mail.login(EMAIL_USER, config['app_password'])
    mail.select("inbox")
    
    # Load existing data
    steps_data = load_existing_data(STEPS_FILE)
    water_data = load_existing_data(WATER_FILE)
    
    steps_records = steps_data.get('daily_records', {})
    water_records = water_data.get('daily_records', {})
    
    new_messages = 0
    
    # Process step emails (ALL of them, not just unread)
    print("Processing step emails...")
    status, messages = mail.search(None, '(FROM "gclapp@mac.com" SUBJECT "step")')
    
    if status == "OK" and messages[0]:
        msg_ids = messages[0].split()
        print(f"  Found {len(msg_ids)} step emails")
        
        for msg_id in msg_ids:
            msg_id_str = msg_id.decode()
            
            # Skip if already processed
            if msg_id_str in processed_ids:
                continue
            
            status, msg_data = mail.fetch(msg_id, '(RFC822)')
            if status != "OK":
                continue
            
            raw_email = msg_data[0][1]
            msg = email.message_from_bytes(raw_email)
            
            # Extract steps
            new_steps = extract_steps_from_attachments(msg)
            
            if new_steps:
                # Overwrite with new data
                steps_records.update(new_steps)
                new_messages += 1
                processed_ids.add(msg_id_str)
                print(f"  ✓ Processed {msg_id_str}: {len(new_steps)} days of step data")
    
    print()
    
    # Process water emails
    print("Processing water emails...")
    status, messages = mail.search(None, '(FROM "gclapp@mac.com" SUBJECT "water")')
    
    if status == "OK" and messages[0]:
        msg_ids = messages[0].split()
        print(f"  Found {len(msg_ids)} water emails")
        
        for msg_id in msg_ids:
            msg_id_str = msg_id.decode()
            
            # Skip if already processed
            if msg_id_str in processed_ids:
                continue
            
            status, msg_data = mail.fetch(msg_id, '(RFC822)')
            if status != "OK":
                continue
            
            raw_email = msg_data[0][1]
            msg = email.message_from_bytes(raw_email)
            
            # Extract water
            new_water = extract_water_from_body(msg)
            
            if new_water:
                # Overwrite with new data
                water_records.update(new_water)
                new_messages += 1
                processed_ids.add(msg_id_str)
                print(f"  ✓ Processed {msg_id_str}: {len(new_water)} water entries")
    
    mail.logout()
    
    # Save data
    if new_messages > 0:
        save_data(STEPS_FILE, steps_records)
        save_data(WATER_FILE, water_records)
        save_processed_ids(processed_ids)
        
        print()
        print("=" * 60)
        print(f"✅ Processed {new_messages} new messages")
        print(f"✅ Steps: {len(steps_records)} days total")
        print(f"✅ Water: {len(water_records)} days total")
        print(f"✅ Data saved")
        print("=" * 60)
    else:
        print()
        print("No new messages to process")
    
    return new_messages

if __name__ == "__main__":
    process_health_emails()
