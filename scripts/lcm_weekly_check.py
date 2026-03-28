#!/usr/bin/env python3
"""
Weekly LCM Health Check - FIXED VERSION
Runs every Saturday to verify lossless-claw is working properly
Sends summary email to Geoff after each run
"""

import json
import os
import subprocess
import sys
import yaml
from datetime import datetime
from pathlib import Path

# Paths
LOG_FILE = Path.home() / ".openclaw" / "workspace" / "logs" / "lcm-weekly-check.log"
REPORT_FILE = Path.home() / ".openclaw" / "workspace" / "config" / "lcm-weekly-report.json"
EMAIL_SCRIPT = Path.home() / ".openclaw" / "workspace" / "scripts" / "send_email.py"
LCM_CONFIG = Path.home() / ".openclaw" / "config" / "lcm.yaml"
OPENCLAW_CONFIG = Path.home() / ".openclaw" / "openclaw.json"

def log(msg):
    """Log with timestamp"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_msg = f"[{timestamp}] {msg}"
    print(log_msg)
    os.makedirs(LOG_FILE.parent, exist_ok=True)
    with open(LOG_FILE, 'a') as f:
        f.write(log_msg + '\n')

def load_lcm_config():
    """Load LCM configuration from YAML file"""
    try:
        if LCM_CONFIG.exists():
            with open(LCM_CONFIG, 'r') as f:
                return yaml.safe_load(f)
    except Exception as e:
        log(f"  ⚠️ Error loading LCM config: {e}")
    return {}

def load_openclaw_config():
    """Load OpenClaw configuration from JSON"""
    try:
        if OPENCLAW_CONFIG.exists():
            with open(OPENCLAW_CONFIG, 'r') as f:
                return json.load(f)
    except Exception as e:
        log(f"  ⚠️ Error loading OpenClaw config: {e}")
    return {}

def get_lcm_parameters():
    """Extract LCM parameters from configuration files"""
    params = {
        'fresh_tail_count': 'not_configured',
        'incremental_max_depth': 'not_configured',
        'context_threshold': 'not_configured',
        'reserve_tokens': 'not_configured',
        'keep_recent_tokens': 'not_configured',
        'source': 'none'
    }
    
    # Try LCM YAML config first
    lcm_yaml = load_lcm_config()
    if lcm_yaml:
        compaction = lcm_yaml.get('compaction', {})
        if compaction:
            params['reserve_tokens'] = compaction.get('reserveTokens', 'not_configured')
            params['keep_recent_tokens'] = compaction.get('keepRecentTokens', 'not_configured')
            params['source'] = 'lcm.yaml'
    
    # Try OpenClaw JSON config for agent defaults
    oc_config = load_openclaw_config()
    if oc_config:
        agents = oc_config.get('agents', {})
        defaults = agents.get('defaults', {})
        compaction = defaults.get('compaction', {})
        
        if compaction:
            if params['reserve_tokens'] == 'not_configured':
                params['reserve_tokens'] = compaction.get('reserveTokens', 'not_configured')
            if params['keep_recent_tokens'] == 'not_configured':
                params['keep_recent_tokens'] = compaction.get('keepRecentTokens', 'not_configured')
            if params['source'] == 'none':
                params['source'] = 'openclaw.json'
    
    return params

def check_database():
    """Check LCM database status without sqlite3 CLI"""
    db_path = Path.home() / ".openclaw" / "lcm.db"
    result = {'status': 'unknown'}
    
    if not db_path.exists():
        result['status'] = 'not_created'
        return result
    
    # Get file stats
    stat = db_path.stat()
    size_mb = stat.st_size / (1024 * 1024)
    result['status'] = 'ok'
    result['size_mb'] = round(size_mb, 2)
    result['path'] = str(db_path)
    result['last_modified'] = datetime.fromtimestamp(stat.st_mtime).isoformat()
    
    # Try to read using Python's sqlite3 module
    try:
        import sqlite3
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # Count conversations
        cursor.execute("SELECT COUNT(*) FROM conversations;")
        result['conversations'] = cursor.fetchone()[0]
        
        # Count summaries
        cursor.execute("SELECT COUNT(*) FROM summaries;")
        result['total_summaries'] = cursor.fetchone()[0]
        
        # Get depth distribution
        cursor.execute("SELECT depth, COUNT(*) FROM summaries GROUP BY depth;")
        depth_counts = {}
        for row in cursor.fetchall():
            depth_counts[f'depth_{row[0]}'] = row[1]
        result['summary_depths'] = depth_counts
        
        conn.close()
        result['query_status'] = 'success'
    except ImportError:
        result['query_status'] = 'sqlite3_module_not_available'
    except Exception as e:
        result['query_status'] = f'error: {e}'
    
    return result

def send_summary_email(results):
    """Send summary email to Geoff"""
    try:
        # Build email content
        status_emoji = "✅" if results['status'] == 'ok' else "⚠️" if results['status'] == 'warning' else "❌"
        
        subject = f"{status_emoji} Weekly LCM Health Check — {datetime.now().strftime('%A, %B %d')}"
        
        # Get LCM parameters
        params = results['checks'].get('lcm_parameters', {})
        
        # Build HTML body
        html_body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <h2>🧠 Lossless-Claw Weekly Health Check</h2>
            <p><strong>Date:</strong> {datetime.now().strftime('%A, %B %d, %Y at %I:%M %p PT')}</p>
            <p><strong>Overall Status:</strong> {status_emoji} {results['status'].upper()}</p>
            
            <hr style="border: none; border-top: 1px solid #ddd; margin: 20px 0;">
            
            <h3>📊 LCM Parameters (Current Configuration)</h3>
            <table style="border-collapse: collapse; width: 100%; max-width: 600px; margin-bottom: 20px;">
                <tr style="background: #f5f5f5;">
                    <th style="padding: 10px; text-align: left; border: 1px solid #ddd;">Parameter</th>
                    <th style="padding: 10px; text-align: left; border: 1px solid #ddd;">Value</th>
                    <th style="padding: 10px; text-align: left; border: 1px solid #ddd;">Description</th>
                </tr>
                <tr>
                    <td style="padding: 10px; border: 1px solid #eee;">reserveTokens</td>
                    <td style="padding: 10px; border: 1px solid #eee;">{params.get('reserve_tokens', 'N/A')}</td>
                    <td style="padding: 10px; border: 1px solid #eee; font-size: 12px; color: #666;">Headroom before compaction triggers</td>
                </tr>
                <tr>
                    <td style="padding: 10px; border: 1px solid #eee;">keepRecentTokens</td>
                    <td style="padding: 10px; border: 1px solid #eee;">{params.get('keep_recent_tokens', 'N/A')}</td>
                    <td style="padding: 10px; border: 1px solid #eee; font-size: 12px; color: #666;">Recent context preserved during compaction</td>
                </tr>
                <tr>
                    <td style="padding: 10px; border: 1px solid #eee;">freshTailCount</td>
                    <td style="padding: 10px; border: 1px solid #eee;">{params.get('fresh_tail_count', 'N/A')}</td>
                    <td style="padding: 10px; border: 1px solid #eee; font-size: 12px; color: #666;">Messages protected from compaction</td>
                </tr>
                <tr>
                    <td style="padding: 10px; border: 1px solid #eee;">incrementalMaxDepth</td>
                    <td style="padding: 10px; border: 1px solid #eee;">{params.get('incremental_max_depth', 'N/A')}</td>
                    <td style="padding: 10px; border: 1px solid #eee; font-size: 12px; color: #666;">Compaction depth (0=leaf only, -1=unlimited)</td>
                </tr>
                <tr>
                    <td style="padding: 10px; border: 1px solid #eee;">contextThreshold</td>
                    <td style="padding: 10px; border: 1px solid #eee;">{params.get('context_threshold', 'N/A')}</td>
                    <td style="padding: 10px; border: 1px solid #eee; font-size: 12px; color: #666;">Fraction of context window triggering compaction</td>
                </tr>
                <tr>
                    <td style="padding: 10px; border: 1px solid #eee;">Config Source</td>
                    <td style="padding: 10px; border: 1px solid #eee;">{params.get('source', 'N/A')}</td>
                    <td style="padding: 10px; border: 1px solid #eee; font-size: 12px; color: #666;">Where parameters are defined</td>
                </tr>
            </table>
            
            <h3>📊 Database Status</h3>
            <table style="border-collapse: collapse; width: 100%; max-width: 500px;">
        """
        
        db = results['checks'].get('database', {})
        if db.get('status') == 'ok':
            html_body += f"""
                <tr><td style="padding: 8px; border-bottom: 1px solid #eee;">Status</td><td style="padding: 8px; border-bottom: 1px solid #eee;">✅ Online</td></tr>
                <tr><td style="padding: 8px; border-bottom: 1px solid #eee;">Size</td><td style="padding: 8px; border-bottom: 1px solid #eee;">{db.get('size_mb', 'N/A')} MB</td></tr>
                <tr><td style="padding: 8px; border-bottom: 1px solid #eee;">Path</td><td style="padding: 8px; border-bottom: 1px solid #eee;"><code>{db.get('path', 'N/A')}</code></td></tr>
            """
            if 'conversations' in db:
                html_body += f"""
                <tr><td style="padding: 8px; border-bottom: 1px solid #eee;">Conversations</td><td style="padding: 8px; border-bottom: 1px solid #eee;">{db.get('conversations', 'N/A')}</td></tr>
                """
            if 'total_summaries' in db:
                html_body += f"""
                <tr><td style="padding: 8px; border-bottom: 1px solid #eee;">Total Summaries</td><td style="padding: 8px; border-bottom: 1px solid #eee;">{db.get('total_summaries', 'N/A')}</td></tr>
                """
            if 'summary_depths' in db:
                html_body += f"""
                <tr><td style="padding: 8px; border-bottom: 1px solid #eee;">Summary Depths</td><td style="padding: 8px; border-bottom: 1px solid #eee;">{db.get('summary_depths', {})}</td></tr>
                """
            if 'last_modified' in db:
                html_body += f"""
                <tr><td style="padding: 8px; border-bottom: 1px solid #eee;">Last Modified</td><td style="padding: 8px; border-bottom: 1px solid #eee;">{db.get('last_modified', 'N/A')}</td></tr>
                """
        elif db.get('status') == 'not_created':
            html_body += '<tr><td style="padding: 8px;">⚠️ Database not yet created</td></tr>'
        else:
            html_body += f"""
                <tr><td style="padding: 8px;">❌ Error: {db.get('query_error', 'Unknown')}</td></tr>
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
        
        html_body += f"""
            </p>
            
            <hr style="border: none; border-top: 1px solid #ddd; margin: 20px 0;">
            
            <h3>📋 Configuration Summary</h3>
            <ul>
                <li><strong>Config File:</strong> <code>{LCM_CONFIG}</code></li>
                <li><strong>Database:</strong> <code>~/.openclaw/lcm.db</code></li>
                <li><strong>Report File:</strong> <code>{REPORT_FILE}</code></li>
                <li><strong>Log File:</strong> <code>{LOG_FILE}</code></li>
            </ul>
            
            <p style="color: #666; font-size: 12px; margin-top: 30px;">
                This is an automated weekly check of the lossless-claw context engine.<br>
                LCM preserves conversation history using lossless compression and hierarchical summarization.
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
    log("WEEKLY LCM HEALTH CHECK (FIXED)")
    log("=" * 60)
    
    results = {
        'timestamp': datetime.now().isoformat(),
        'checks': {},
        'status': 'ok'
    }
    
    # 1. Check LCM Parameters
    log("\n🔧 Checking LCM parameters...")
    params = get_lcm_parameters()
    results['checks']['lcm_parameters'] = params
    
    if params['source'] != 'none':
        log(f"  ✅ LCM parameters found in {params['source']}")
        log(f"     reserveTokens: {params['reserve_tokens']}")
        log(f"     keepRecentTokens: {params['keep_recent_tokens']}")
    else:
        log(f"  ⚠️ LCM parameters not found in any config file")
        results['status'] = 'warning'
    
    # 2. Check database
    log("\n📊 Checking LCM database...")
    db_result = check_database()
    results['checks']['database'] = db_result
    
    if db_result['status'] == 'ok':
        log(f"  ✅ Database exists: {db_result['size_mb']:.2f} MB")
        if 'conversations' in db_result:
            log(f"  📊 Conversations: {db_result['conversations']}")
        if 'total_summaries' in db_result:
            log(f"  📊 Total summaries: {db_result['total_summaries']}")
        if 'summary_depths' in db_result:
            log(f"  📊 Summary depths: {db_result['summary_depths']}")
    elif db_result['status'] == 'not_created':
        log(f"  ⚠️ Database not yet created")
        results['status'] = 'warning'
    else:
        log(f"  ❌ Database error")
        results['status'] = 'error'
    
    # 3. Check LCM plugin is loaded
    log("\n🔌 Checking LCM plugin status...")
    oc_config = load_openclaw_config()
    plugins = oc_config.get('plugins', {})
    entries = plugins.get('entries', {})
    
    if 'lossless-claw' in entries:
        plugin_config = entries['lossless-claw']
        if plugin_config.get('enabled', False):
            log("  ✅ Lossless-claw plugin enabled")
            results['checks']['plugin'] = {'status': 'registered', 'enabled': True}
        else:
            log("  ⚠️ Lossless-claw plugin disabled")
            results['checks']['plugin'] = {'status': 'disabled'}
            results['status'] = 'warning'
    else:
        log("  ⚠️ Lossless-claw plugin not found in config")
        results['checks']['plugin'] = {'status': 'not_found'}
        results['status'] = 'warning'
    
    # 4. Summary
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
    
    # 5. Send summary email
    log("\n📧 Sending summary email...")
    send_summary_email(results)
    
    return results['status'] == 'ok'

if __name__ == "__main__":
    success = run_check()
    sys.exit(0 if success else 1)
