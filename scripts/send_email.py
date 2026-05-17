#!/usr/bin/env python3
"""
Gmail SMTP Email Sender - Auto-converts markdown to HTML
Usage: python3 send_email.py --to "recipient@example.com" --subject "Subject" --body "Body text"

ALWAYS sends HTML (markdown auto-converted). Use --plain for plain text only.
"""

import os
import sys
import argparse
import smtplib
import json
import re
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
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

def markdown_to_html(text):
    """Convert markdown to HTML"""
    html = text
    
    # Escape HTML entities first
    html = html.replace('&', '&amp;')
    html = html.replace('<', '&lt;')
    html = html.replace('>', '&gt;')
    
    # Headers (h1-h6)
    html = re.sub(r'^###### (.+)$', r'<h6>\1</h6>', html, flags=re.MULTILINE)
    html = re.sub(r'^##### (.+)$', r'<h5>\1</h5>', html, flags=re.MULTILINE)
    html = re.sub(r'^#### (.+)$', r'<h4>\1</h4>', html, flags=re.MULTILINE)
    html = re.sub(r'^### (.+)$', r'<h3>\1</h3>', html, flags=re.MULTILINE)
    html = re.sub(r'^## (.+)$', r'<h2>\1</h2>', html, flags=re.MULTILINE)
    html = re.sub(r'^# (.+)$', r'<h1>\1</h1>', html, flags=re.MULTILINE)
    
    # Bold and italic
    html = re.sub(r'\*\*\*(.+?)\*\*\*', r'<strong><em>\1</em></strong>', html)
    html = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', html)
    html = re.sub(r'\*(.+?)\*', r'<em>\1</em>', html)
    html = re.sub(r'_(.+?)_', r'<em>\1</em>', html)
    
    # Code inline
    html = re.sub(r'`([^`]+)`', r'<code>\1</code>', html)
    
    # Code blocks
    html = re.sub(r'```(\w+)?\n(.*?)```', r'<pre><code>\2</code></pre>', html, flags=re.DOTALL)
    
    # Links [text](url)
    html = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2">\1</a>', html)
    
    # Images ![alt](url)
    html = re.sub(r'!\[([^\]]*)\]\(([^)]+)\)', r'<img src="\2" alt="\1" />', html)
    
    # Horizontal rules
    html = re.sub(r'^---+$', r'<hr>', html, flags=re.MULTILINE)
    html = re.sub(r'^\*\*\*+$', r'<hr>', html, flags=re.MULTILINE)
    
    # Blockquotes
    lines = html.split('\n')
    in_quote = False
    result = []
    for line in lines:
        if line.startswith('&gt; '):
            if not in_quote:
                result.append('<blockquote>')
                in_quote = True
            result.append(line[5:])
        else:
            if in_quote:
                result.append('</blockquote>')
                in_quote = False
            result.append(line)
    if in_quote:
        result.append('</blockquote>')
    html = '\n'.join(result)
    
    # Lists
    lines = html.split('\n')
    in_ul = False
    in_ol = False
    result = []
    for line in lines:
        ul_match = re.match(r'^[\*\-\+] (.+)$', line)
        ol_match = re.match(r'^\d+\. (.+)$', line)
        
        if ul_match:
            if not in_ul:
                result.append('<ul>')
                in_ul = True
            if in_ol:
                result.append('</ol>')
                in_ol = False
            result.append(f'<li>{ul_match.group(1)}</li>')
        elif ol_match:
            if not in_ol:
                result.append('<ol>')
                in_ol = True
            if in_ul:
                result.append('</ul>')
                in_ul = False
            result.append(f'<li>{ol_match.group(1)}</li>')
        else:
            if in_ul:
                result.append('</ul>')
                in_ul = False
            if in_ol:
                result.append('</ol>')
                in_ol = False
            result.append(line)
    
    if in_ul:
        result.append('</ul>')
    if in_ol:
        result.append('</ol>')
    html = '\n'.join(result)
    
    # Tables (simple format)
    lines = html.split('\n')
    in_table = False
    result = []
    header_row = False
    
    for i, line in enumerate(lines):
        if '|' in line and not in_table:
            # Check if next line is separator
            if i + 1 < len(lines) and re.match(r'^[\|\-\:\s]+$', lines[i + 1]):
                in_table = True
                header_row = True
                result.append('<table>')
                result.append('<thead>')
                cells = [c.strip() for c in line.split('|') if c.strip()]
                result.append('<tr>' + ''.join(f'<th>{c}</th>' for c in cells) + '</tr>')
                result.append('</thead>')
                result.append('<tbody>')
            else:
                result.append(line)
        elif in_table and '|' in line:
            if re.match(r'^[\|\-\:\s]+$', line):
                continue  # Skip separator line
            cells = [c.strip() for c in line.split('|') if c.strip()]
            if cells:
                result.append('<tr>' + ''.join(f'<td>{c}</td>' for c in cells) + '</tr>')
        elif in_table and '|' not in line:
            in_table = False
            result.append('</tbody>')
            result.append('</table>')
            result.append(line)
        else:
            result.append(line)
    
    if in_table:
        result.append('</tbody>')
        result.append('</table>')
    html = '\n'.join(result)
    
    # Paragraphs (wrap non-tag lines)
    lines = html.split('\n')
    result = []
    in_para = False
    
    for line in lines:
        stripped = line.strip()
        if not stripped:
            if in_para:
                result.append('</p>')
                in_para = False
            result.append('')
        elif stripped.startswith('<') and stripped.endswith('>'):
            if in_para:
                result.append('</p>')
                in_para = False
            result.append(line)
        else:
            if not in_para:
                result.append('<p>')
                in_para = True
            result.append(line)
    
    if in_para:
        result.append('</p>')
    
    html = '\n'.join(result)
    
    # Line breaks within paragraphs
    html = re.sub(r'<p>(.+?)\n(.+?)</p>', r'<p>\1<br>\2</p>', html, flags=re.DOTALL)
    
    return html

def send_email(to, subject, body, html=False, cc=None, attachment=None):
    """Send email via Gmail SMTP with optional attachment"""
    config = load_config()
    
    if 'app_password' not in config:
        print("❌ Error: Gmail app password not configured.")
        print("   Run: python3 send_email.py --setup PASSWORD")
        sys.exit(1)
    
    app_password = config['app_password']
    
    # Create message
    msg = MIMEMultipart()
    msg['From'] = DEFAULT_FROM
    msg['To'] = to
    msg['Subject'] = subject
    
    if cc:
        msg['Cc'] = cc
        to = [to] + cc.split(',')
    
    # Convert markdown to HTML if not already HTML
    if html:
        # Check if body already looks like HTML
        if '<html>' in body or '<body>' in body or '<p>' in body:
            html_body = body
        else:
            # Convert markdown to HTML
            html_body = markdown_to_html(body)
            # Wrap in basic HTML structure
            html_body = f'''<!DOCTYPE html>
<html>
<head>
<style>
body {{ font-family: Georgia, serif; line-height: 1.6; color: #333; max-width: 700px; margin: 0 auto; padding: 20px; }}
h1 {{ color: #1a1a1a; }}
h2 {{ color: #2a2a2a; border-bottom: 2px solid #eee; padding-bottom: 10px; }}
h3 {{ color: #3a3a3a; }}
table {{ border-collapse: collapse; width: 100%; margin: 20px 0; }}
th, td {{ padding: 10px; text-align: left; border-bottom: 1px solid #ddd; }}
th {{ background: #f5f5f5; }}
code {{ background: #f5f5f5; padding: 2px 6px; border-radius: 3px; }}
pre {{ background: #f5f5f5; padding: 15px; overflow-x: auto; }}
blockquote {{ border-left: 4px solid #ddd; padding-left: 20px; color: #666; }}
</style>
</head>
<body>
{html_body}
</body>
</html>'''
        msg.attach(MIMEText(html_body, 'html'))
    else:
        msg.attach(MIMEText(body, 'plain'))
    
    # Add attachment if provided
    if attachment and os.path.exists(attachment):
        with open(attachment, 'rb') as f:
            part = MIMEBase('application', 'octet-stream')
            part.set_payload(f.read())
        encoders.encode_base64(part)
        part.add_header('Content-Disposition', f'attachment; filename="{os.path.basename(attachment)}"')
        msg.attach(part)
        print(f"📎 Attached: {os.path.basename(attachment)}")
    
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
    parser = argparse.ArgumentParser(description='Send email via Gmail (HTML by default)')
    parser.add_argument('--setup', metavar='PASSWORD', help='Set up Gmail app password')
    parser.add_argument('--to', help='Recipient email address')
    parser.add_argument('--subject', help='Email subject')
    parser.add_argument('--body', help='Email body')
    parser.add_argument('--body-file', help='Read body from file')
    parser.add_argument('--html', action='store_true', default=True, help='Send as HTML (default, auto-converts markdown)')
    parser.add_argument('--plain', action='store_true', help='Send as plain text (no conversion)')
    parser.add_argument('--cc', help='CC recipients (comma-separated)')
    parser.add_argument('--attach', help='Attachment file path')
    
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
    
    # Default to HTML with markdown conversion unless --plain specified
    is_html = not args.plain
    send_email(args.to, args.subject, body, html=is_html, cc=args.cc, attachment=args.attach)

if __name__ == "__main__":
    main()
