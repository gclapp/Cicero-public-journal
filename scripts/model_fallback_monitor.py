#!/usr/bin/env python3
"""
Model Fallback Monitor
Tracks when OpenClaw falls back to backup models and sends email alerts
Run this every 5 minutes via cron to detect fallback events
"""

import json
import os
import sys
from pathlib import Path
from datetime import datetime, timedelta
import subprocess
import re

# Configuration
LOG_FILE = Path.home() / ".openclaw" / "workspace" / "logs" / "model-fallbacks.json"
ALERT_LOG = Path.home() / ".openclaw" / "workspace" / "logs" / "model-alerts.log"
GATEWAY_LOG = Path.home() / ".openclaw" / "logs" / "gateway.log"
EMAIL_SCRIPT = Path.home() / ".openclaw" / "workspace" / "scripts" / "send_email.py"

# Expected primary model
PRIMARY_MODEL = "openai/gpt-5.5"
PRIMARY_ALIAS = "GPT-4o"
FALLBACK_MODELS = {
    "openai/gpt-5.4-mini": "GPT-4o Mini",
    "moonshot/kimi-k2.5": "Kimi K2.5"
}

def log(msg):
    """Log to alert log"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_msg = f"[{timestamp}] {msg}"
    print(log_msg)
    os.makedirs(ALERT_LOG.parent, exist_ok=True)
    with open(ALERT_LOG, 'a') as f:
        f.write(log_msg + '\n')

def load_fallback_log():
    """Load fallback history"""
    if LOG_FILE.exists():
        try:
            with open(LOG_FILE) as f:
                return json.load(f)
        except:
            return {"fallbacks": [], "last_alert": None, "current_model": None}
    return {"fallbacks": [], "last_alert": None, "current_model": None}

def save_fallback_log(data):
    """Save fallback history"""
    os.makedirs(LOG_FILE.parent, exist_ok=True)
    with open(LOG_FILE, 'w') as f:
        json.dump(data, f, indent=2, default=str)

def send_alert_email(fallback_model, fallback_name, reason="Automatic fallback detected"):
    """Send email alert about model fallback"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S PT")
    
    subject = f"🚨 Model Fallback Alert: Using {fallback_name}"
    
    body_html = f"""<html>
<body style="font-family: Arial, sans-serif; padding: 20px;">
    <h2 style="color: #d32f2f;">⚠️ Model Fallback Alert</h2>
    
    <p><strong>Time:</strong> {timestamp}</p>
    
    <table style="border-collapse: collapse; width: 100%; max-width: 600px; margin: 20px 0;">
        <tr style="background: #f5f5f5;">
            <td style="padding: 12px; border: 1px solid #ddd; font-weight: bold;">Expected Primary</td>
            <td style="padding: 12px; border: 1px solid #ddd;">{PRIMARY_ALIAS} ({PRIMARY_MODEL})</td>
        </tr>
        <tr style="background: #ffebee;">
            <td style="padding: 12px; border: 1px solid #ddd; font-weight: bold; color: #d32f2f;">Currently Using</td>
            <td style="padding: 12px; border: 1px solid #ddd; color: #d32f2f; font-weight: bold;">{fallback_name} ({fallback_model})</td>
        </tr>
        <tr style="background: #f5f5f5;">
            <td style="padding: 12px; border: 1px solid #ddd; font-weight: bold;">Reason</td>
            <td style="padding: 12px; border: 1px solid #ddd;">{reason}</td>
        </tr>
    </table>
    
    <h3>What This Means</h3>
    <p>OpenClaw has fallen back to a backup model because the primary OpenAI model 
    (GPT-4o) is unavailable or returned an error. The backup model is still functional 
    but may have different capabilities or performance characteristics.</p>
    
    <h3>Common Causes</h3>
    <ul>
        <li>OpenAI API rate limiting</li>
        <li>OpenAI service outage</li>
        <li>API key issues or expiration</li>
        <li>Network connectivity to OpenAI</li>
        <li>Model overload/high demand</li>
    </ul>
    
    <h3>What You Can Do</h3>
    <ul>
        <li>Check <a href="https://status.openai.com">OpenAI Status Page</a></li>
        <li>Verify API key is valid at <a href="https://platform.openai.com">OpenAI Platform</a></li>
        <li>Wait for service to recover (fallback is automatic)</li>
        <li>Contact support if persistent</li>
    </ul>
    
    <hr style="margin: 30px 0; border: none; border-top: 1px solid #ddd;">
    <p style="color: #666; font-size: 12px;">
        This is an automated alert from your OpenClaw model fallback monitor.<br>
        Log file: {LOG_FILE}
    </p>
</body>
</html>"""
    
    try:
        result = subprocess.run(
            [
                sys.executable,
                str(EMAIL_SCRIPT),
                "--to", "[REDACTED]",
                "--subject", subject,
                "--body", body_html,
                "--html"
            ],
            capture_output=True,
            text=True,
            timeout=60
        )
        if result.returncode == 0:
            log(f"✅ Alert email sent successfully for fallback to {fallback_model}")
            return True
        else:
            log(f"❌ Failed to send alert email: {result.stderr}")
            return False
    except Exception as e:
        log(f"❌ Error sending alert email: {e}")
        return False

def send_recovery_email():
    """Send email alert about recovery to primary model"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S PT")
    
    subject = f"✅ Model Recovery: Back to {PRIMARY_ALIAS}"
    
    body_html = f"""<html>
<body style="font-family: Arial, sans-serif; padding: 20px;">
    <h2 style="color: #388e3c;">✅ Model Recovery</h2>
    
    <p><strong>Time:</strong> {timestamp}</p>
    
    <table style="border-collapse: collapse; width: 100%; max-width: 600px; margin: 20px 0;">
        <tr style="background: #e8f5e9;">
            <td style="padding: 12px; border: 1px solid #ddd; font-weight: bold;">Current Model</td>
            <td style="padding: 12px; border: 1px solid #ddd; color: #388e3c; font-weight: bold;">{PRIMARY_ALIAS} ({PRIMARY_MODEL})</td>
        </tr>
        <tr style="background: #f5f5f5;">
            <td style="padding: 12px; border: 1px solid #ddd; font-weight: bold;">Status</td>
            <td style="padding: 12px; border: 1px solid #ddd;">✅ Recovered to primary model</td>
        </tr>
    </table>
    
    <p>OpenClaw has successfully returned to the primary OpenAI model (GPT-4o). 
    All systems are operating normally.</p>
    
    <hr style="margin: 30px 0; border: none; border-top: 1px solid #ddd;">
    <p style="color: #666; font-size: 12px;">
        This is an automated alert from your OpenClaw model fallback monitor.
    </p>
</body>
</html>"""
    
    try:
        result = subprocess.run(
            [
                sys.executable,
                str(EMAIL_SCRIPT),
                "--to", "[REDACTED]",
                "--subject", subject,
                "--body", body_html,
                "--html"
            ],
            capture_output=True,
            text=True,
            timeout=60
        )
        if result.returncode == 0:
            log(f"✅ Recovery email sent successfully")
            return True
        else:
            log(f"❌ Failed to send recovery email: {result.stderr}")
            return False
    except Exception as e:
        log(f"❌ Error sending recovery email: {e}")
        return False

def detect_model_from_logs():
    """Try to detect current model from recent gateway logs"""
    try:
        if not GATEWAY_LOG.exists():
            return None
        
        # Read last 100 lines of gateway log
        with open(GATEWAY_LOG, 'r') as f:
            lines = f.readlines()[-100:]
        
        # Look for model references
        for line in reversed(lines):
            for model_id, name in FALLBACK_MODELS.items():
                if model_id in line or name in line:
                    return model_id
            if PRIMARY_MODEL in line or PRIMARY_ALIAS in line:
                return PRIMARY_MODEL
        
        return None
    except Exception as e:
        log(f"Error reading gateway logs: {e}")
        return None

def main():
    """Main monitoring function"""
    log("=" * 60)
    log("Model Fallback Monitor Check")
    log("=" * 60)
    
    # Check for command line arguments
    if len(sys.argv) > 1:
        if sys.argv[1] == "--report":
            # Manual report mode - report current model from argument
            if len(sys.argv) > 2:
                current = sys.argv[2]
                log(f"Manual report: {current}")
            else:
                log("Usage: model_fallback_monitor.py --report <model_name>")
                return
        elif sys.argv[1] == "--check":
            # Just check and report status
            pass
        else:
            current = sys.argv[1]
    else:
        # Get current model from marker file or environment
        current = None
        marker_file = Path.home() / ".openclaw" / "workspace" / "logs" / "current-model.txt"
        if marker_file.exists():
            try:
                with open(marker_file) as f:
                    current = f.read().strip()
            except:
                pass
        
        # Fallback: try to detect from logs
        if not current:
            current = detect_model_from_logs()
        
        # Fallback: use environment if available
        if not current:
            current = os.environ.get('OPENCLAW_CURRENT_MODEL')
    
    if not current:
        log("⚠️ Could not determine current model, skipping check")
        log("Usage: model_fallback_monitor.py <model_name> or --report <model_name>")
        return
    
    # Load history
    data = load_fallback_log()
    
    log(f"Detected model: {current}")
    log(f"Expected primary: {PRIMARY_MODEL}")
    
    # Determine if we're on primary or fallback
    is_fallback = any(fb in current for fb in FALLBACK_MODELS.keys())
    is_primary = PRIMARY_MODEL in current or PRIMARY_ALIAS in current or "gpt-5.5" in current
    
    previous_model = data.get("current_model")
    
    if is_fallback and not is_primary:
        # We're on a fallback model
        fallback_id = None
        fallback_name = None
        for fb_id, fb_name in FALLBACK_MODELS.items():
            if fb_id in current or fb_name in current:
                fallback_id = fb_id
                fallback_name = fb_name
                break
        
        if fallback_id:
            log(f"🔴 FALLBACK DETECTED: Currently using {fallback_name}")
            
            # Only alert if this is a new fallback (different from previous check)
            if previous_model != fallback_id:
                # Record the fallback
                fallback_entry = {
                    "timestamp": datetime.now().isoformat(),
                    "fallback_model": fallback_id,
                    "expected_primary": PRIMARY_MODEL,
                    "alert_sent": False
                }
                
                # Check if we already sent an alert recently (within last hour)
                should_alert = True
                if data["last_alert"]:
                    try:
                        last_alert_time = datetime.fromisoformat(data["last_alert"])
                        time_since_alert = datetime.now() - last_alert_time
                        if time_since_alert.total_seconds() < 3600:  # 1 hour
                            log(f"⏭️ Alert already sent {time_since_alert.total_seconds()/60:.0f} minutes ago, skipping")
                            should_alert = False
                    except:
                        pass
                
                if should_alert:
                    # Send email alert
                    if send_alert_email(fallback_id, fallback_name):
                        fallback_entry["alert_sent"] = True
                        data["last_alert"] = datetime.now().isoformat()
                
                data["fallbacks"].append(fallback_entry)
            else:
                log(f"⏭️ Still on fallback {fallback_name}, no change from previous check")
            
            data["current_model"] = fallback_id
            save_fallback_log(data)
            
    elif is_primary:
        log(f"✅ Running on primary model ({PRIMARY_MODEL})")
        
        # Check if we recovered from a fallback
        if previous_model and previous_model != PRIMARY_MODEL:
            log("🟢 Recovered to primary model!")
            
            # Update the last fallback entry with recovery info
            if data["fallbacks"]:
                last_fallback = data["fallbacks"][-1]
                if not last_fallback.get("recovery_time"):
                    last_fallback["recovery_time"] = datetime.now().isoformat()
                    save_fallback_log(data)
                    
                    # Send recovery email
                    send_recovery_email()
        
        data["current_model"] = PRIMARY_MODEL
        save_fallback_log(data)
        
    else:
        log(f"⚠️ Unknown model state: {current}")
        data["current_model"] = current
        save_fallback_log(data)

if __name__ == "__main__":
    main()
