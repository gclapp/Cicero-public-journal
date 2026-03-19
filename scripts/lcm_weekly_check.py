#!/usr/bin/env python3
"""
Weekly LCM Health Check
Runs every Saturday to verify lossless-claw is working properly
Sends summary email to Geoff after each run
"""

import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

# Paths
LOG_FILE = Path.home() / ".openclaw" / "workspace" / "logs" / "lcm-weekly-check.log"
REPORT_FILE = Path.home() / ".openclaw" / "workspace" / "config" / "lcm-weekly-report.json"
EMAIL_SCRIPT = Path.home() / ".openclaw" / "workspace" / "scripts" / "send_email.py"

def log(msg):
    """Log with timestamp"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_msg = f"[{timestamp}] {msg}"
    print(log_msg)
    os.makedirs(LOG_FILE.parent, exist_ok=True)
    with open(LOG_FILE, 'a') as f:
        f.write(log_msg + '\n')

def send_summary_email(results):
    """Send summary email to Geoff"""
    try:
        # Build email content
        status_emoji = "✅" if results['status'] == 'ok' else "⚠️" if results['status'] == 'warning' else "❌"
        
        subject = f"{status_emoji} Weekly LCM Health Check — {datetime.now().strftime('%A, %B %d')}"
        
        # Build HTML body
        html_body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <h2>🧠 Lossless-Claw Weekly Health Check</h2>
            <p><strong>Date:</strong> {datetime.now().strftime('%A, %B %d, %Y at %I:%M %p PT')}</p>
            <p><strong>Overall Status:</strong> {status_emoji} {results['status'].upper()}</p>
            
            <hr style="border: none; border-top: 1px solid #ddd; margin: 20px 0;">
            
            <h3>📊 Database Status</h3>
            <table style="border-collapse: collapse; width: 100%; max-width: 500px;">
        """
        
        db = results['checks'].get('database', {})
        if db.get('status') == 'ok':
            html_body += f"""
                <tr><td style="padding: 8px; border-bottom: 1px solid #eee;">Status</td><td style="padding: 8px; border-bottom: 1px solid #eee;">✅ Online</td></tr>
                <tr><td style="padding: 8px; border-bottom: 1px solid #eee;">Size</td><td style="padding: 8px; border-bottom: 1px solid #eee;">{db.get('size_mb', 'N/A')} MB</td></tr>
                <tr><td style="padding: 8px; border-bottom: 1px solid #eee;">Conversations</td><td style="padding: 8px; border-bottom: 1px solid #eee;">{db.get('conversations', 'N/A')}</td></tr>
                <tr><td style="padding: 8px; border-bottom: 1px solid #eee;">Total Summaries</td><td style="padding: 8px; border-bottom: 1px solid #eee;">{db.get('total_summaries', 'N/A')}</td></tr>
            """
            depths = db.get('summary_depths', {})
            if depths:
                html_body += f"""
                    <tr><td style="padding: 8px; border-bottom: 1px solid #eee;">Summary Depths</td><td style="padding: 8px; border-bottom: 1px solid #eee;">{depths}</td></tr>
                """
        elif db.get('status') == 'not_created':
            html_body += '<tr><td style="padding: 8px;">⚠️ Database not yet created</td></tr>'
        else:
            html_body += f"""
                <tr><td style="padding: 8px;">❌ Error: {db.get('query_error', 'Unknown')}</td></tr>
            """
        
        html_body += """
            </table>
            
            <h3>🔧 Environment Variables</h3>
            <table style="border-collapse: collapse; width: 100%; max-width: 500px;">
        """
        
        env = results['checks'].get('environment', {})
        for key, value in env.items():
            status = "✅" if value != 'not_set' else "❌"
            html_body += f"""
                <tr><td style="padding: 8px; border-bottom: 1px solid #eee;">{key}</td><td style="padding: 8px; border-bottom: 1px solid #eee;">{status} {value}</td></tr>
            """
        
        html_body += """
            </table>
            
            <h3>🔌 Plugin Status</h3>
            <p>
        """
        
        plugin = results['checks'].get('plugin', {})
        if plugin.get('status') == 'registered':
            html_body += "✅ Lossless-claw plugin registered"
        elif plugin.get('status') == 'not_found':
            html_body += "⚠️ Plugin not found in config"
        else:
            html_body += f"❌ Error: {plugin.get('error', 'Unknown')}"
        
        html_body += """
            </p>
            
            <h3>📁 Log Files</h3>
            <p>
        """
        
        logs = results['checks'].get('logs', {})
        if logs.get('status') == 'ok':
            html_body += "✅ LCM log file exists and is accessible"
        elif logs.get('status') == 'not_found':
            html_body += "⚠️ LCM log not found"
        else:
            html_body += f"❌ Error: {logs.get('error', 'Unknown')}"
        
        html_body += f"""
            </p>
            
            <hr style="border: none; border-top: 1px solid #ddd; margin: 20px 0;">
            
            <p style="color: #666; font-size: 12px;">
                This is an automated weekly check of the lossless-claw context engine.<br>
                Report file: <code>{REPORT_FILE}</code><br>
                Log file: <code>{LOG_FILE}</code>
            </p>
        </body>
        </html>
        """
        
        # Send email
        cmd = [
            'python3', str(EMAIL_SCRIPT),
            '--to', '[REDACTED]',
            '--cc', 'geoffrey.clapp@progyny.com',
            '--subject', subject,
            '--body', html_body,
            '--html'
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            log("  ✅ Summary email sent to [REDACTED]")
            return True
        else:
            log(f"  ❌ Email failed: {result.stderr}")
            return False
            
    except Exception as e:
        log(f"  ❌ Error sending email: {e}")
        return False

def run_check():
    """Run weekly LCM health check"""
    log("=" * 60)
    log("WEEKLY LCM HEALTH CHECK")
    log("=" * 60)
    
    results = {
        'timestamp': datetime.now().isoformat(),
        'checks': {},
        'status': 'ok'
    }
    
    # 1. Check database exists and is accessible
    log("\n📊 Checking LCM database...")
    db_path = Path.home() / ".openclaw" / "lcm.db"
    if db_path.exists():
        size_mb = db_path.stat().st_size / (1024 * 1024)
        log(f"  ✅ Database exists: {size_mb:.2f} MB")
        results['checks']['database'] = {'status': 'ok', 'size_mb': round(size_mb, 2)}
        
        # Query database stats
        try:
            stats = subprocess.run(
                ['sqlite3', str(db_path), 
                 "SELECT COUNT(*) FROM conversations;"],
                capture_output=True, text=True, timeout=10
            )
            if stats.returncode == 0:
                conversations = int(stats.stdout.strip())
                log(f"  📊 Conversations: {conversations}")
                results['checks']['database']['conversations'] = conversations
            
            # Summary depth distribution
            depths = subprocess.run(
                ['sqlite3', str(db_path),
                 "SELECT depth, COUNT(*) FROM summaries GROUP BY depth;"],
                capture_output=True, text=True, timeout=10
            )
            if depths.returncode == 0:
                depth_counts = {}
                for line in depths.stdout.strip().split('\n'):
                    if line:
                        depth, count = line.split('|')
                        depth_counts[f'depth_{depth}'] = int(count)
                log(f"  📊 Summary depths: {depth_counts}")
                results['checks']['database']['summary_depths'] = depth_counts
                
            # Total summaries
            total = subprocess.run(
                ['sqlite3', str(db_path),
                 "SELECT COUNT(*) FROM summaries;"],
                capture_output=True, text=True, timeout=10
            )
            if total.returncode == 0:
                total_summaries = int(total.stdout.strip())
                log(f"  📊 Total summaries: {total_summaries}")
                results['checks']['database']['total_summaries'] = total_summaries
                
        except Exception as e:
            log(f"  ⚠️ Database query error: {e}")
            results['checks']['database']['query_error'] = str(e)
    else:
        log(f"  ⚠️ Database not yet created")
        results['checks']['database'] = {'status': 'not_created'}
        results['status'] = 'warning'
    
    # 2. Check environment variables
    log("\n🔧 Checking environment variables...")
    env_vars = {
        'LCM_FRESH_TAIL_COUNT': os.environ.get('LCM_FRESH_TAIL_COUNT', 'not_set'),
        'LCM_INCREMENTAL_MAX_DEPTH': os.environ.get('LCM_INCREMENTAL_MAX_DEPTH', 'not_set'),
        'LCM_CONTEXT_THRESHOLD': os.environ.get('LCM_CONTEXT_THRESHOLD', 'not_set')
    }
    
    all_set = all(v != 'not_set' for v in env_vars.values())
    if all_set:
        log(f"  ✅ All environment variables set")
        for k, v in env_vars.items():
            log(f"     {k}={v}")
    else:
        log(f"  ⚠️ Some environment variables not set")
        for k, v in env_vars.items():
            status = "✅" if v != 'not_set' else "❌"
            log(f"     {status} {k}={v}")
        results['status'] = 'warning'
    
    results['checks']['environment'] = env_vars
    
    # 3. Check LCM plugin is loaded
    log("\n🔌 Checking LCM plugin status...")
    try:
        plugin_check = subprocess.run(
            ['openclaw', 'gateway', 'config.get'],
            capture_output=True, text=True, timeout=10
        )
        if 'lossless-claw' in plugin_check.stdout:
            log("  ✅ Lossless-claw plugin registered")
            results['checks']['plugin'] = {'status': 'registered'}
        else:
            log("  ⚠️ Lossless-claw plugin not found in config")
            results['checks']['plugin'] = {'status': 'not_found'}
            results['status'] = 'warning'
    except Exception as e:
        log(f"  ⚠️ Could not check plugin status: {e}")
        results['checks']['plugin'] = {'status': 'error', 'error': str(e)}
    
    # 4. Check log files
    log("\n📁 Checking log files...")
    lcm_log = Path.home() / ".openclaw" / "logs" / "lcm.log"
    if lcm_log.exists():
        # Get last 5 lines
        try:
            last_lines = subprocess.run(
                ['tail', '-5', str(lcm_log)],
                capture_output=True, text=True, timeout=5
            )
            log(f"  ✅ LCM log exists")
            log(f"  📝 Recent log entries:")
            for line in last_lines.stdout.strip().split('\n'):
                log(f"     {line}")
            results['checks']['logs'] = {'status': 'ok'}
        except Exception as e:
            log(f"  ⚠️ Could not read log: {e}")
            results['checks']['logs'] = {'status': 'error', 'error': str(e)}
    else:
        log(f"  ⚠️ LCM log not found")
        results['checks']['logs'] = {'status': 'not_found'}
    
    # 5. Summary
    log("\n" + "=" * 60)
    if results['status'] == 'ok':
        log("✅ All checks passed")
    elif results['status'] == 'warning':
        log("⚠️ Some checks returned warnings")
    else:
        log("❌ Some checks failed")
    log("=" * 60)
    
    # Save report
    os.makedirs(REPORT_FILE.parent, exist_ok=True)
    with open(REPORT_FILE, 'w') as f:
        json.dump(results, f, indent=2)
    log(f"\n📄 Report saved to: {REPORT_FILE}")
    
    # 6. Send summary email
    log("\n📧 Sending summary email...")
    send_summary_email(results)
    
    return results['status'] == 'ok'

if __name__ == "__main__":
    success = run_check()
    sys.exit(0 if success else 1)
