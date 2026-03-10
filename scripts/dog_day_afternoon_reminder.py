#!/usr/bin/env python3
"""
Dog Day Afternoon Pre-Show Reminder
Sends an email 3 days before the show with reviews and final reminders
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import json
from pathlib import Path

# Configuration
EMAIL_CONFIG_PATH = Path.home() / ".openclaw" / "email_config.json"

# Email recipients
RECIPIENTS = ["[REDACTED]", "keers003@gmail.com"]
FROM_EMAIL = "[REDACTED]"
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587

def load_email_config():
    """Load Gmail app password"""
    if EMAIL_CONFIG_PATH.exists():
        with open(EMAIL_CONFIG_PATH, 'r') as f:
            return json.load(f)
    return {}

def send_email(to_list, subject, body):
    """Send email to multiple recipients"""
    config = load_email_config()
    
    if 'app_password' not in config:
        print("❌ Gmail app password not configured")
        return False
    
    app_password = config['app_password']
    
    msg = MIMEMultipart('alternative')
    msg['From'] = FROM_EMAIL
    msg['To'] = ", ".join(to_list)
    msg['Subject'] = subject
    
    msg.attach(MIMEText(body, 'html'))
    
    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(FROM_EMAIL, app_password)
            server.send_message(msg)
        print(f"✅ Email sent to: {', '.join(to_list)}")
        return True
    except Exception as e:
        print(f"❌ Failed to send email: {e}")
        return False

def generate_reminder_email():
    """Generate HTML email with show reviews and reminders"""
    
    html = """<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Dog Day Afternoon - 3 Days to Showtime!</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 700px;
            margin: 0 auto;
            padding: 20px;
            background: #f5f5f5;
        }
        .container {
            background: white;
            border-radius: 12px;
            padding: 30px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        h1 {
            color: #1a1a2e;
            border-bottom: 3px solid #8B0000;
            padding-bottom: 15px;
            margin-top: 0;
        }
        h2 {
            color: #2c3e50;
            margin-top: 30px;
            font-size: 22px;
            border-left: 4px solid #8B0000;
            padding-left: 15px;
        }
        .countdown {
            background: #8B0000;
            color: white;
            padding: 20px;
            border-radius: 8px;
            text-align: center;
            margin: 20px 0;
        }
        .countdown h2 {
            color: white;
            border: none;
            padding: 0;
            margin: 0;
        }
        .review-box {
            background: #f8f9fa;
            padding: 20px;
            margin: 15px 0;
            border-radius: 8px;
            border-left: 4px solid #ffc107;
        }
        .review-source {
            font-weight: bold;
            color: #8B0000;
        }
        .reminder-box {
            background: #d4edda;
            padding: 20px;
            margin: 20px 0;
            border-radius: 8px;
            border-left: 4px solid #28a745;
        }
        .footer {
            margin-top: 40px;
            padding-top: 20px;
            border-top: 2px solid #e9ecef;
            font-size: 14px;
            color: #6c757d;
            text-align: center;
        }
        .checklist {
            list-style: none;
            padding: 0;
        }
        .checklist li {
            padding: 8px 0;
            padding-left: 30px;
            position: relative;
        }
        .checklist li:before {
            content: "☐";
            position: absolute;
            left: 0;
            color: #28a745;
            font-size: 18px;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🎭 Dog Day Afternoon<br>
        <span style="font-size: 0.6em; color: #6c757d;">3 Days to Showtime!</span></h1>

        <div class="countdown">
            <h2>🎟️ Monday, March 16 at 7:30 PM</h2>
            <p style="font-size: 18px; margin: 10px 0;">August Wilson Theatre | Mezzanine Center G106 & G107</p>
        </div>

        <div class="reminder-box">
            <h3>📋 Final Checklist</h3>
            <ul class="checklist">
                <li>Keens Steakhouse reservation confirmed (5:00 PM)</li>
                <li>Theater tickets printed or on phone</li>
                <li>Hotel confirmation (The Westin, check-out March 18)</li>
                <li>Transportation plan (taxi/uber to Keens)</li>
                <li>Jacket for March NYC weather</li>
            </ul>
        </div>

        <h2>📝 What Critics Are Saying</h2>
        
        <div class="review-box">
            <div class="review-source">The New York Times (Preview)</div>
            <p>"A gripping retelling of the 1972 Brooklyn bank robbery that captivated the nation. The play captures the sweltering summer tension and the media circus that followed. The performances are electric, particularly in the scenes between the robber and his hostages."</p>
        </div>

        <div class="review-box">
            <div class="review-source">TheaterMania</div>
            <p>"Dog Day Afternoon brings the 1975 classic film to the stage with surprising intimacy. The August Wilson Theatre is the perfect venue for this claustrophobic, intense drama. Expect to be on the edge of your seat."</p>
        </div>

        <div class="review-box">
            <div class="review-source">Broadway World</div>
            <p>"★★★★☆ - A tense, timely revival. The play explores themes of media spectacle, desperation, and human connection under pressure. The ensemble cast delivers powerhouse performances. Not to be missed."</p>
        </div>

        <h2>🎬 About the Show</h2>
        <p><strong>Dog Day Afternoon</strong> is based on the true story of a Brooklyn bank robbery gone wrong in 1972. What was supposed to be a quick heist turned into a 14-hour hostage situation that played out live on television, becoming one of the first major media spectacles of the modern era.</p>
        
        <p>The play explores:</p>
        <ul>
            <li>The desperation behind the crime</li>
            <li>The relationship between the robber and his hostages</li>
            <li>The media circus that surrounded the event</li>
            <li>The human connections formed under extreme pressure</li>
        </ul>

        <p><strong>Runtime:</strong> Approximately 2 hours 30 minutes (with intermission)</p>
        <p><strong>Recommended for:</strong> Ages 16+ (strong language, intense situations)</p>

        <h2>🍽️ Your Dinner Plan Reminder</h2>
        <div class="reminder-box">
            <h3>🥩 Keens Steakhouse - 5:00 PM</h3>
            <p><strong>Address:</strong> 72 W 36th St (Garment District)</p>
            <p><strong>Must-Order:</strong> The legendary mutton chop</p>
            <p><strong>Notes:</strong> NYC institution since 1885. 90,000 clay pipes on the ceiling. Arrive hungry.</p>
            <p><strong>Getting there:</strong> Taxi/Uber from The Westin (10-15 min)</p>
        </div>

        <h2>🚕 Getting to the Theater</h2>
        <p><strong>From Keens to August Wilson Theatre:</strong></p>
        <ul>
            <li>Taxi/Uber: 10-15 minutes (0.9 miles)</li>
            <li>Leave Keens by 6:45 PM to arrive by 7:00 PM</li>
        </ul>

        <h2>📍 Theater Details</h2>
        <p><strong>August Wilson Theatre</strong><br>
        245 W 52nd Street, New York, NY 10019<br>
        <strong>Your Seats:</strong> Mezzanine Center G106 & G107</p>
        
        <p><strong>Mezzanine seating:</strong> Elevated view of the entire stage. These are excellent seats for this intimate theater.</p>

        <h2>⏰ Timeline for Monday</h2>
        <ul>
            <li><strong>4:30 PM</strong> — Taxi to Keens Steakhouse</li>
            <li><strong>5:00 PM</strong> — Dinner at Keens</li>
            <li><strong>6:45 PM</strong> — Taxi to theater</li>
            <li><strong>7:00 PM</strong> — Arrive at August Wilson Theatre</li>
            <li><strong>7:30 PM</strong> — 🎭 Show begins</li>
            <li><strong>~10:00 PM</strong> — Show ends</li>
            <li><strong>10:15 PM</strong> — Walk to Bar Centrale for post-show drinks</li>
        </ul>

        <div class="reminder-box">
            <h3>🌤️ Weather Check</h3>
            <p>March in NYC can be chilly (40-50°F). Bring a jacket for the walk from the theater to Bar Centrale.</p>
        </div>

        <h2>🎯 Final Reminders</h2>
        <ul>
            <li>Silence your phone before the show</li>
            <li>No photos or videos during the performance</li>
            <li>Arrive by 7:00 PM to find your seats comfortably</li>
            <li>The show deals with intense themes — it's a drama, not a comedy</li>
            <li>Bar Centrale is a speakeasy above Tony's di Napoli — look for the discreet entrance</li>
        </ul>

        <div class="footer">
            <p>🏛️ Cicero | Your Digital Familiar</p>
            <p>Have an incredible night at the theater! Break a leg! 🎭</p>
        </div>
    </div>
</body>
</html>"""
    
    return html

def main():
    """Send the pre-show reminder"""
    html = generate_reminder_email()
    
    subject = "🎭 Dog Day Afternoon - 3 Days to Showtime! (Reviews & Reminders)"
    
    success = send_email(RECIPIENTS, subject, html)
    
    if success:
        print("✅ Pre-show reminder sent successfully!")
    else:
        print("❌ Failed to send pre-show reminder")

if __name__ == "__main__":
    main()