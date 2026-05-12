#!/usr/bin/env python3
"""
Weight Email Processor
Parses daily weight from email body, stores for Vitus health agent
"""

import imaplib
import email
import json
import re
from pathlib import Path
from datetime import datetime
import pytz
from email.utils import parsedate_to_datetime

# Paths
DATA_DIR = Path.home() / ".openclaw" / "workspace" / "data"
WEIGHT_FILE = DATA_DIR / "weight-tracking" / "geoff-weights.json"
PROCESSED_FILE = DATA_DIR / ".processed-weight-ids.json"
CONFIG_PATH = Path.home() / ".openclaw" / "email_config.json"

# IMAP settings
IMAP_SERVER = "imap.gmail.com"
IMAP_PORT = 993
EMAIL_USER = "[REDACTED]"
PACIFIC_TZ = pytz.timezone('America/Los_Angeles')

def load_email_config():
    with open(CONFIG_PATH) as f:
        return json.load(f)

def load_processed_ids():
    if PROCESSED_FILE.exists():
        with open(PROCESSED_FILE) as f:
            data = json.load(f)
            return set(data.get('message_ids', []))
    return set()

def save_processed_ids(message_ids):
    PROCESSED_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(PROCESSED_FILE, 'w') as f:
        json.dump({
            'message_ids': list(message_ids),
            'last_updated': datetime.now().isoformat()
        }, f, indent=2)

def extract_weight_from_email(msg):
    """Extract weight from email body"""
    # Get email date
    email_date = None
    try:
        date_str = msg.get('Date')
        if date_str:
            email_date = parsedate_to_datetime(date_str)
            if email_date.tzinfo is None:
                email_date = pytz.utc.localize(email_date)
            email_date = email_date.astimezone(PACIFIC_TZ)
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
    
    # Parse weight - look for number (allowing decimal)
    # Try to find a number that looks like a weight (100-500 lbs)
    lines = body.strip().split('\n')
    for line in lines:
        line = line.strip()
        # Try to extract number
        match = re.search(r'(\d+\.?\d*)', line)
        if match:
            try:
                weight = float(match.group(1))
                # Validate reasonable weight range
                if 100 <= weight <= 500:
                    if email_date:
                        date_str = email_date.strftime('%Y-%m-%d')
                    else:
                        date_str = datetime.now(PACIFIC_TZ).strftime('%Y-%m-%d')
                    
                    return {
                        'date': date_str,
                        'weight': weight,
                        'email_sent': email_date.isoformat() if email_date else None
                    }
            except:
                continue
    
    return None

def load_existing_weights():
    """Load existing weight data"""
    if WEIGHT_FILE.exists():
        with open(WEIGHT_FILE) as f:
            data = json.load(f)
            # Handle both old format (list) and new format (dict with weights key)
            if isinstance(data, list):
                return {
                    'weights': data,
                    'goal': {'target': 222.0, 'start': 247.9, 'start_date': '2026-01-31'},
                    'metadata': {'last_updated': None}
                }
            elif isinstance(data, dict):
                if 'weights' not in data:
                    data['weights'] = []
                if 'goal' not in data:
                    data['goal'] = {'target': 222.0, 'start': 247.9, 'start_date': '2026-01-31'}
                if 'metadata' not in data:
                    data['metadata'] = {'last_updated': None}
                return data
    return {
        'weights': [],
        'goal': {'target': 222.0, 'start': 247.9, 'start_date': '2026-01-31'},
        'metadata': {'last_updated': None}
    }

def save_weights(data):
    """Save weight data"""
    WEIGHT_FILE.parent.mkdir(parents=True, exist_ok=True)
    
    # Update metadata
    data['metadata']['last_updated'] = datetime.now().isoformat()
    
    # Sort by date
    data['weights'] = sorted(data['weights'], key=lambda x: x['date'])
    
    with open(WEIGHT_FILE, 'w') as f:
        json.dump(data, f, indent=2)

def process_weight_emails():
    """Main function"""
    print("=" * 60)
    print("Weight Email Processor")
    print("=" * 60)
    print()
    
    config = load_email_config()
    processed_ids = load_processed_ids()
    
    mail = imaplib.IMAP4_SSL(IMAP_SERVER, IMAP_PORT)
    mail.login(EMAIL_USER, config['app_password'])
    mail.select("inbox")
    
    # Load existing data
    weight_data = load_existing_weights()
    
    # Create lookup by date
    weight_by_date = {w['date']: w for w in weight_data['weights']}
    
    new_messages = 0
    
    # Search for weight emails
    # Look for emails with "weight" in subject from your email
    status, messages = mail.search(None, '(FROM "gclapp@mac.com" SUBJECT "weight")')
    
    if status != "OK" or not messages[0]:
        # Try without subject filter
        status, messages = mail.search(None, '(FROM "gclapp@mac.com")')
    
    if status == "OK" and messages[0]:
        msg_ids = messages[0].split()
        print(f"Found {len(msg_ids)} emails from gclapp@mac.com")
        
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
            
            subject = msg['Subject'] or ''
            
            # Check if this looks like a weight email
            # Either subject contains "weight" or body contains a weight-like number
            is_weight_email = 'weight' in subject.lower()
            
            weight_entry = extract_weight_from_email(msg)
            
            if weight_entry:
                is_weight_email = True
                date = weight_entry['date']
                weight = weight_entry['weight']
                
                # Overwrite or add
                if date in weight_by_date:
                    old_weight = weight_by_date[date]['weight']
                    weight_by_date[date]['weight'] = weight
                    weight_by_date[date]['updated'] = datetime.now().isoformat()
                    print(f"  ✓ Updated {date}: {old_weight} → {weight} lbs")
                else:
                    weight_by_date[date] = weight_entry
                    print(f"  ✓ Added {date}: {weight} lbs")
                
                new_messages += 1
                processed_ids.add(msg_id_str)
    
    mail.logout()
    
    # Save data
    if new_messages > 0:
        weight_data['weights'] = list(weight_by_date.values())
        save_weights(weight_data)
        
        print()
        print("=" * 60)
        print(f"✅ Processed {new_messages} weight emails")
        print(f"✅ Total weight entries: {len(weight_data['weights'])}")
        print("=" * 60)
        
        # Update MEMORY.md with latest weight
        update_memory_with_weight(weight_data)
    else:
        print("No new weight emails found")
    
    return new_messages

def update_memory_with_weight(weight_data):
    """Update MEMORY.md with latest weight for Vitus"""
    if not weight_data['weights']:
        return
    
    latest = weight_data['weights'][-1]
    print(f"\n📊 Latest weight: {latest['weight']} lbs on {latest['date']}")
    print("Vitus will use this for goal setting and coaching.")

if __name__ == "__main__":
    process_weight_emails()
