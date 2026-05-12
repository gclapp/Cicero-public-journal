#!/usr/bin/env python3
"""
System Health Monitor - Comprehensive daily check
Sends multi-channel alerts for failures + daily summary
"""

import json
import subprocess
import sys
from pathlib import Path
from datetime import datetime, timedelta

# Paths
LOG_FILE = Path.home() / ".openclaw" / "workspace" / "logs" / "system-health.log"
ALERT_STATE_FILE = Path.home() / ".openclaw" / "workspace" / "state" / "alert-state.json"

# Alert channels
SMS_NUMBER = "+16507767054"
EMAIL_TO = "[REDACTED]"

def log(msg):
    """Log to file"""
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG_FILE, 'a') as f:
        f.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {msg}\n")
    print(msg)

def send_alert(subject, message, priority="high"):
    """Send multi-channel alert"""
    # Build voice message with repetition
    voice_message = f"Alert from Cicero. {subject}. {message}. I will repeat that now. Alert from Cicero. {subject}. {message}. Goodbye."
    
    # SMS/Voice Call
    try:
        subprocess.run([
            "python3", "-c",
            f"from voice_call import voice_call; voice_call(action='initiate_call', to='{SMS_NUMBER}', message='{voice_message}')"
        ], capture_output=True, timeout=30)
    except:
        pass
    
    # Telegram
    try:
        subprocess.run([
            "python3", 
            "/home/ubuntu/.openclaw/workspace/scripts/send_telegram.py",
            f"🚨 SYSTEM ALERT: {subject}\n\n{message}"
        ], capture_output=True, timeout=30)
    except:
        pass
    
    # Email
    try:
        subprocess.run([
            "python3",
            "/home/ubuntu/.openclaw/workspace/scripts/send_email.py",
            "--to", EMAIL_TO,
            "--subject", f"Cicero Alert: {subject}",
            "--body", message,
            "--html"
        ], capture_output=True, timeout=30)
    except:
        pass
    
    log(f"ALERT SENT: {subject}")

def check_memory_system():
    """Check if memory logging is working"""
    memory_dir = Path.home() / ".openclaw" / "workspace" / "memory"
    today_file = memory_dir / f"{datetime.now().strftime('%Y-%m-%d')}.md"
    
    if not today_file.exists():
        return False, "Today's memory file missing"
    
    # Check if updated in last 4 hours
    mtime = today_file.stat().st_mtime
    age_hours = (datetime.now().timestamp() - mtime) / 3600
    
    if age_hours > 4:
        return False, f"Memory file stale ({age_hours:.1f}h old)"
    
    return True, f"OK ({today_file.stat().st_size} bytes, {age_hours:.1f}h old)"

def check_cron_jobs():
    """Check if critical cron jobs are running"""
    try:
        result = subprocess.run(['crontab', '-l'], capture_output=True, text=True)
        cron_content = result.stdout
        
        critical_jobs = [
            'whoop', 'vitus', 'health', 'steps', 'water',
            'calendar', 'travel', 'competitor'
        ]
        
        missing = []
        for job in critical_jobs:
            if job not in cron_content.lower():
                missing.append(job)
        
        if missing:
            return False, f"Missing cron jobs: {', '.join(missing)}"
        
        return True, f"All critical jobs present"
    except Exception as e:
        return False, f"Cannot check cron: {e}"

def check_disk_space():
    """Check disk space"""
    try:
        result = subprocess.run(['df', '-h', '/'], capture_output=True, text=True)
        lines = result.stdout.strip().split('\n')
        if len(lines) > 1:
            parts = lines[1].split()
            usage = parts[4]  # e.g., "23%"
            usage_num = int(usage.replace('%', ''))
            
            if usage_num > 90:
                return False, f"CRITICAL: {usage} full"
            elif usage_num > 80:
                return True, f"WARNING: {usage} full"
            else:
                return True, f"OK: {usage} full"
    except Exception as e:
        return False, f"Cannot check disk: {e}"

def check_whoop_token():
    """Check Whoop token health"""
    token_file = Path.home() / ".openclaw" / "credentials" / "whoop-tokens.json"
    
    if not token_file.exists():
        return False, "Token file missing"
    
    try:
        with open(token_file) as f:
            data = json.load(f)
        
        # Check if token is recent (within 24 hours)
        mtime = token_file.stat().st_mtime
        age_hours = (datetime.now().timestamp() - mtime) / 3600
        
        if age_hours > 24:
            return False, f"Token stale ({age_hours:.1f}h old)"
        
        return True, f"OK (refreshed {age_hours:.1f}h ago)"
    except Exception as e:
        return False, f"Token error: {e}"

def check_skills():
    """Check if critical skills are working"""
    # Check if whoop client exists (not just skill directory)
    whoop_client = Path.home() / ".openclaw" / "workspace" / "skills" / "whoop-openclaw-skill" / "scripts" / "whoop_client.py"
    if not whoop_client.exists():
        return False, "Whoop client missing"
    
    # Check other skills
    weather_skill = Path.home() / ".openclaw" / "workspace" / "skills" / "weather" / "SKILL.md"
    if not weather_skill.exists():
        return False, "Weather skill missing"
    
    return True, "All critical skills present"

def check_security():
    """Basic security checks"""
    issues = []
    
    # Check credentials directory permissions
    creds_dir = Path.home() / ".openclaw" / "credentials"
    if creds_dir.exists():
        stat = creds_dir.stat()
        # Should be 700 (rwx------)
        if oct(stat.st_mode)[-3:] != '700':
            issues.append("Credentials dir permissions wrong")
    
    if issues:
        return False, f"Issues: {', '.join(issues)}"
    
    return True, "OK"

def generate_health_report():
    """Generate comprehensive health report"""
    checks = {
        "Memory System": check_memory_system(),
        "Cron Jobs": check_cron_jobs(),
        "Disk Space": check_disk_space(),
        "Whoop Token": check_whoop_token(),
        "Skills": check_skills(),
        "Security": check_security(),
    }
    
    all_ok = True
    alerts = []
    
    for name, (ok, msg) in checks.items():
        if not ok:
            all_ok = False
            alerts.append(f"{name}: {msg}")
    
    # Build clean report
    report_lines = [
        "SYSTEM HEALTH REPORT",
        f"Date: {datetime.now().strftime('%A, %B %d, %Y at %I:%M %p PT')}",
        "",
        "STATUS CHECKS:",
        "",
    ]
    
    for name, (ok, msg) in checks.items():
        status = "✓" if ok else "✗"
        report_lines.append(f"{status} {name}")
        report_lines.append(f"  {msg}")
        report_lines.append("")
    
    report_lines.append("-" * 40)
    report_lines.append("")
    
    if all_ok:
        report_lines.append("✓ ALL SYSTEMS OPERATIONAL")
    else:
        report_lines.append("✗ ISSUES DETECTED - See above")
    
    report = "\n".join(report_lines)
    
    # Send alerts if issues found
    if alerts and not all_ok:
        alert_msg = "\n".join([f"• {a}" for a in alerts])
        send_alert(
            "System Health Issues Detected",
            f"The following issues require your attention:\n\n{alert_msg}",
            priority="critical"
        )
    
    return report, all_ok

if __name__ == "__main__":
    report, ok = generate_health_report()
    print(report)
    
    # Log to file
    log("\n" + report)
    
    sys.exit(0 if ok else 1)
