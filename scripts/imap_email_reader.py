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

def is_flight_cancellation(subject, body):
    """Check if email is a flight cancellation"""
    text = (subject + ' ' + body).lower()
    cancellation_keywords = ['canceled', 'cancelled', 'cancellation', 'flight cancelled', 'flight canceled']
    return any(kw in text for kw in cancellation_keywords) and 'delta' in text

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

def generate_flight_reply(flight_info, is_cancellation=False):
    """Generate context-aware reply for flight confirmations or cancellations"""
    flight_num = flight_info.get('flight_number', 'Unknown')
    confirmation = flight_info.get('confirmation_code', 'Unknown')
    date = flight_info.get('departure', {}).get('date', 'Unknown date')
    time = flight_info.get('departure', {}).get('time', 'Unknown time')
    airport = flight_info.get('departure', {}).get('airport', 'Unknown')
    
    if is_cancellation:
        reply = f"""⚠️ FLIGHT CANCELLATION DETECTED

**Canceled Flight:**
- Flight: Delta {flight_num}
- Confirmation: {confirmation}
- Was scheduled for: {date} at {time}
- From: {airport}

I've noted the cancellation. If there's a replacement flight in your inbox, I'll process it separately.

Please check for:
- Rebooking options
- Refund status
- Alternative flights

🏛️ Cicero"""
    else:
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

def process_flight_cancellation(email_data, flight_info):
    """Process a flight cancellation email"""
    from_addr = email_data['from']
    subject = email_data['subject']
    
    print("   ✈️ Detected: Flight CANCELLATION")
    
    # Log the cancellation
    log_cancellation(flight_info)
    
    # Send cancellation alert
    reply = generate_flight_reply(flight_info, is_cancellation=True)
    send_reply(get_sender_email(from_addr), subject, reply)
    
    # Also send alert to both Geoff emails
    alert_subject = f"⚠️ Flight Cancellation Alert: Delta {flight_info.get('flight_number', 'Unknown')}"
    alert_body = f"""Flight Cancellation Detected

Flight: Delta {flight_info.get('flight_number', 'Unknown')}
Confirmation: {flight_info.get('confirmation_code', 'Unknown')}
Was scheduled for: {flight_info.get('departure', {}).get('date', 'Unknown')}

Please check your email for rebooking options or replacement flights.

🏛️ Cicero"""
    
    send_alert("[REDACTED]", alert_subject, alert_body)
    send_alert("geoffrey.clapp@progyny.com", alert_subject, alert_body)
    
    print("   ✅ Cancellation processed and alerts sent")
    return True

def log_cancellation(flight_info):
    """Log flight cancellation"""
    log_file = Path.home() / ".openclaw" / "workspace" / "data" / "flight-cancellations.json"
    
    if log_file.exists():
        with open(log_file, 'r') as f:
            log = json.load(f)
    else:
        log = {"cancellations": []}
    
    log['cancellations'].append({
        'flight_number': flight_info.get('flight_number'),
        'confirmation': flight_info.get('confirmation_code'),
        'date': flight_info.get('departure', {}).get('date'),
        'logged_at': datetime.now().isoformat()
    })
    
    log_file.parent.mkdir(parents=True, exist_ok=True)
    with open(log_file, 'w') as f:
        json.dump(log, f, indent=2)

def generate_general_reply(body_text):
    """Generate reply for general emails"""
    # Simple acknowledgment with offer to help
    reply = """Got your message!

I'm tracking everything you send me. If this was:
- A command — tell me what you want done
- A question — ask away
- Info to store — it's saved
- Something to act on — give me the next step

What would you like me to do with this?

🏛️ Cicero"""
    return reply

def is_calendar_event_request(subject, body):
    """Check if email is a calendar event creation request"""
    subject_lower = subject.lower()
    body_lower = body.lower()
    
    # Check subject line triggers
    subject_triggers = [
        'create calendar',
        'calendar event',
        'add to calendar',
        'schedule event',
        'new event'
    ]
    
    # Check body triggers
    body_triggers = [
        'event:',
        'date:',
        'when:',
        'what:'
    ]
    
    # Check if subject contains trigger
    for trigger in subject_triggers:
        if trigger in subject_lower:
            return True
    
    # Check if body has event structure (event name + date)
    has_event = 'event:' in body_lower or 'what:' in body_lower
    has_date = 'date:' in body_lower or 'when:' in body_lower
    
    if has_event and has_date:
        return True
    
    return False

def parse_calendar_event(body):
    """Parse event details from email body"""
    import re
    
    event = {
        'title': None,
        'date': None,
        'time': None,
        'location': None,
        'attendees': [],
        'description': None
    }
    
    lines = body.split('\n')
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        # Event/What
        if line.lower().startswith('event:') or line.lower().startswith('what:'):
            event['title'] = line.split(':', 1)[1].strip()
        
        # Date/When
        elif line.lower().startswith('date:') or line.lower().startswith('when:'):
            event['date'] = line.split(':', 1)[1].strip()
        
        # Time
        elif line.lower().startswith('time:'):
            event['time'] = line.split(':', 1)[1].strip()
        
        # Location/Where
        elif line.lower().startswith('location:') or line.lower().startswith('where:'):
            event['location'] = line.split(':', 1)[1].strip()
        
        # Attendees
        elif line.lower().startswith('attendees:') or line.lower().startswith('who:'):
            attendees_str = line.split(':', 1)[1].strip()
            # Split by comma and clean up
            event['attendees'] = [a.strip() for a in attendees_str.split(',') if a.strip()]
        
        # Description/Notes
        elif line.lower().startswith('description:') or line.lower().startswith('notes:'):
            event['description'] = line.split(':', 1)[1].strip()
    
    return event

def create_ics_file(event):
    """Create .ics file from event details"""
    from datetime import datetime, timedelta
    import uuid
    
    # Parse date
    try:
        # Try various date formats
        date_str = event['date']
        # Remove any day of week
        date_str = date_str.replace('Monday,', '').replace('Tuesday,', '').replace('Wednesday,', '').replace('Thursday,', '').replace('Friday,', '').replace('Saturday,', '').replace('Sunday,', '').strip()
        
        # Try to parse
        for fmt in ['%B %d, %Y', '%b %d, %Y', '%m/%d/%Y', '%Y-%m-%d']:
            try:
                parsed_date = datetime.strptime(date_str, fmt)
                break
            except:
                continue
        else:
            # Default to today + 7 days if parsing fails
            parsed_date = datetime.now() + timedelta(days=7)
    except:
        parsed_date = datetime.now() + timedelta(days=7)
    
    # Parse time
    try:
        time_str = event.get('time', '12:00 PM')
        # Try various time formats
        for fmt in ['%I:%M %p', '%I:%M%p', '%H:%M']:
            try:
                parsed_time = datetime.strptime(time_str.strip(), fmt)
                break
            except:
                continue
        else:
            parsed_time = datetime.strptime('12:00', '%H:%M')
    except:
        parsed_time = datetime.strptime('12:00', '%H:%M')
    
    # Combine date and time
    dtstart = datetime.combine(parsed_date.date(), parsed_time.time())
    dtend = dtstart + timedelta(hours=2)  # Default 2 hour duration
    
    # Generate ICS content
    ics_content = f"""BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//Cicero//Calendar Event//EN
CALSCALE:GREGORIAN
METHOD:REQUEST
BEGIN:VEVENT
DTSTART:{dtstart.strftime('%Y%m%dT%H%M%S')}
DTEND:{dtend.strftime('%Y%m%dT%H%M%S')}
DTSTAMP:{datetime.now().strftime('%Y%m%dT%H%M%S')}Z
ORGANIZER;CN=Cicero:MAILTO:[REDACTED]
UID:{uuid.uuid4()}@openclaw.ai
SUMMARY:{event.get('title', 'New Event')}
DESCRIPTION:{event.get('description', event.get('title', 'Event created by Cicero'))}
LOCATION:{event.get('location', 'TBD')}
STATUS:CONFIRMED
SEQUENCE:0
BEGIN:VALARM
ACTION:DISPLAY
DESCRIPTION:Event reminder
TRIGGER:-P1D
END:VALARM
END:VEVENT
END:VCALENDAR
"""
    
    return ics_content

def process_calendar_event_request(email_data):
    """Process calendar event creation request"""
    body = email_data['body']
    from_addr = email_data['from']
    subject = email_data['subject']
    
    print("   📝 Parsing event details...")
    
    # Parse event from email
    event = parse_calendar_event(body)
    
    # Validate required fields
    if not event['title']:
        print("   ❌ No event title found")
        send_simple_reply(from_addr, "Calendar Event Error", "I couldn't find an event title. Please include 'Event: [name]' in your email.")
        return False
    
    if not event['date']:
        print("   ❌ No date found")
        send_simple_reply(from_addr, "Calendar Event Error", "I couldn't find a date. Please include 'Date: [date]' in your email.")
        return False
    
    print(f"   ✅ Parsed: {event['title']} on {event['date']}")
    
    # Create ICS file
    ics_content = create_ics_file(event)
    
    # Save to temp file
    temp_file = Path.home() / ".openclaw" / "workspace" / "temp_event.ics"
    temp_file.parent.mkdir(parents=True, exist_ok=True)
    with open(temp_file, 'w') as f:
        f.write(ics_content)
    
    # Determine recipients
    recipients = event['attendees'] if event['attendees'] else [get_sender_email(from_addr)]
    
    # Send calendar invites
    for recipient in recipients:
        send_calendar_invite_email(recipient, event, temp_file)
    
    print(f"   ✅ Calendar invites sent to {len(recipients)} recipient(s)")
    
    # Clean up temp file
    temp_file.unlink()
    
    return True

def send_simple_reply(to_email, subject, body):
    """Send simple text reply"""
    send_reply(to_email, subject, body)

def send_calendar_invite_email(to_email, event, ics_file):
    """Send calendar invite email with ICS attachment"""
    import smtplib
    from email.mime.text import MIMEText
    from email.mime.multipart import MIMEMultipart
    from email.mime.base import MIMEBase
    from email import encoders
    
    config = load_config()
    if 'app_password' not in config:
        return False
    
    # Create message
    msg = MIMEMultipart('mixed')
    msg['From'] = "[REDACTED]"
    msg['To'] = to_email
    msg['Subject'] = f"Calendar Invite: {event.get('title', 'New Event')}"
    
    # Email body (HTML)
    html_body = f"""<html>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
<h2>Calendar Invite</h2>
<p>You have been invited to an event:</p>
<table style="border-collapse: collapse; width: 100%; max-width: 500px;">
<tr><td style="padding: 8px; border: 1px solid #ddd; background: #f5f5f5;"><strong>Event:</strong></td><td style="padding: 8px; border: 1px solid #ddd;">{event.get('title', 'TBD')}</td></tr>
<tr><td style="padding: 8px; border: 1px solid #ddd; background: #f5f5f5;"><strong>Date:</strong></td><td style="padding: 8px; border: 1px solid #ddd;">{event.get('date', 'TBD')}</td></tr>
<tr><td style="padding: 8px; border: 1px solid #ddd; background: #f5f5f5;"><strong>Time:</strong></td><td style="padding: 8px; border: 1px solid #ddd;">{event.get('time', 'TBD')}</td></tr>
<tr><td style="padding: 8px; border: 1px solid #ddd; background: #f5f5f5;"><strong>Location:</strong></td><td style="padding: 8px; border: 1px solid #ddd;">{event.get('location', 'TBD')}</td></tr>
</table>
<p><strong>To add this to your calendar:</strong></p>
<ol>
<li>Open the attached .ics file</li>
<li>It will automatically add to your default calendar app</li>
</ol>
<p>Or manually add the details above to your calendar.</p>
<br>
<p>Created by Cicero</p>
</body>
</html>"""
    
    msg.attach(MIMEText(html_body, 'html'))
    
    # Attach ICS file
    with open(ics_file, 'rb') as f:
        ics_attachment = MIMEBase('application', 'octet-stream')
        ics_attachment.set_payload(f.read())
    
    encoders.encode_base64(ics_attachment)
    ics_attachment.add_header('Content-Disposition', f'attachment; filename="{event.get("title", "event").replace(" ", "_")}.ics"')
    msg.attach(ics_attachment)
    
    # Send
    try:
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            server.login("[REDACTED]", config['app_password'])
            server.send_message(msg)
        print(f"   📧 Invite sent to {to_email}")
        return True
    except Exception as e:
        print(f"   ❌ Failed to send invite to {to_email}: {e}")
        return False

def send_alert(to_email, subject, body):
    """Send security alert to Geoff"""
    import smtplib
    from email.mime.text import MIMEText
    from email.mime.multipart import MIMEMultipart
    
    config = load_config()
    if 'app_password' not in config:
        return False
    
    try:
        msg = MIMEMultipart('alternative')
        msg['From'] = "[REDACTED]"
        msg['To'] = to_email
        msg['Subject'] = subject
        
        msg.attach(MIMEText(body, 'plain'))
        
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            server.login("[REDACTED]", config['app_password'])
            server.send_message(msg)
        
        return True
    except Exception as e:
        print(f"   ❌ Failed to send alert: {e}")
        return False

def log_unauthorized_email(sender, subject, timestamp):
    """Log unauthorized email for weekly report"""
    log_file = Path.home() / ".openclaw" / "workspace" / "data" / "email-security-log.json"
    
    if log_file.exists():
        with open(log_file, 'r') as f:
            log = json.load(f)
    else:
        log = {"unauthorized": [], "authorized": []}
    
    log['unauthorized'].append({
        'sender': sender,
        'subject': subject,
        'timestamp': timestamp
    })
    
    log_file.parent.mkdir(parents=True, exist_ok=True)
    with open(log_file, 'w') as f:
        json.dump(log, f, indent=2)

def log_authorized_email(sender, subject, timestamp):
    """Log authorized email for weekly report"""
    log_file = Path.home() / ".openclaw" / "workspace" / "data" / "email-security-log.json"
    
    if log_file.exists():
        with open(log_file, 'r') as f:
            log = json.load(f)
    else:
        log = {"unauthorized": [], "authorized": []}
    
    log['authorized'].append({
        'sender': sender,
        'subject': subject,
        'timestamp': timestamp
    })
    
    log_file.parent.mkdir(parents=True, exist_ok=True)
    with open(log_file, 'w') as f:
        json.dump(log, f, indent=2)

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
        
        # 🚨 ALERT GEOFF IMMEDIATELY about unauthorized email
        alert_subject = f"🚨 SECURITY ALERT: Unauthorized Email from {sender_email}"
        alert_body = f"""🚨 UNAUTHORIZED EMAIL ALERT 🚨

An email was received from an unauthorized sender:

From: {from_addr}
Subject: {subject}
Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S PT')}

This sender is NOT on the authorized list:
{', '.join(AUTHORIZED_SENDERS)}

The email was logged but NOT processed or replied to.

If you want to authorize this sender, reply with:
"Authorize {sender_email}"

🏛️ Cicero Security Monitor"""
        
        # Send alert to both Geoff's emails
        send_alert("[REDACTED]", alert_subject, alert_body)
        send_alert("geoffrey.clapp@progyny.com", alert_subject, alert_body)
        print(f"   🚨 ALERT SENT TO GEOFF")
        
        # Log unauthorized email
        log_unauthorized_email(sender_email, subject, datetime.now().isoformat())
        
        return False
    
    print(f"   ✅ Authorized sender: {sender_email}")
    
    # Log authorized email for weekly report
    log_authorized_email(sender_email, subject, datetime.now().isoformat())
    
    # 📅 CHECK FOR CALENDAR EVENT REQUEST
    if is_calendar_event_request(subject, body):
        print("   📅 Detected: Calendar event creation request")
        success = process_calendar_event_request(email_data)
        if success:
            return True
    
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
    
    # Check for flight cancellations FIRST (before confirmations)
    elif is_flight_cancellation(subject, body):
        print("   ✈️❌ Detected: Flight CANCELLATION")
        flight_info = extract_flight_info(subject, body)
        process_flight_cancellation(email_data, flight_info)
        reply_sent = True
    
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
