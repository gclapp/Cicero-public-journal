#!/usr/bin/env python3
"""
deliver_checkin.py - Delivers pending check-ins via Telegram and Email
Called by the main session when pending-checkin.json is detected
"""

import json
import subprocess
from pathlib import Path
from datetime import datetime

def send_email(to, subject, html_body, cc=None):
    """Send HTML email using the existing send_email.py script"""
    script = "/home/ubuntu/.openclaw/workspace/scripts/send_email.py"
    
    cmd = [
        "python3", script,
        "--to", to,
        "--subject", subject,
        "--body", html_body,
        "--html"
    ]
    
    if cc:
        cmd.extend(["--cc", cc])
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        return result.returncode == 0
    except Exception as e:
        print(f"Email send failed: {e}")
        return False

def deliver_checkin():
    """Deliver pending check-in via both channels"""
    checkin_file = Path("/home/ubuntu/.openclaw/workspace/logs/pending-checkin.json")
    
    if not checkin_file.exists():
        return None
    
    with open(checkin_file) as f:
        data = json.load(f)
    
    if data.get("sent"):
        return None  # Already sent
    
    results = {
        "telegram": False,
        "email": False,
        "timestamp": datetime.utcnow().isoformat()
    }
    
    # Send email to both addresses in one email
    subject = data.get("subject", "Cicero Check-In")
    html_body = data.get("html_message", data.get("message", ""))
    
    # Send to [REDACTED] with geoffrey.clapp@progyny.com in CC
    if send_email("[REDACTED]", subject, html_body, cc="geoffrey.clapp@progyny.com"):
        results["email"] = True
    
    # Mark as sent
    data["sent"] = True
    data["delivered_at"] = datetime.utcnow().isoformat()
    data["delivery_results"] = results
    
    with open(checkin_file, 'w') as f:
        json.dump(data, f, indent=2)
    
    # Return the Telegram message for the main session to send
    return {
        "telegram_message": data.get("message", ""),
        "email_sent": results["email"],
        "checkin_type": data.get("checkin_type", "unknown")
    }

if __name__ == "__main__":
    result = deliver_checkin()
    if result:
        print(json.dumps(result))
    else:
        print("No pending check-in to deliver")
