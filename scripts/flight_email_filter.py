#!/usr/bin/env python3
"""
Flight Email Filter
Filters out unhelpful flight status emails while keeping important ones
"""

import imaplib
import email
from email.header import decode_header
import re
from pathlib import Path
from datetime import datetime

# Configuration
IMAP_SERVER = "imap.gmail.com"
EMAIL_ACCOUNT = "[REDACTED]"
CREDENTIALS_FILE = Path.home() / ".openclaw" / "email_config.json"

# Patterns for emails to AUTO-ARCHIVE (unhelpful)
AUTO_ARCHIVE_PATTERNS = [
    r'flight status changed from pending to scheduled',
    r'flight status: scheduled\s*$',
    r'booking confirmed.*flight.*scheduled',
    r'reservation confirmed.*flight',
]

# Patterns for emails to KEEP (important)
IMPORTANT_PATTERNS = [
    r'delayed',
    r'cancelled',
    r'cancellation',
    r'gate change',
    r'departure time change',
    r'arrival time change',
    r'flight time change',
    r'schedule change',
    r'flight change',
    r'diverted',
    r'weather',
]

# Airlines to monitor
AIRLINE_KEYWORDS = [
    'delta', 'american airlines', 'united', 'jetblue', 'southwest', 'alaska',
    'flight', 'airlines', 'boarding pass', 'check-in', 'itinerary'
]

def get_credentials():
    """Get email credentials"""
    import json
    if CREDENTIALS_FILE.exists():
        with open(CREDENTIALS_FILE, 'r') as f:
            data = json.load(f)
            # Handle different credential formats
            if 'app_password' in data:
                # Remove spaces from app password if present
                password = data['app_password'].replace(' ', '')
                return {
                    'email': EMAIL_ACCOUNT,
                    'password': password
                }
            return data
    return None

def decode_email_subject(msg):
    """Decode email subject"""
    subject = msg.get("Subject", "")
    if subject:
        decoded = decode_header(subject)
        subject = ""
        for part, charset in decoded:
            if isinstance(part, bytes):
                subject += part.decode(charset or "utf-8", errors="ignore")
            else:
                subject += part
    return subject

def decode_email_body(msg):
    """Extract email body text"""
    body = ""
    if msg.is_multipart():
        for part in msg.walk():
            content_type = part.get_content_type()
            if content_type == "text/plain" or content_type == "text/html":
                try:
                    payload = part.get_payload(decode=True)
                    if payload:
                        charset = part.get_content_charset() or "utf-8"
                        body += payload.decode(charset, errors="ignore")
                except:
                    pass
    else:
        try:
            payload = msg.get_payload(decode=True)
            if payload:
                charset = msg.get_content_charset() or "utf-8"
                body += payload.decode(charset, errors="ignore")
        except:
            pass
    return body.lower()

def is_flight_email(subject, body, sender):
    """Check if this is a flight-related email"""
    text = f"{subject} {body} {sender}".lower()
    return any(keyword in text for keyword in AIRLINE_KEYWORDS)

def should_archive(subject, body):
    """Check if email should be auto-archived (unhelpful)"""
    text = f"{subject} {body}".lower()
    
    # Check if it matches important patterns first
    for pattern in IMPORTANT_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            return False  # Keep important emails
    
    # Check if it matches auto-archive patterns
    for pattern in AUTO_ARCHIVE_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            return True  # Archive unhelpful emails
    
    return False  # Default: keep email

def process_flight_emails():
    """Main function to process flight emails"""
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Checking flight emails...")
    
    creds = get_credentials()
    if not creds:
        print("No email credentials found")
        return
    
    try:
        # Connect to IMAP
        mail = imaplib.IMAP4_SSL(IMAP_SERVER)
        mail.login(creds.get('email'), creds.get('password'))
        mail.select("inbox")
        
        # Search for unread emails
        status, messages = mail.search(None, "UNSEEN")
        
        if status != "OK" or not messages[0]:
            print("No new emails")
            mail.logout()
            return
        
        email_ids = messages[0].split()
        print(f"Found {len(email_ids)} unread emails")
        
        archived_count = 0
        kept_count = 0
        
        for email_id in email_ids:
            status, msg_data = mail.fetch(email_id, "(RFC822)")
            
            if status != "OK":
                continue
            
            msg = email.message_from_bytes(msg_data[0][1])
            subject = decode_email_subject(msg)
            sender = msg.get("From", "")
            body = decode_email_body(msg)
            
            # Check if this is a flight email
            if not is_flight_email(subject, body, sender):
                continue
            
            # Decide what to do with it
            if should_archive(subject, body):
                # Archive the email (move to Archive folder)
                mail.copy(email_id, "[Gmail]/Archive")
                mail.store(email_id, "+FLAGS", "\\Deleted")
                archived_count += 1
                print(f"  Archived: {subject[:60]}...")
            else:
                kept_count += 1
                print(f"  Kept: {subject[:60]}...")
        
        mail.expunge()
        mail.logout()
        
        print(f"Processed: {archived_count} archived, {kept_count} kept")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    process_flight_emails()
