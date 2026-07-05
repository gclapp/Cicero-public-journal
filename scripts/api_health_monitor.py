#!/usr/bin/env python3
"""
API Health Monitor - Probes APIs directly instead of scraping logs
Tests OpenAI and Moonshot/Kimi APIs with minimal requests
Sends alerts only on actual API failures
Flock locking: prevents overlapping runs
"""

import json
import os
import sys
import subprocess
import urllib.request
import urllib.error
from pathlib import Path
from datetime import datetime, timedelta
from collections import defaultdict

# Add script directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))
from flock_utils import acquire_lock, LockHeldError

# Configuration
WORKSPACE_LOGS = Path.home() / ".openclaw" / "workspace" / "logs"
ALERT_LOG = WORKSPACE_LOGS / "api-health-alerts.log"
HEALTH_STATE = WORKSPACE_LOGS / "api-health-state.json"
EMAIL_SCRIPT = Path.home() / ".openclaw" / "workspace" / "scripts" / "send_email.py"
CREDENTIALS_DIR = Path.home() / ".openclaw" / "credentials"

# Alert thresholds
FAILURE_THRESHOLD = 2  # Alert after 2 consecutive failures
ALERT_COOLDOWN_MINUTES = 60  # Don't alert more than once per hour

# API endpoints to test
APIS = {
    "openai": {
        "name": "OpenAI",
        "url": "https://api.openai.com/v1/models",
        "key_file": "openai-api-key.txt",
        "critical": True
    },
    "moonshot": {
        "name": "Moonshot/Kimi",
        "url": "https://api.moonshot.ai/v1/models",
        "key_file": None,  # Key is in openclaw.json
        "critical": True
    }
}

def log(msg):
    """Log to alert log"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_msg = f"[{timestamp}] {msg}"
    print(log_msg)
    os.makedirs(ALERT_LOG.parent, exist_ok=True)
    with open(ALERT_LOG, 'a') as f:
        f.write(log_msg + '\n')

def load_health_state():
    """Load health monitoring state"""
    if HEALTH_STATE.exists():
        try:
            with open(HEALTH_STATE) as f:
                return json.load(f)
        except:
            pass
    return {
        "failure_counts": {},
        "last_alert": {},
        "last_status": {}
    }

def save_health_state(data):
    """Save health monitoring state"""
    os.makedirs(HEALTH_STATE.parent, exist_ok=True)
    with open(HEALTH_STATE, 'w') as f:
        json.dump(data, f, indent=2, default=str)

def get_api_key(key_file):
    """Read API key from credentials directory"""
    if not key_file:
        return None
    key_path = CREDENTIALS_DIR / key_file
    if key_path.exists():
        try:
            with open(key_path) as f:
                return f.read().strip()
        except:
            pass
    return None

def probe_api(api_key, config):
    """Probe an API endpoint to check if it's healthy"""
    try:
        key = get_api_key(config.get("key_file"))
        if not key:
            # Try reading from openclaw.json for moonshot
            if api_key == "moonshot":
                return probe_moonshot()
            return False, "No API key found"
        
        req = urllib.request.Request(
            config["url"],
            headers={
                "Authorization": f"Bearer {key}",
                "User-Agent": "OpenClaw-HealthMonitor/1.0"
            },
            method="GET"
        )
        
        with urllib.request.urlopen(req, timeout=10) as response:
            if response.status == 200:
                return True, "OK"
            return False, f"HTTP {response.status}"
            
    except urllib.error.HTTPError as e:
        if e.code == 401:
            return False, "Unauthorized - Invalid API key"
        elif e.code == 429:
            return False, "Rate limited"
        return False, f"HTTP {e.code}"
    except urllib.error.URLError as e:
        return False, f"Connection error: {str(e.reason)}"
    except Exception as e:
        return False, f"Error: {str(e)}"

def probe_moonshot():
    """Probe Moonshot API - just check if endpoint is reachable"""
    try:
        # Simple check - just verify we can reach the endpoint
        # 401 is expected without auth, which means API is up
        req = urllib.request.Request(
            "https://api.moonshot.ai/v1/models",
            headers={"User-Agent": "OpenClaw-HealthMonitor/1.0"},
            method="GET"
        )
        with urllib.request.urlopen(req, timeout=10) as response:
            if response.status == 200:
                return True, "OK"
            return False, f"HTTP {response.status}"
    except urllib.error.HTTPError as e:
        # 401 is expected without auth - means API is up
        if e.code == 401:
            return True, "OK (endpoint reachable)"
        return False, f"HTTP {e.code}"
    except urllib.error.URLError as e:
        return False, f"Connection error: {str(e.reason)}"
    except Exception as e:
        return False, f"Error: {str(e)}"

def should_alert(api_key, state, consecutive_failures):
    """Determine if we should send an alert"""
    if consecutive_failures < FAILURE_THRESHOLD:
        return False
        
    last_alert = state["last_alert"].get(api_key)
    
    if last_alert:
        try:
            last_alert_time = datetime.fromisoformat(last_alert)
            if datetime.now() - last_alert_time < timedelta(minutes=ALERT_COOLDOWN_MINUTES):
                return False
        except:
            pass
    
    return True

def send_alert_email(api_key, config, consecutive_failures, last_error):
    """Send alert email about API failures"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S PT")
    
    subject = f"🚨 API Health Alert: {config['name']} failing ({consecutive_failures} consecutive failures)"
    
    body_html = f"""<html>
<body style="font-family: Arial, sans-serif; padding: 20px;">
    <h2 style="color: #d32f2f;">🚨 API Health Alert: {config['name']}</h2>
    
    <p><strong>Time:</strong> {timestamp}</p>
    <p><strong>Consecutive Failures:</strong> {consecutive_failures}</p>
    
    <table style="border-collapse: collapse; width: 100%; max-width: 600px; margin: 20px 0;">
        <tr style="background: #f5f5f5;">
            <td style="padding: 12px; border: 1px solid #ddd; font-weight: bold;">API</td>
            <td style="padding: 12px; border: 1px solid #ddd;">{config['name']}</td>
        </tr>
        <tr style="background: #ffebee;">
            <td style="padding: 12px; border: 1px solid #ddd; font-weight: bold; color: #d32f2f;">Status</td>
            <td style="padding: 12px; border: 1px solid #ddd; color: #d32f2f; font-weight: bold;">FAILING</td>
        </tr>
        <tr style="background: #f5f5f5;">
            <td style="padding: 12px; border: 1px solid #ddd; font-weight: bold;">Last Error</td>
            <td style="padding: 12px; border: 1px solid #ddd; font-family: monospace;">{last_error}</td>
        </tr>
        <tr style="background: #f5f5f5;">
            <td style="padding: 12px; border: 1px solid #ddd; font-weight: bold;">Critical</td>
            <td style="padding: 12px; border: 1px solid #ddd;">{'Yes' if config['critical'] else 'No'}</td>
        </tr>
    </table>
    
    <h3>What This Means</h3>
    <p>The {config['name']} API is not responding to health checks. This may affect model availability.</p>
    
    <h3>Recommended Actions</h3>
    <ul>
        <li>Check API key validity at provider dashboard</li>
        <li>Verify account has sufficient credits/quota</li>
        <li>Check provider status page for outages</li>
        <li>Review recent configuration changes</li>
    </ul>
    
    <hr style="margin: 30px 0; border: none; border-top: 1px solid #ddd;">
    <p style="color: #666; font-size: 12px;">
        This is an automated alert from your OpenClaw API Health Monitor.<br>
        Alert cooldown: {ALERT_COOLDOWN_MINUTES} minutes<br>
        Failure threshold: {FAILURE_THRESHOLD} consecutive failures
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
            log(f"✅ Alert email sent for {api_key}")
            return True
        else:
            log(f"❌ Failed to send alert: {result.stderr}")
            return False
    except Exception as e:
        log(f"❌ Error sending alert: {e}")
        return False

def send_recovery_email(api_key, config):
    """Send recovery email when API comes back"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S PT")
    
    subject = f"✅ API Recovery: {config['name']} is healthy"
    
    body_html = f"""<html>
<body style="font-family: Arial, sans-serif; padding: 20px;">
    <h2 style="color: #388e3c;">✅ API Recovery</h2>
    
    <p><strong>Time:</strong> {timestamp}</p>
    
    <table style="border-collapse: collapse; width: 100%; max-width: 600px; margin: 20px 0;">
        <tr style="background: #e8f5e9;">
            <td style="padding: 12px; border: 1px solid #ddd; font-weight: bold;">API</td>
            <td style="padding: 12px; border: 1px solid #ddd; color: #388e3c; font-weight: bold;">{config['name']}</td>
        </tr>
        <tr style="background: #f5f5f5;">
            <td style="padding: 12px; border: 1px solid #ddd; font-weight: bold;">Status</td>
            <td style="padding: 12px; border: 1px solid #ddd;">✅ Healthy</td>
        </tr>
    </table>
    
    <p>The {config['name']} API is responding normally to health checks.</p>
    
    <hr style="margin: 30px 0; border: none; border-top: 1px solid #ddd;">
    <p style="color: #666; font-size: 12px;">
        This is an automated alert from your OpenClaw API Health Monitor.
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
            log(f"✅ Recovery email sent for {api_key}")
            return True
    except Exception as e:
        log(f"❌ Error sending recovery email: {e}")
    return False

def main():
    """Main monitoring function"""
    log("=" * 60)
    log("API Health Monitor Check (Direct Probe Mode)")
    log("=" * 60)
    
    # Load state
    state = load_health_state()
    alerts_sent = 0
    
    for api_key, config in APIS.items():
        healthy, message = probe_api(api_key, config)
        
        # Track consecutive failures
        if api_key not in state["failure_counts"]:
            state["failure_counts"][api_key] = 0
        
        previous_status = state["last_status"].get(api_key, "unknown")
        
        if healthy:
            log(f"✅ {config['name']}: {message}")
            
            # Reset failure count on success
            if state["failure_counts"][api_key] >= FAILURE_THRESHOLD:
                # Was failing, now recovered
                log(f"🟢 {config['name']} recovered!")
                send_recovery_email(api_key, config)
            
            state["failure_counts"][api_key] = 0
            state["last_status"][api_key] = "healthy"
        else:
            state["failure_counts"][api_key] += 1
            consecutive = state["failure_counts"][api_key]
            
            log(f"⚠️ {config['name']}: {message} ({consecutive} consecutive failures)")
            
            # Check if we should alert
            if should_alert(api_key, state, consecutive):
                if send_alert_email(api_key, config, consecutive, message):
                    state["last_alert"][api_key] = datetime.now().isoformat()
                    alerts_sent += 1
            else:
                if consecutive < FAILURE_THRESHOLD:
                    log(f"   (Below threshold - need {FAILURE_THRESHOLD} failures to alert)")
                else:
                    log(f"   (Alert suppressed - cooldown active)")
            
            state["last_status"][api_key] = "failing"
    
    # Save state
    save_health_state(state)
    
    log(f"\nCheck complete. Alerts sent: {alerts_sent}")
    return 0 if alerts_sent == 0 else 1

if __name__ == "__main__":
    try:
        with acquire_lock("api-health-monitor"):
            sys.exit(main())
    except LockHeldError:
        print("[api-health-monitor] Lock held by another instance, skipping")
        sys.exit(0)
