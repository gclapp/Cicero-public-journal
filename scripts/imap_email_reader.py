#!/usr/bin/env python3
"""
IMAP Email Reader for [REDACTED]
Polls inbox periodically and processes replies
"""

import imaplib
import email
import json
from pathlib import Path
from datetime import datetime, timedelta
import time

# Configuration
CONFIG_PATH = Path.home() / ".openclaw" / "email_config.json"
PROCESSED_FILE = Path.home() / ".openclaw" / "workspace" / "data" / "processed-emails.json"
IMAP_SERVER = "imap.gmail.com"
IMAP_PORT = 993

# Authorized senders - only these people get replies
AUTHORIZED_SENDERS = [
    "[REDACTED]",
    "geoffrey.clapp@progyny.com",
    "keers003@gmail.com"  # Grace
]

def load_config():
    """Load email credentials"""
    if CONFIG_PATH.exists():
        with open(CONFIG_PATH, 'r') as f:
            return json.load(f)
    return {}

def load_processed():
    """Load list of already processed email IDs"""
    if PROCESSED_FILE.exists():
        with open(PROCESSED_FILE, 'r') as f:
            return json.load(f)
    return {"processed_ids": [], "last_check": None}

def save_processed(data):
    """Save processed email IDs"""
    PROCESSED_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(PROCESSED_FILE, 'w') as f:
        json.dump(data, f, indent=2)

def connect_imap():
    """Connect to Gmail IMAP"""
    config = load_config()
    
    if 'app_password' not in config:
        print("❌ No app password configured")
        return None
    
    try:
        mail = imaplib.IMAP4_SSL(IMAP_SERVER, IMAP_PORT)
        mail.login("[REDACTED]", config['app_password'])
        return mail
    except Exception as e:
        print(f"❌ IMAP connection failed: {e}")
        return None

def fetch_unread_emails(mail):
    """Fetch unread emails from inbox"""
    mail.select('inbox')
    
    # Search for unread emails
    status, messages = mail.search(None, 'UNSEEN')
    
    if status != 'OK':
        print("No unread messages")
        return []
    
    email_ids = messages[0].split()
    emails = []
    
    for e_id in email_ids:
        status, msg_data = mail.fetch(e_id, '(RFC822)')
        
        if status != 'OK':
            continue
        
        raw_email = msg_data[0][1]
        msg = email.message_from_bytes(raw_email)
        
        # Extract email details
        subject = msg['Subject'] or "(No Subject)"
        from_addr = msg['From'] or "Unknown"
        date = msg['Date'] or "Unknown"
        
        # Get body
        body = ""
        if msg.is_multipart():
            for part in msg.walk():
                content_type = part.get_content_type()
                if content_type == "text/plain":
                    try:
                        body = part.get_payload(decode=True).decode('utf-8')
                    except:
                        body = str(part.get_payload())
                    break
        else:
            try:
                body = msg.get_payload(decode=True).decode('utf-8')
            except:
                body = str(msg.get_payload())
        
        emails.append({
            'id': e_id.decode(),
            'subject': subject,
            'from': from_addr,
            'date': date,
            'body': body[:1000]  # First 1000 chars
        })
    
    return emails

def extract_watch_info(subject, body):
    """Extract watch listing info from forwarded emails"""
    import re
    
    watch_data = {
        'source': None,
        'brand': None,
        'model': None,
        'year': None,
        'price': None,
        'url': None,
        'added_at': datetime.now().isoformat()
    }
    
    # Detect source
    if 'chrono24' in subject.lower() or 'chrono24' in body.lower():
        watch_data['source'] = 'Chrono24'
    elif 'bob\'s watches' in subject.lower() or 'bobswatches' in body.lower():
        watch_data['source'] = "Bob's Watches"
    elif 'ebay' in subject.lower():
        watch_data['source'] = 'eBay'
    
    # Extract year (1973 or other)
    year_match = re.search(r'19(70|71|72|73|74|75)', subject + ' ' + body)
    if year_match:
        watch_data['year'] = '19' + year_match.group(1)
    
    # Extract price
    price_match = re.search(r'\$[\d,]+(?:\.\d{2})?', body)
    if price_match:
        watch_data['price'] = price_match.group(0)
    
    # Extract URL
    url_match = re.search(r'https?://[^\s<>"{}|\\^`[\]]+', body)
    if url_match:
        watch_data['url'] = url_match.group(0)
    
    # Detect brand/model
    if 'rolex' in (subject + body).lower():
        watch_data['brand'] = 'Rolex'
        # Look for model references
        model_match = re.search(r'(Datejust|Daytona|Submariner|GMT-Master|President)', subject + body, re.IGNORECASE)
        if model_match:
            watch_data['model'] = model_match.group(1)
    
    return watch_data

def add_to_watch_tracker(watch_data):
    """Add watch listing to tracker"""
    tracker_file = Path.home() / ".openclaw" / "workspace" / "data" / "watch-emails.json"
    
    # Load existing
    if tracker_file.exists():
        with open(tracker_file, 'r') as f:
            tracker = json.load(f)
    else:
        tracker = {"watches": [], "last_updated": None}
    
    # Add new watch
    tracker['watches'].append(watch_data)
    tracker['last_updated'] = datetime.now().isoformat()
    
    # Save
    tracker_file.parent.mkdir(parents=True, exist_ok=True)
    with open(tracker_file, 'w') as f:
        json.dump(tracker, f, indent=2)
    
    return len(tracker['watches'])

def is_watch_email(subject, body):
    """Check if email is a watch alert/forward"""
    watch_keywords = ['chrono24', 'watch', 'rolex', 'datejust', '1973', 'bob\'s watches', 'bezel']
    text = (subject + ' ' + body).lower()
    return any(kw in text for kw in watch_keywords)

def is_flight_confirmation(subject, body):
    """Check if email is a flight confirmation"""
    flight_keywords = ['flight', 'confirmation code', 'delta air lines', 'boarding pass', 'itinerary']
    text = (subject + ' ' + body).lower()
    return any(kw in text for kw in flight_keywords) and 'delta' in text

def extract_flight_info(subject, body):
    """Extract flight details from confirmation emails"""
    import re
    
    flight_data = {
        'airline': 'Delta Air Lines',
        'confirmation_code': None,
        'flight_number': None,
        'departure': {},
        'arrival': {},
        'extracted_at': datetime.now().isoformat()
    }
    
    # Extract confirmation code
    code_match = re.search(r'[Cc]onfirmation code:\s*([A-Z0-9]{6})', body)
    if code_match:
        flight_data['confirmation_code'] = code_match.group(1)
    
    # Extract flight number
    flight_match = re.search(r'[Dd]elta [Aa]ir [Ll]ines\s*(\d{3,4})', subject + body)
    if flight_match:
        flight_data['flight_number'] = flight_match.group(1)
    
    # Extract date/time
    date_match = re.search(r'([A-Za-z]+,\s+[A-Za-z]+\s+\d{1,2},?\s+\d{4})', body)
    if date_match:
        flight_data['departure']['date'] = date_match.group(1)
    
    time_match = re.search(r'(\d{1,2}:\d{2}\s*(?:AM|PM|am|pm))', body)
    if time_match:
        flight_data['departure']['time'] = time_match.group(1)
    
    # Extract airports
    airport_match = re.search(r'([A-Z]{3})-[A-Za-z\s]+\)', body)
    if airport_match:
        flight_data['departure']['airport'] = airport_match.group(1)
    
    return flight_data

def save_flight_to_calendar(flight_data):
    """Save flight info for calendar integration"""
    flights_file = Path.home() / ".openclaw" / "workspace" / "data" / "pending-flights.json"
    
    if flights_file.exists():
        with open(flights_file, 'r') as f:
            flights = json.load(f)
    else:
        flights = {"flights": []}
    
    flights['flights'].append(flight_data)
    
    flights_file.parent.mkdir(parents=True, exist_ok=True)
    with open(flights_file, 'w') as f:
        json.dump(flights, f, indent=2)
    
    return True

def send_reply(to_email, subject, body):
    """Send a reply email"""
    import smtplib
    from email.mime.text import MIMEText
    from email.mime.multipart import MIMEMultipart
    
    config = load_config()
    if 'app_password' not in config:
        print("   ❌ Cannot send reply - no app password")
        return False
    
    try:
        msg = MIMEMultipart('alternative')
        msg['From'] = "[REDACTED]"
        msg['To'] = to_email
        msg['Subject'] = f"Re: {subject.replace('Re: ', '').replace('RE: ', '')}"
        
        msg.attach(MIMEText(body, 'plain'))
        
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            server.login("[REDACTED]", config['app_password'])
            server.send_message(msg)
        
        print(f"   ✅ Reply sent to {to_email}")
        return True
    except Exception as e:
        print(f"   ❌ Failed to send reply: {e}")
        return False

def generate_watch_reply(watch_info):
    """Generate context-aware reply for watch emails"""
    year = watch_info.get('year', 'Unknown year')
    brand = watch_info.get('brand', 'Unknown brand')
    model = watch_info.get('model', '')
    price = watch_info.get('price', 'Price not found')
    source = watch_info.get('source', 'Unknown source')
    url = watch_info.get('url', '')
    
    reply = f"""Got your watch alert!

**What I found:**
- {brand} {model} ({year})
- Price: {price}
- Source: {source}
"""
    
    if url:
        reply += f"- Link: {url}\n"
    
    if year == '1973':
        reply += "\n🎯 **1973 MATCH!** This fits your criteria. Want me to add it to the priority tracker?"
    elif year in ['1970', '1971', '1972', '1974', '1975']:
        reply += f"\n⚠️ Close but not 1973 (it's {year}). Still want me to track it?"
    else:
        reply += "\nNot a 1973, but I'll log it anyway."
    
    reply += "\n\n🏛️ Cicero"
    return reply

def generate_flight_reply(flight_info):
    """Generate context-aware reply for flight confirmations"""
    flight_num = flight_info.get('flight_number', 'Unknown')
    confirmation = flight_info.get('confirmation_code', 'Unknown')
    date = flight_info.get('departure', {}).get('date', 'Unknown date')
    time = flight_info.get('departure', {}).get('time', 'Unknown time')
    airport = flight_info.get('departure', {}).get('airport', 'Unknown')
    
    reply = f"""Got your flight confirmation!

**Extracted details:**
- Flight: Delta {flight_num}
- Confirmation: {confirmation}
- Date: {date}
- Time: {time}
- From: {airport}

I've saved this to your travel data. I'll add it to your calendar and create a pre-flight checklist.

🏛️ Cicero"""
    return reply

def generate_general_reply(body_text):
    """Generate reply for general emails"""
    # Simple acknowledgment with offer to help
    reply = """Got your message!

I'm tracking everything you send me. If this was:
- A **command** — tell me what you want done
- A **question** — ask away
- **Info to store** — it's saved
- **Something to act on** — give me the next step

What would you like me to do with this?

🏛️ Cicero"""
    return reply

def is_authorized_sender(from_addr):
    """Check if sender is authorized to receive replies"""
    import re
    email_match = re.search(r'<([^>]+)>', from_addr)
    sender_email = email_match.group(1) if email_match else from_addr
    
    return sender_email.lower() in [e.lower() for e in AUTHORIZED_SENDERS]

def get_sender_email(from_addr):
    """Extract email address from From field"""
    import re
    email_match = re.search(r'<([^>]+)>', from_addr)
    return email_match.group(1) if email_match else from_addr

def process_email(email_data):
    """Process a single email and send context-aware reply"""
    subject = email_data['subject']
    body = email_data['body']
    from_addr = email_data['from']
    
    sender_email = get_sender_email(from_addr)
    authorized = is_authorized_sender(from_addr)
    
    print(f"\n📧 New email from: {from_addr}")
    print(f"   Subject: {subject}")
    print(f"   Body preview: {body[:200]}...")
    
    # SECURITY: Only process emails from authorized senders
    if not authorized:
        print(f"   ⚠️ UNAUTHORIZED SENDER: {sender_email}")
        print("   🚫 No reply sent. Email logged only.")
        return False
    
    print(f"   ✅ Authorized sender: {sender_email}")
    
    # 🚨 GRACE ALERT: Immediately notify Geoff when Grace emails
    if sender_email.lower() == "keers003@gmail.com":
        print("   🚨🚨🚨 GRACE EMAIL ALERT 🚨🚨🚨")
        print("   Priority: HIGHEST - Notifying Geoff immediately")
        # Send alert to Geoff
        alert_body = f"""🚨 GRACE EMAIL ALERT 🚨

Grace just sent an email to [REDACTED]

From: {from_addr}
Subject: {subject}
Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S PT')}

Body preview:
{body[:500]}

---
I am processing this email now and will respond to Grace within 15 minutes.

🏛️ Cicero"""
        
        send_reply("[REDACTED]", "GRACE EMAIL ALERT", alert_body)
        print("   ✅ Alert sent to Geoff")
        
        # Send Grace-specific confirmation (simple, loving, no confusing details)
        grace_confirmations = [
            "Got it, beautiful! ❤️ Replying within 15 minutes. Geoff loves you so much.",
            "Message received! 💕 15 minutes max. Geoff adores you!",
            "On it! ❤️ 15 minute turnaround. Geoff is crazy about you.",
            "Working on it now! 💗 15 minutes. Geoff is so lucky to have you.",
            "Got your email! 💝 15 minute response time. Geoff loves you more than anything."
        ]
        
        import random
        grace_reply = random.choice(grace_confirmations)
        send_reply(sender_email, f"Re: {subject}", grace_reply)
        print("   ✅ Grace confirmation sent")
        reply_sent = True
        
        # Skip normal processing for Grace - she gets special handling
        return True
    
    reply_sent = False
    
    # Check for watch emails
    if is_watch_email(subject, body):
        print("   🔍 Detected: Watch alert/forward")
        watch_info = extract_watch_info(subject, body)
        count = add_to_watch_tracker(watch_info)
        print(f"   ✅ Added to watch tracker (total: {count} watches)")
        
        # Send context-aware reply
        reply_body = generate_watch_reply(watch_info)
        send_reply(sender_email, subject, reply_body)
        reply_sent = True
        
        # Check if it's a 1973 match
        if watch_info.get('year') == '1973':
            print("   🎯 1973 WATCH FOUND!")
    
    # Check for flight confirmations
    elif is_flight_confirmation(subject, body):
        print("   ✈️ Detected: Flight confirmation")
        flight_info = extract_flight_info(subject, body)
        save_flight_to_calendar(flight_info)
        print(f"   ✅ Saved flight {flight_info.get('flight_number')} with confirmation {flight_info.get('confirmation_code')}")
        
        # Send context-aware reply
        reply_body = generate_flight_reply(flight_info)
        send_reply(sender_email, subject, reply_body)
        reply_sent = True
    
    # Check for replies to my emails
    elif 'cicero' in subject.lower() or 're:' in subject.lower():
        print("   💬 Detected: Reply to my email")
        # Generate contextual reply based on content
        reply_body = generate_general_reply(body)
        send_reply(sender_email, subject, reply_body)
        reply_sent = True
    
    else:
        print("   ℹ️ General email")
        # Still send acknowledgment
        reply_body = generate_general_reply(body)
        send_reply(sender_email, subject, reply_body)
        reply_sent = True
    
    return reply_sent

def check_emails():
    """Main check function"""
    print(f"\n[{datetime.now().isoformat()}] Checking emails...")
    
    mail = connect_imap()
    if not mail:
        return
    
    try:
        emails = fetch_unread_emails(mail)
        processed = load_processed()
        
        new_count = 0
        for email_data in emails:
            if email_data['id'] not in processed['processed_ids']:
                if process_email(email_data):
                    processed['processed_ids'].append(email_data['id'])
                    new_count += 1
        
        processed['last_check'] = datetime.now().isoformat()
        save_processed(processed)
        
        print(f"✅ Processed {new_count} new emails")
        
        mail.close()
        mail.logout()
        
    except Exception as e:
        print(f"❌ Error checking emails: {e}")

def main():
    """Run email checker once (for cron)"""
    check_emails()

if __name__ == "__main__":
    main()
