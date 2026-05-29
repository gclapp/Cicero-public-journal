#!/usr/bin/env python3
"""
Token Health Monitor - Automated token monitoring and refresh
Checks both Whoop and Google Calendar tokens twice daily
Auto-refreshes using stored refresh tokens, alerts on failures

Run: python3 token_health_monitor.py [--check-only] [--alert-email EMAIL]
"""

import os
import sys
import json
import pickle
import base64
import requests
import argparse
from datetime import datetime, timedelta
from pathlib import Path

# Configuration
CREDENTIALS_DIR = Path.home() / ".openclaw" / "credentials"
LOG_DIR = Path.home() / ".openclaw" / "workspace" / "logs"
LOG_FILE = LOG_DIR / "token-health.log"
STATUS_FILE = LOG_DIR / "token-health-status.json"
EMAIL_SCRIPT = Path.home() / ".openclaw" / "workspace" / "scripts" / "send_email.py"

# Token configurations
TOKEN_CONFIG = {
    "calendar": {
        "name": "Google Calendar",
        "pickle_file": CREDENTIALS_DIR / "calendar-token.pickle",
        "credentials_file": CREDENTIALS_DIR / "calendar-credentials.json",
        "critical": True,
        "auto_refresh": True,
        "expiry_threshold_hours": 24,  # Alert if expires within 24 hours
    },
    "whoop": {
        "name": "Whoop API",
        "token_file": CREDENTIALS_DIR / "whoop-tokens.json",
        "config_file": CREDENTIALS_DIR / "whoop-config.json",
        "access_token_file": Path.home() / ".whoop_token",
        "refresh_token_file": Path.home() / ".whoop_refresh_token",
        "critical": True,
        "auto_refresh": True,
        "expiry_threshold_hours": 1,  # Whoop tokens expire in 1 hour
    },
    "github": {
        "name": "GitHub PAT",
        "token_file": CREDENTIALS_DIR / "github-token.txt",
        "critical": False,  # Not critical for daily operations
        "auto_refresh": False,  # GitHub PATs don't auto-refresh
        "expiry_threshold_days": 7,  # Alert if expires within 7 days
    }
}


def log(message, level="INFO"):
    """Log message with timestamp and level"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_line = f"[{timestamp}] [{level}] {message}"
    print(log_line)
    
    # Write to log file
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    with open(LOG_FILE, 'a') as f:
        f.write(log_line + "\n")


def send_alert_email(subject, body_html, to_email="[REDACTED]"):
    """Send alert email using the email script"""
    try:
        import subprocess
        import tempfile
        
        # Create temp file for HTML body
        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as f:
            f.write(body_html)
            temp_path = f.name
        
        # Send email
        result = subprocess.run([
            'python3', str(EMAIL_SCRIPT),
            '--to', to_email,
            '--subject', subject,
            '--body-file', temp_path,
            '--html'
        ], capture_output=True, text=True)
        
        # Clean up temp file
        os.unlink(temp_path)
        
        if result.returncode == 0:
            log(f"✅ Alert email sent to {to_email}", "SUCCESS")
            return True
        else:
            log(f"❌ Failed to send email: {result.stderr}", "ERROR")
            return False
    except Exception as e:
        log(f"❌ Email error: {e}", "ERROR")
        return False


def load_pickle_token(pickle_path):
    """Load Google OAuth token from pickle file"""
    try:
        with open(pickle_path, 'rb') as f:
            creds = pickle.load(f)
        return creds
    except Exception as e:
        log(f"Failed to load pickle token: {e}", "ERROR")
        return None


def save_pickle_token(creds, pickle_path):
    """Save Google OAuth token to pickle file"""
    try:
        with open(pickle_path, 'wb') as f:
            pickle.dump(creds, f)
        os.chmod(pickle_path, 0o600)
        return True
    except Exception as e:
        log(f"Failed to save pickle token: {e}", "ERROR")
        return False


def check_calendar_token():
    """Check Google Calendar token health"""
    config = TOKEN_CONFIG["calendar"]
    result = {
        "service": "calendar",
        "name": config["name"],
        "status": "unknown",
        "valid": False,
        "expires_soon": False,
        "action_required": False,
        "message": "",
        "checked_at": datetime.now().isoformat()
    }
    
    pickle_path = config["pickle_file"]
    
    if not pickle_path.exists():
        result["status"] = "missing"
        result["message"] = "❌ Token file not found"
        result["action_required"] = True
        return result
    
    try:
        creds = load_pickle_token(pickle_path)
        
        if not creds:
            result["status"] = "error"
            result["message"] = "❌ Failed to load credentials"
            result["action_required"] = True
            return result
        
        # Check if token is valid
        if creds.valid:
            result["status"] = "valid"
            result["valid"] = True
            
            # Check expiry
            if hasattr(creds, 'expiry') and creds.expiry:
                time_to_expiry = creds.expiry - datetime.now()
                hours_to_expiry = time_to_expiry.total_seconds() / 3600
                
                if hours_to_expiry < config["expiry_threshold_hours"]:
                    result["expires_soon"] = True
                    result["message"] = f"⚠️ Token expires in {hours_to_expiry:.1f} hours"
                    
                    # Try to refresh
                    if config["auto_refresh"] and creds.refresh_token:
                        refresh_result = refresh_calendar_token(creds, pickle_path)
                        if refresh_result:
                            result["status"] = "refreshed"
                            result["message"] = "✅ Token auto-refreshed successfully"
                            result["expires_soon"] = False
                        else:
                            result["status"] = "refresh_failed"
                            result["message"] = "❌ Token refresh failed - manual re-auth required"
                            result["action_required"] = True
                    else:
                        result["action_required"] = True
                else:
                    result["message"] = f"✅ Token valid (expires in {hours_to_expiry:.1f} hours)"
            else:
                result["message"] = "✅ Token valid (no expiry info)"
            
            return result
        
        # Token is expired or invalid
        if creds.expired:
            result["status"] = "expired"
            result["message"] = "⚠️ Token expired"
            
            if config["auto_refresh"] and creds.refresh_token:
                refresh_result = refresh_calendar_token(creds, pickle_path)
                if refresh_result:
                    result["status"] = "refreshed"
                    result["valid"] = True
                    result["message"] = "✅ Token refreshed successfully"
                else:
                    result["status"] = "refresh_failed"
                    result["message"] = "❌ Token refresh failed - manual re-auth required"
                    result["action_required"] = True
            else:
                result["action_required"] = True
        else:
            result["status"] = "invalid"
            result["message"] = "❌ Token invalid"
            result["action_required"] = True
            
    except Exception as e:
        result["status"] = "error"
        result["message"] = f"❌ Error checking token: {str(e)}"
        result["action_required"] = True
    
    return result


def refresh_calendar_token(creds, pickle_path):
    """Refresh Google Calendar token using refresh token"""
    try:
        from google.auth.transport.requests import Request
        
        log("Attempting to refresh Calendar token...")
        creds.refresh(Request())
        
        if creds.valid:
            save_pickle_token(creds, pickle_path)
            log("✅ Calendar token refreshed successfully", "SUCCESS")
            return True
        else:
            log("❌ Token refresh returned invalid credentials", "ERROR")
            return False
            
    except Exception as e:
        log(f"❌ Calendar token refresh failed: {e}", "ERROR")
        return False


def check_github_token():
    """Check GitHub PAT health"""
    config = TOKEN_CONFIG["github"]
    result = {
        "service": "github",
        "name": config["name"],
        "status": "unknown",
        "valid": False,
        "expires_soon": False,
        "action_required": False,
        "message": "",
        "checked_at": datetime.now().isoformat()
    }
    
    token_file = config["token_file"]
    
    if not token_file.exists():
        result["status"] = "missing"
        result["message"] = "❌ GitHub token file not found"
        result["action_required"] = True
        return result
    
    try:
        # Read token
        token = token_file.read_text().strip()
        
        if not token:
            result["status"] = "missing"
            result["message"] = "❌ GitHub token file is empty"
            result["action_required"] = True
            return result
        
        # Validate token with GitHub API
        headers = {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3+json"
        }
        response = requests.get(
            "https://api.github.com/user",
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            user_data = response.json()
            result["status"] = "valid"
            result["valid"] = True
            result["message"] = f"✅ Token valid ({user_data.get('login', 'unknown')})"
            
            # Check token expiration if available
            # GitHub classic tokens don't have expiry, fine-grained tokens do
            scopes = response.headers.get('X-OAuth-Scopes', 'unknown')
            log(f"GitHub token scopes: {scopes}")
            
        elif response.status_code == 401:
            result["status"] = "invalid"
            result["message"] = "❌ Token invalid (401) - may be expired or revoked"
            result["action_required"] = True
        else:
            result["status"] = "error"
            result["message"] = f"⚠️ Unexpected response: HTTP {response.status_code}"
            result["action_required"] = True
            
    except requests.exceptions.Timeout:
        result["status"] = "timeout"
        result["message"] = "⚠️ GitHub API timeout"
    except Exception as e:
        result["status"] = "error"
        result["message"] = f"❌ Error checking token: {str(e)}"
        result["action_required"] = True
    
    return result


def check_whoop_token():
    """Check Whoop token health"""
    config = TOKEN_CONFIG["whoop"]
    result = {
        "service": "whoop",
        "name": config["name"],
        "status": "unknown",
        "valid": False,
        "expires_soon": False,
        "action_required": False,
        "message": "",
        "checked_at": datetime.now().isoformat()
    }
    
    token_file = config["token_file"]
    access_token_file = config["access_token_file"]
    
    if not token_file.exists():
        result["status"] = "missing"
        result["message"] = "❌ Token file not found"
        result["action_required"] = True
        return result
    
    try:
        # Load tokens
        with open(token_file, 'r') as f:
            tokens = json.load(f)
        
        access_token = tokens.get('access_token', '')
        refresh_token = tokens.get('refresh_token', '')
        
        if not access_token:
            result["status"] = "missing"
            result["message"] = "❌ No access token in file"
            result["action_required"] = True
            return result
        
        # Validate token with API call
        is_valid = validate_whoop_token(access_token)
        
        if is_valid:
            result["status"] = "valid"
            result["valid"] = True
            result["message"] = "✅ Token valid"
            
            # Check file age as proxy for expiry
            if access_token_file.exists():
                mtime = datetime.fromtimestamp(access_token_file.stat().st_mtime)
                age_minutes = (datetime.now() - mtime).total_seconds() / 60
                
                if age_minutes > 50:  # Whoop tokens expire in ~60 minutes
                    result["expires_soon"] = True
                    result["message"] = f"⚠️ Token is {age_minutes:.0f} minutes old - refreshing..."
                    
                    # Try to refresh
                    if config["auto_refresh"] and refresh_token:
                        refresh_result = refresh_whoop_token(refresh_token)
                        if refresh_result:
                            result["status"] = "refreshed"
                            result["message"] = "✅ Token auto-refreshed successfully"
                            result["expires_soon"] = False
                        else:
                            result["status"] = "refresh_failed"
                            result["message"] = "❌ Token refresh failed - manual re-auth may be required"
                            result["action_required"] = True
            
            return result
        else:
            result["status"] = "invalid"
            result["message"] = "❌ Token invalid (API returned 401)"
            
            if config["auto_refresh"] and refresh_token:
                refresh_result = refresh_whoop_token(refresh_token)
                if refresh_result:
                    result["status"] = "refreshed"
                    result["valid"] = True
                    result["message"] = "✅ Token refreshed successfully"
                else:
                    result["status"] = "refresh_failed"
                    result["message"] = "❌ Token refresh failed - manual re-auth required"
                    result["action_required"] = True
            else:
                result["action_required"] = True
                
    except Exception as e:
        result["status"] = "error"
        result["message"] = f"❌ Error checking token: {str(e)}"
        result["action_required"] = True
    
    return result


def validate_whoop_token(access_token):
    """Validate Whoop token by making API call"""
    try:
        headers = {"Authorization": f"Bearer {access_token}"}
        response = requests.get(
            "https://api.prod.whoop.com/developer/v2/user/profile/basic",
            headers=headers,
            timeout=10
        )
        return response.status_code == 200
    except Exception as e:
        log(f"Token validation error: {e}", "ERROR")
        return False


def refresh_whoop_token(refresh_token):
    """Refresh Whoop token using refresh token"""
    config = TOKEN_CONFIG["whoop"]
    
    try:
        log("Attempting to refresh Whoop token...")
        
        # Load config
        with open(config["config_file"], 'r') as f:
            whoop_config = json.load(f)
        
        # Make refresh request
        data = {
            'grant_type': 'refresh_token',
            'refresh_token': refresh_token,
            'client_id': whoop_config['client_id'],
            'client_secret': whoop_config['client_secret'],
            'redirect_uri': whoop_config['redirect_uri']
        }
        
        response = requests.post(
            'https://api.prod.whoop.com/oauth/oauth2/token',
            data=data,
            timeout=15
        )
        
        if response.status_code == 200:
            tokens = response.json()
            
            # Validate new token
            if not validate_whoop_token(tokens['access_token']):
                log("❌ New token failed validation", "ERROR")
                return False
            
            # Save tokens
            with open(config["token_file"], 'w') as f:
                json.dump(tokens, f, indent=2)
            
            # Update access token file
            config["access_token_file"].write_text(tokens['access_token'])
            
            # Update refresh token if provided
            if 'refresh_token' in tokens:
                config["refresh_token_file"].write_text(tokens['refresh_token'])
            else:
                config["refresh_token_file"].write_text(refresh_token)
            
            # Set secure permissions
            os.chmod(config["token_file"], 0o600)
            os.chmod(config["access_token_file"], 0o600)
            os.chmod(config["refresh_token_file"], 0o600)
            
            log("✅ Whoop token refreshed successfully", "SUCCESS")
            return True
            
        elif response.status_code == 401:
            log("❌ Whoop refresh failed: Invalid credentials (401) - re-auth required", "ERROR")
            return False
        else:
            log(f"❌ Whoop refresh failed: HTTP {response.status_code}", "ERROR")
            return False
            
    except requests.exceptions.Timeout:
        log("❌ Whoop refresh timeout", "ERROR")
        return False
    except Exception as e:
        log(f"❌ Whoop refresh error: {e}", "ERROR")
        return False


def generate_alert_email(failed_services):
    """Generate HTML alert email for failed token refreshes"""
    services_html = ""
    for svc in failed_services:
        services_html += f"""
        <div style="background: #fff3cd; border-left: 4px solid #ffc107; padding: 15px; margin: 10px 0; border-radius: 4px;">
            <h3 style="margin-top: 0; color: #856404;">⚠️ {svc['name']}</h3>
            <p><strong>Status:</strong> {svc['status']}</p>
            <p><strong>Message:</strong> {svc['message']}</p>
            <p><strong>Checked at:</strong> {svc['checked_at']}</p>
        </div>
        """
    
    html = f"""<!DOCTYPE html>
<html>
<head>
<style>
body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; line-height: 1.6; color: #333; background: #f5f5f5; }}
.container {{ background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
h1 {{ color: #dc3545; margin-top: 0; }}
.code {{ background: #f8f9fa; padding: 15px; border-radius: 4px; font-family: monospace; font-size: 0.9em; overflow-x: auto; margin: 10px 0; }}
.button {{ display: inline-block; background: #007bff; color: white; padding: 10px 20px; text-decoration: none; border-radius: 4px; margin: 10px 0; }}
.footer {{ margin-top: 30px; padding-top: 20px; border-top: 1px solid #eee; color: #6c757d; font-size: 0.9em; }}
</style>
</head>
<body>
<div class="container">
<h1>🔐 Token Health Alert</h1>

<p>The automated token health monitor has detected issues with the following services:</p>

{services_html}

<h2>Manual Fix Instructions</h2>

<h3>For Google Calendar:</h3>
<div class="code">
python3 ~/.openclaw/workspace/scripts/refresh_calendar_token.py
</div>
<p>If that fails, run the full OAuth flow:</p>
<div class="code">
python3 ~/.openclaw/workspace/scripts/calendar_auth.py
</div>

<h3>For Whoop:</h3>
<div class="code">
python3 ~/.openclaw/workspace/scripts/refresh_whoop_token.py
</div>
<p>If that fails, run the full OAuth flow:</p>
<div class="code">
python3 ~/.openclaw/workspace/skills/whoop-openclaw-skill/scripts/whoop_oauth.py \\
  --config ~/.openclaw/credentials/whoop-config.json
</div>

<h3>For GitHub:</h3>
<div class="code">
# Generate new token at:
https://github.com/settings/tokens

# Save to file:
echo 'ghp_YOUR_NEW_TOKEN' > ~/.openclaw/credentials/github-token.txt
chmod 600 ~/.openclaw/credentials/github-token.txt
</div>
<p>Then update git remote URL:</p>
<div class="code">
git remote set-url origin https://gclapp:ghp_YOUR_NEW_TOKEN@github.com/gclapp/REPO_NAME.git
</div>

<div class="footer">
<p>Token Health Monitor<br>
Checked at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} UTC</p>
</div>
</div>
</body>
</html>"""
    
    return html


def save_status(results):
    """Save check results to status file"""
    try:
        STATUS_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(STATUS_FILE, 'w') as f:
            json.dump({
                "last_check": datetime.now().isoformat(),
                "results": results
            }, f, indent=2)
    except Exception as e:
        log(f"Failed to save status: {e}", "ERROR")


def load_previous_status():
    """Load previous check status"""
    try:
        if STATUS_FILE.exists():
            with open(STATUS_FILE, 'r') as f:
                return json.load(f)
    except Exception:
        pass
    return {}


def should_send_alert(failed_services, previous_status):
    """Determine if we should send an alert (rate limiting)"""
    if not failed_services:
        return False
    
    # Check if we already sent an alert recently (within 4 hours)
    if previous_status and 'last_alert_sent' in previous_status:
        last_alert = datetime.fromisoformat(previous_status['last_alert_sent'])
        if datetime.now() - last_alert < timedelta(hours=4):
            log("Alert already sent within last 4 hours, skipping...")
            return False
    
    return True


def main():
    parser = argparse.ArgumentParser(description='Token Health Monitor')
    parser.add_argument('--check-only', action='store_true', help='Only check, do not refresh')
    parser.add_argument('--alert-email', default='[REDACTED]', help='Email for alerts')
    parser.add_argument('--no-alert', action='store_true', help='Do not send email alerts')
    args = parser.parse_args()
    
    log("=" * 70)
    log("TOKEN HEALTH MONITOR - Starting check")
    log("=" * 70)
    
    # Load previous status for rate limiting
    previous_status = load_previous_status()
    
    # Check all tokens
    calendar_result = check_calendar_token()
    whoop_result = check_whoop_token()
    github_result = check_github_token()
    
    results = {
        "calendar": calendar_result,
        "whoop": whoop_result,
        "github": github_result
    }
    
    # Log results
    log("-" * 70)
    log(f"Calendar: {calendar_result['message']}")
    log(f"Whoop: {whoop_result['message']}")
    log(f"GitHub: {github_result['message']}")
    log("-" * 70)
    
    # Determine failed services
    failed_services = []
    for service, result in results.items():
        if result.get('action_required') or (not result.get('valid') and result.get('status') != 'refreshed'):
            failed_services.append(result)
    
    # Save status
    save_status(results)
    
    # Send alert if needed
    if failed_services and not args.no_alert:
        if should_send_alert(failed_services, previous_status):
            log(f"🚨 Sending alert for {len(failed_services)} failed service(s)...")
            
            subject = f"🔐 Token Health Alert: {len(failed_services)} service(s) need attention"
            body_html = generate_alert_email(failed_services)
            
            if send_alert_email(subject, body_html, args.alert_email):
                # Update last alert time
                previous_status['last_alert_sent'] = datetime.now().isoformat()
                save_status(results)
        else:
            log("Alert rate limiting active, not sending email")
    
    # Summary
    healthy_count = sum(1 for r in results.values() if r.get('valid') or r.get('status') == 'refreshed')
    failed_count = len(failed_services)
    
    log(f"Summary: {healthy_count} healthy, {failed_count} failed")
    log(f"Services: Calendar ({'✅' if calendar_result.get('valid') else '❌'}), Whoop ({'✅' if whoop_result.get('valid') else '❌'}), GitHub ({'✅' if github_result.get('valid') else '❌'})")
    log("=" * 70)
    
    # Exit with error code if any failed
    if failed_count > 0:
        sys.exit(1)
    
    sys.exit(0)


if __name__ == "__main__":
    main()
