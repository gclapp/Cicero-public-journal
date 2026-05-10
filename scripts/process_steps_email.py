#!/usr/bin/env python3
"""
Process Apple Health steps data emails from gclapp@mac.com
NEW FORMAT: Email body contains date:step pairs, one per line
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
STEPS_DATA_FILE = DATA_DIR / "steps-history.json"
CONFIG_PATH = Path.home() / ".openclaw" / "email_config.json"

# IMAP settings
IMAP_SERVER = "imap.gmail.com"
IMAP_PORT = 993
EMAIL_USER = "[REDACTED]"

# Daily step target
STEPS_TARGET = 10000

# Timezone - Always use Pacific (LA) time
PACIFIC_TZ = pytz.timezone('America/Los_Angeles')


def load_email_config():
    with open(CONFIG_PATH, 'r') as f:
        return json.load(f)


def extract_steps_from_email_body(msg):
    """
    Extract steps data from email body.
    Expected format:
    2026-04-26:11510
    2026-04-27:6783
    2026-04-28:6752
    """
    steps_data = []
    
    # Get email body
    body = ""
    if msg.is_multipart():
        for part in msg.walk():
            content_type = part.get_content_type()
            if content_type == "text/plain":
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
    
    if not body:
        return steps_data
    
    # Parse date:step lines
    # Pattern: YYYY-MM-DD:NUMBER
    pattern = r'(\d{4}-\d{2}-\d{2}):(\d+)'
    matches = re.findall(pattern, body)
    
    for date_str, steps_str in matches:
        try:
            steps = int(steps_str)
            # Validate date format
            datetime.strptime(date_str, '%Y-%m-%d')
            
            steps_data.append({
                'date': date_str,
                'steps': steps,
                'miles': round(steps * 0.0005, 2),
                'calories': round(steps * 0.04, 0),
                'percent_of_goal': round((steps / STEPS_TARGET) * 100, 1)
            })
        except ValueError:
            continue
    
    return steps_data


def extract_steps_from_attachments(msg):
    """
    LEGACY: Extract steps data from .txt attachment filenames.
    Only used as fallback if body parsing fails.
    """
    steps_data = []
    
    if not msg.is_multipart():
        return steps_data
    
    # Get email sent date for tracking (convert to Pacific time)
    email_sent_date = None
    try:
        date_str = msg.get('Date')
        if date_str:
            email_sent_date = parsedate_to_datetime(date_str)
            # Convert to Pacific time
            if email_sent_date.tzinfo is None:
                email_sent_date = pytz.utc.localize(email_sent_date)
            email_sent_date = email_sent_date.astimezone(PACIFIC_TZ)
    except:
        pass
    
    # Collect all .txt attachments with their step counts
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
    
    # Calculate dates for each attachment
    if email_sent_date:
        today = email_sent_date
    else:
        today = datetime.now(pytz.utc).astimezone(PACIFIC_TZ)
    
    num_attachments = len(attachments)
    
    for i, steps in enumerate(attachments):
        days_ago = num_attachments - 1 - i
        date = (today - timedelta(days=days_ago)).strftime('%Y-%m-%d')
        
        steps_data.append({
            'date': date,
            'steps': int(steps),
            'miles': round(steps * 0.0005, 2),
            'calories': round(steps * 0.04, 0),
            'percent_of_goal': round((steps / STEPS_TARGET) * 100, 1),
            'days_ago': days_ago,
            'email_sent': today.isoformat() if email_sent_date else None,
            'source': 'legacy_attachment'
        })
    
    return steps_data


def extract_steps_from_email(msg):
    """
    Extract steps data from email.
    Tries new body format first, falls back to legacy attachment format.
    """
    # Try new format first (body parsing)
    steps_data = extract_steps_from_email_body(msg)
    if steps_data:
        # Get email sent date for tracking
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
        
        # Add email_sent to each record
        for record in steps_data:
            record['email_sent'] = email_sent_date.isoformat() if email_sent_date else None
            record['source'] = 'body'
        
        return steps_data
    
    # Fall back to legacy attachment format
    return extract_steps_from_attachments(msg)


def load_existing_data():
    """Load existing steps data"""
    if STEPS_DATA_FILE.exists():
        with open(STEPS_DATA_FILE, 'r') as f:
            return json.load(f)
    return {
        'daily_records': {},
        'metadata': {
            'last_updated': None,
            'total_days_tracked': 0,
            'average_daily_steps': 0,
            'emails_processed': 0
        }
    }


def save_steps_data(data):
    """Save steps data to JSON file"""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    
    daily_records = data['daily_records']
    if daily_records:
        non_zero_days = [day['steps'] for day in daily_records.values() if day['steps'] > 0]
        total_steps = sum(non_zero_days)
        data['metadata']['total_days_tracked'] = len(daily_records)
        data['metadata']['average_daily_steps'] = int(total_steps / len(non_zero_days)) if non_zero_days else 0
        data['metadata']['last_updated'] = datetime.now().isoformat()
    
    with open(STEPS_DATA_FILE, 'w') as f:
        json.dump(data, f, indent=2)


def process_steps_emails():
    """Main function to process steps emails"""
    config = load_email_config()
    app_password = config['app_password']
    
    mail = imaplib.IMAP4_SSL(IMAP_SERVER, IMAP_PORT)
    mail.login(EMAIL_USER, app_password)
    mail.select("inbox")
    
    # Search for unread steps emails
    status, messages = mail.search(None, '(UNSEEN FROM "gclapp@mac.com" SUBJECT "step")')
    
    if status != "OK" or not messages[0]:
        print("No new steps emails found")
        mail.logout()
        return None
    
    msg_ids = messages[0].split()
    print(f"Found {len(msg_ids)} new steps email(s)")
    
    # Load existing data
    data = load_existing_data()
    
    # Track which emails we've processed and their sent dates
    emails_data = []
    
    for msg_id in msg_ids:
        status, msg_data = mail.fetch(msg_id, '(RFC822)')
        if status != "OK":
            continue
        
        raw_email = msg_data[0][1]
        msg = email.message_from_bytes(raw_email)
        
        # Get email sent date
        email_sent_date = None
        try:
            date_str = msg.get('Date')
            if date_str:
                email_sent_date = parsedate_to_datetime(date_str)
        except:
            pass
        
        # Extract steps from THIS email
        email_steps = extract_steps_from_email(msg)
        
        if email_steps:
            emails_data.append({
                'msg_id': msg_id.decode(),
                'sent_date': email_sent_date,
                'steps_data': email_steps
            })
            source = email_steps[0].get('source', 'unknown')
            print(f"  Email {msg_id.decode()}: {len(email_steps)} days of data, source={source}, sent {email_sent_date}")
    
    mail.logout()
    
    if not emails_data:
        print("No valid steps data found in emails")
        return None
    
    # Sort emails by sent date (most recent last)
    emails_data.sort(key=lambda x: x['sent_date'] if x['sent_date'] else datetime.min)
    
    # Process each email's data
    # For each date, we use the MOST RECENT email's value
    updates_made = []
    
    for email_info in emails_data:
        email_sent = email_info['sent_date']
        
        for day_data in email_info['steps_data']:
            date_key = day_data['date']
            new_steps = day_data['steps']
            
            existing = data['daily_records'].get(date_key, {})
            existing_steps = existing.get('steps', 0)
            existing_email_sent = existing.get('email_sent')
            
            # Check if we should update
            should_update = False
            
            if date_key not in data['daily_records']:
                # New date - add it
                should_update = True
                update_reason = "new date"
            elif existing_email_sent and email_sent:
                # Both have email sent dates - use most recent
                if email_sent > datetime.fromisoformat(existing_email_sent):
                    should_update = True
                    update_reason = f"newer email ({email_sent.strftime('%H:%M')} > {existing_email_sent[:16]})"
            elif new_steps != existing_steps:
                # No email sent date tracking, but value changed
                should_update = True
                update_reason = f"value changed ({existing_steps} → {new_steps})"
            
            if should_update:
                data['daily_records'][date_key] = day_data
                updates_made.append(f"{date_key}: {existing_steps} → {new_steps} steps ({update_reason})")
    
    # Update metadata
    data['metadata']['emails_processed'] = data['metadata'].get('emails_processed', 0) + len(emails_data)
    
    save_steps_data(data)
    
    return {
        'emails_processed': len(emails_data),
        'updates_made': len(updates_made),
        'update_details': updates_made[:10],  # First 10
        'total_days': len(data['daily_records']),
        'average_steps': data['metadata']['average_daily_steps']
    }


def get_recent_steps_summary(days=7):
    """Get summary of recent steps for Vitus coaching"""
    data = load_existing_data()
    
    summary = []
    today = datetime.now(PACIFIC_TZ)
    
    for i in range(days):
        date_key = (today - timedelta(days=i)).strftime('%Y-%m-%d')
        if date_key in data['daily_records']:
            record = data['daily_records'][date_key]
            summary.append({
                'date': date_key,
                'steps': record['steps'],
                'miles': record['miles'],
                'calories': record['calories'],
                'percent': record['percent_of_goal']
            })
        else:
            summary.append({
                'date': date_key,
                'steps': 0,
                'miles': 0,
                'calories': 0,
                'percent': 0,
                'missing': True
            })
    
    return summary


def get_steps_status():
    """Get current steps status for coaching insights"""
    recent = get_recent_steps_summary(7)
    
    valid_days = [day for day in recent if not day.get('missing') and day['steps'] > 0]
    
    if not valid_days:
        return {'status': 'no_data', 'message': 'No steps data available'}
    
    total_steps = sum(day['steps'] for day in valid_days)
    avg_steps = int(total_steps / len(valid_days))
    
    if avg_steps >= STEPS_TARGET:
        status = 'excellent'
        message = f"Crushing it! Averaging {avg_steps:,} steps/day"
    elif avg_steps >= STEPS_TARGET * 0.75:
        status = 'good'
        message = f"Good movement. Averaging {avg_steps:,} steps/day (target: {STEPS_TARGET:,})"
    elif avg_steps >= STEPS_TARGET * 0.5:
        status = 'needs_improvement'
        message = f"Below target. Averaging {avg_steps:,} steps/day (target: {STEPS_TARGET:,})"
    else:
        status = 'poor'
        message = f"Low activity. Averaging {avg_steps:,} steps/day (target: {STEPS_TARGET:,})"
    
    return {
        'status': status,
        'message': message,
        'average_steps': avg_steps,
        'target_steps': STEPS_TARGET,
        'percent_of_target': round((avg_steps / STEPS_TARGET) * 100, 1),
        'recent_days': recent,
        'days_logged': len(valid_days)
    }


def print_steps_report():
    """Print a formatted steps report"""
    data = load_existing_data()
    
    print("="*60)
    print("STEPS REPORT (Pacific Time)")
    print("="*60)
    
    sorted_dates = sorted(data['daily_records'].keys(), reverse=True)
    
    print(f"\nTotal days tracked: {len(sorted_dates)}")
    print(f"Last updated: {data['metadata'].get('last_updated', 'Never')}")
    print(f"Timezone: Pacific (Los Angeles)")
    print(f"Target: {STEPS_TARGET:,} steps/day")
    print()
    
    for date_key in sorted_dates[:14]:
        record = data['daily_records'][date_key]
        steps = record['steps']
        bar = '█' * int(steps / 500)
        status = '✅' if steps >= STEPS_TARGET else '⚠️' if steps >= STEPS_TARGET * 0.75 else '🔴' if steps > 0 else '❓'
        source = record.get('source', 'unknown')
        print(f"{date_key} {status} {steps:>6,} steps {bar}")
    
    print()
    status = get_steps_status()
    print(f"7-Day Average: {status['average_steps']:,} steps/day")
    print(f"Target: {STEPS_TARGET:,} steps/day ({status['percent_of_target']}%)")
    print(f"Status: {status['message']}")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == 'report':
        print_steps_report()
    else:
        result = process_steps_emails()
        if result:
            print(f"\n✅ Processed {result['emails_processed']} email(s)")
            print(f"   Updates made: {result['updates_made']}")
            if result.get('update_details'):
                print(f"   Recent updates:")
                for update in result['update_details']:
                    print(f"      {update}")
            print(f"   Total days tracked: {result['total_days']}")
            print(f"   Historical average: {result['average_steps']:,} steps/day")
            
            status = get_steps_status()
            print(f"\n👟 Status: {status['message']}")
        else:
            print("No new steps data to process")
