#!/usr/bin/env python3
"""
Gmail SMTP Email Sender
Usage: python3 send_email.py --to "recipient@example.com" --subject "Subject" --body "Body text" [--html]
"""

import os
import sys
import argparse
import smtplib
import json
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pathlib import Path

# Configuration
CONFIG_PATH = Path.home() / ".openclaw" / "email_config.json"
DEFAULT_FROM = "[REDACTED]"
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587

def load_config():
    """Load email configuration"""
    if CONFIG_PATH.exists():
        with open(CONFIG_PATH, 'r') as f:
            return json.load(f)
    return {}

def save_config(config):
    """Save email configuration"""
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_PATH, 'w') as f:
        json.dump(config, f, indent=2)
    os.chmod(CONFIG_PATH, 0o600)

def setup_app_password(password):
    """Store Gmail app password"""
    config = load_config()
    config['app_password'] = password
    save_config(config)
    print(f"✅ App password saved to {CONFIG_PATH}")

def send_email(to, subject, body, html=False, cc=None):
    """Send email via Gmail SMTP"""
    config = load_config()
    
    if 'app_password' not in config:
        print("❌ Error: Gmail app password not configured.")
        print("   Run: python3 send_email.py --setup PASSWORD")
        sys.exit(1)
    
    app_password = config['app_password']
    
    # Create message
    msg = MIMEMultipart('alternative')
    msg['From'] = DEFAULT_FROM
    msg['To'] = to
    msg['Subject'] = subject
    
    if cc:
        msg['Cc'] = cc
        to = [to] + cc.split(',')
    
    # Attach body
    content_type = 'html' if html else 'plain'
    msg.attach(MIMEText(body, content_type))
    
    # Send via SMTP
    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(DEFAULT_FROM, app_password)
            server.send_message(msg)
        print(f"✅ Email sent successfully to {to}")
        return True
    except Exception as e:
        print(f"❌ Failed to send email: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description='Send email via Gmail')
    parser.add_argument('--setup', metavar='PASSWORD', help='Set up Gmail app password')
    parser.add_argument('--to', help='Recipient email address')
    parser.add_argument('--subject', help='Email subject')
    parser.add_argument('--body', help='Email body')
    parser.add_argument('--body-file', help='Read body from file')
    parser.add_argument('--html', action='store_true', default=True, help='Send as HTML (default)')
    parser.add_argument('--plain', action='store_true', help='Send as plain text')
    parser.add_argument('--cc', help='CC recipients (comma-separated)')
    
    args = parser.parse_args()
    
    if args.setup:
        setup_app_password(args.setup)
        return
    
    if not all([args.to, args.subject]):
        parser.print_help()
        sys.exit(1)
    
    # Get body content
    if args.body_file:
        with open(args.body_file, 'r') as f:
            body = f.read()
    elif args.body:
        body = args.body
    else:
        print("❌ Error: Must provide --body or --body-file")
        sys.exit(1)
    
    # Default to HTML unless --plain is specified
    is_html = not args.plain
    send_email(args.to, args.subject, body, html=is_html, cc=args.cc)

if __name__ == "__main__":
    main()
