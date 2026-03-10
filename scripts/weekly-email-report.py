#!/usr/bin/env python3
"""
Weekly Email Report Generator
Sends summary of all emails received every Saturday
"""

import json
from pathlib import Path
from datetime import datetime, timedelta
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Paths
LOG_FILE = Path.home() / ".openclaw" / "workspace" / "data" / "email-security-log.json"
CONFIG_PATH = Path.home() / ".openclaw" / "email_config.json"

# Recipients
RECIPIENTS = [
    "[REDACTED]",
    "geoffrey.clapp@progyny.com"
]

def load_config():
    """Load email credentials"""
    if CONFIG_PATH.exists():
        with open(CONFIG_PATH, 'r') as f:
            return json.load(f)
    return {}

def load_email_log():
    """Load email security log"""
    if LOG_FILE.exists():
        with open(LOG_FILE, 'r') as f:
            return json.load(f)
    return {"unauthorized": [], "authorized": []}

def count_by_sender(emails):
    """Count emails by sender"""
    counts = {}
    for email in emails:
        sender = email['sender']
        counts[sender] = counts.get(sender, 0) + 1
    return counts

def generate_weekly_report():
    """Generate weekly email report"""
    log = load_email_log()
    
    # Get date range (last 7 days)
    end_date = datetime.now()
    start_date = end_date - timedelta(days=7)
    
    # Filter emails from last 7 days
    authorized_recent = [
        e for e in log.get('authorized', [])
        if datetime.fromisoformat(e['timestamp']) >= start_date
    ]
    
    unauthorized_recent = [
        e for e in log.get('unauthorized', [])
        if datetime.fromisoformat(e['timestamp']) >= start_date
    ]
    
    # Count by sender
    authorized_counts = count_by_sender(authorized_recent)
    unauthorized_counts = count_by_sender(unauthorized_recent)
    
    # Build HTML report
    html = f"""<html>
<head>
<style>
body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.6; color: #333; max-width: 700px; margin: 0 auto; padding: 20px; }}
h1 {{ color: #2c3e50; border-bottom: 3px solid #3498db; padding-bottom: 10px; }}
h2 {{ color: #34495e; margin-top: 30px; border-left: 4px solid #3498db; padding-left: 15px; }}
table {{ border-collapse: collapse; width: 100%; margin: 20px 0; }}
th, td {{ border: 1px solid #ddd; padding: 12px; text-align: left; }}
th {{ background-color: #3498db; color: white; }}
tr:nth-child(even) {{ background-color: #f2f2f2; }}
.warning {{ background-color: #fff3cd; border-left: 4px solid #ffc107; padding: 15px; margin: 20px 0; }}
.success {{ background-color: #d4edda; border-left: 4px solid #28a745; padding: 15px; margin: 20px 0; }}
.footer {{ margin-top: 40px; padding-top: 20px; border-top: 2px solid #e9ecef; font-size: 14px; color: #6c757d; text-align: center; }}
</style>
</head>
<body>
<h1>📧 Weekly Email Report</h1>
<p><strong>Week of:</strong> {start_date.strftime('%A, %B %d')} - {end_date.strftime('%A, %B %d, %Y')}</p>

<div class="success">
<h2>✅ Authorized Emails</h2>
<p><strong>Total:</strong> {len(authorized_recent)} emails</p>
</div>

<h3>Authorized Senders Breakdown</h3>
<table>
<tr><th>Sender</th><th>Email Address</th><th>Count</th></tr>
"""
    
    # Add authorized senders
    for sender, count in sorted(authorized_counts.items(), key=lambda x: x[1], reverse=True):
        html += f"<tr><td>{sender.split('@')[0].title()}</td><td>{sender}</td><td>{count}</td></tr>\n"
    
    if not authorized_counts:
        html += "<tr><td colspan='3'>No authorized emails this week</td></tr>\n"
    
    html += "</table>\n"
    
    # Unauthorized section
    html += f"""
<div class="{'warning' if unauthorized_recent else 'success'}">
<h2>⚠️ Unauthorized Emails</h2>
<p><strong>Total:</strong> {len(unauthorized_recent)} emails</p>
</div>
"""
    
    if unauthorized_recent:
        html += "<h3>Unauthorized Senders</h3>\n<table>\n"
        html += "<tr><th>Sender</th><th>Subject</th><th>Date</th></tr>\n"
        
        for email in unauthorized_recent:
            date_str = datetime.fromisoformat(email['timestamp']).strftime('%Y-%m-%d %H:%M')
            html += f"<tr><td>{email['sender']}</td><td>{email['subject']}</td><td>{date_str}</td></tr>\n"
        
        html += "</table>\n"
    else:
        html += "<p>🎉 No unauthorized emails this week!</p>\n"
    
    # Summary stats
    total = len(authorized_recent) + len(unauthorized_recent)
    html += f"""
<div class="success">
<h2>📊 Summary</h2>
<ul>
<li><strong>Total emails received:</strong> {total}</li>
<li><strong>Authorized:</strong> {len(authorized_recent)} ({len(authorized_recent)/total*100:.1f}% if total > 0 else 0)</li>
<li><strong>Unauthorized:</strong> {len(unauthorized_recent)} ({len(unauthorized_recent)/total*100:.1f}% if total > 0 else 0)</li>
</ul>
</div>

<div class="footer">
<p>🏛️ Cicero | Weekly Email Security Report</p>
<p>This report is sent every Saturday at 9:00 AM PT</p>
</div>

</body>
</html>"""
    
    return html

def send_weekly_report():
    """Send weekly email report"""
    config = load_config()
    
    if 'app_password' not in config:
        print("❌ No app password configured")
        return False
    
    html = generate_weekly_report()
    
    msg = MIMEMultipart('alternative')
    msg['From'] = "[REDACTED]"
    msg['To'] = ", ".join(RECIPIENTS)
    msg['Subject'] = f"📧 Weekly Email Report - {datetime.now().strftime('%B %d, %Y')}"
    
    msg.attach(MIMEText(html, 'html'))
    
    try:
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            server.login("[REDACTED]", config['app_password'])
            server.send_message(msg)
        
        print(f"✅ Weekly report sent to: {', '.join(RECIPIENTS)}")
        return True
    except Exception as e:
        print(f"❌ Failed to send weekly report: {e}")
        return False

if __name__ == "__main__":
    send_weekly_report()
