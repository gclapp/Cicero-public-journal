#!/usr/bin/env python3
"""
Whoop Health Alerts - Monitors recovery, HRV, sleep, and strain
Sends alerts when thresholds are breached
"""

import json
import requests
from pathlib import Path
from datetime import datetime, timedelta

# Config
TOKEN_FILE = Path.home() / '.whoop_token'
DATA_DIR = Path.home() / '.openclaw' / 'workspace' / 'data' / 'whoop'
ALERT_STATE_FILE = Path.home() / '.openclaw' / 'workspace' / 'config' / 'whoop-alert-state.json'
EMAIL_SCRIPT = Path.home() / '.openclaw' / 'workspace' / 'scripts' / 'send_email.py'

def get_token():
    if TOKEN_FILE.exists():
        return TOKEN_FILE.read_text().strip()
    return None

def fetch_latest_whoop():
    """Fetch latest Whoop data from API"""
    token = get_token()
    if not token:
        return None
    
    headers = {'Authorization': f'Bearer {token}'}
    BASE_URL = 'https://api.prod.whoop.com/developer/v2'
    
    try:
        recovery_resp = requests.get(f'{BASE_URL}/recovery', headers=headers, params={'limit': 3})
        recovery_resp.raise_for_status()
        recovery_data = recovery_resp.json()
        
        sleep_resp = requests.get(f'{BASE_URL}/activity/sleep', headers=headers, params={'limit': 3})
        sleep_resp.raise_for_status()
        sleep_data = sleep_resp.json()
        
        cycle_resp = requests.get(f'{BASE_URL}/cycle', headers=headers, params={'limit': 3})
        cycle_resp.raise_for_status()
        cycle_data = cycle_resp.json()
        
        return {
            'recovery': recovery_data.get('records', []),
            'sleep': sleep_data.get('records', []),
            'cycles': cycle_data.get('records', [])
        }
    except Exception as e:
        print(f"Error fetching Whoop: {e}")
        return None

def load_alert_state():
    if ALERT_STATE_FILE.exists():
        with open(ALERT_STATE_FILE, 'r') as f:
            return json.load(f)
    return {
        'last_alerts': {},
        'alert_counts': {},
        'hrv_baseline': None,
        'baseline_date': None
    }

def save_alert_state(state):
    ALERT_STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(ALERT_STATE_FILE, 'w') as f:
        json.dump(state, f, indent=2)

def calculate_hrv_baseline(recovery_records):
    """Calculate 7-day HRV baseline"""
    hrv_values = []
    for rec in recovery_records[:7]:
        if 'score' in rec and 'hrv_rmssd_milli' in rec['score']:
            hrv_values.append(rec['score']['hrv_rmssd_milli'])
    if hrv_values:
        return sum(hrv_values) / len(hrv_values)
    return None

def check_alerts(data, state):
    """Check all alert conditions and return list of triggered alerts"""
    alerts = []
    today = datetime.now().strftime('%Y-%m-%d')
    
    if not data or not data.get('recovery'):
        return alerts
    
    # Get latest recovery
    latest_recovery = data['recovery'][0]
    latest_sleep = data['sleep'][0] if data.get('sleep') else None
    latest_cycle = data['cycles'][0] if data.get('cycles') else None
    
    if 'score' not in latest_recovery:
        return alerts
    
    rec_score = latest_recovery['score'].get('recovery_score', 0)
    hrv = latest_recovery['score'].get('hrv_rmssd_milli', 0)
    rhr = latest_recovery['score'].get('resting_heart_rate', 0)
    
    # Get sleep score
    sleep_score = 0
    if latest_sleep:
        sleep_score = latest_sleep.get('sleep_performance_percentage') or \
                      latest_sleep.get('score', {}).get('sleep_performance_percentage', 0)
    
    # Get strain
    strain = 0
    if latest_cycle and 'score' in latest_cycle:
        strain = latest_cycle['score'].get('strain', 0)
    
    # Alert 1: Critical Recovery (< 33% for 2+ days)
    low_recovery_days = 0
    for rec in data['recovery'][:2]:
        if 'score' in rec:
            if rec['score'].get('recovery_score', 100) < 33:
                low_recovery_days += 1
    
    if low_recovery_days >= 2:
        alert_key = f"critical_recovery_{today}"
        if state['last_alerts'].get('critical_recovery') != today:
            alerts.append({
                'type': 'critical_recovery',
                'severity': '🔴 CRITICAL',
                'title': 'Recovery Below 33% for 2+ Days',
                'message': f'Your recovery has been critically low for {low_recovery_days} consecutive days. Current: {rec_score}%. Prioritize rest and sleep.',
                'recommendation': 'Take a rest day. No intense workouts. Sleep 8+ hours tonight.'
            })
            state['last_alerts']['critical_recovery'] = today
    
    # Alert 2: HRV Drop (> 20% from baseline)
    baseline = calculate_hrv_baseline(data['recovery'])
    if baseline and baseline > 0:
        hrv_drop = (baseline - hrv) / baseline * 100
        if hrv_drop > 20:
            alert_key = f"hrv_drop_{today}"
            if state['last_alerts'].get('hrv_drop') != today:
                alerts.append({
                    'type': 'hrv_drop',
                    'severity': '📉 WARNING',
                    'title': f'HRV Dropped {hrv_drop:.1f}% from Baseline',
                    'message': f'Your HRV ({hrv:.1f} ms) is significantly below your 7-day baseline ({baseline:.1f} ms).',
                    'recommendation': 'Check stress levels, hydration, and alcohol intake. Consider meditation or breathwork.'
                })
                state['last_alerts']['hrv_drop'] = today
    
    # Alert 3: Poor Sleep (< 50% for 2+ nights)
    poor_sleep_nights = 0
    for sleep in data['sleep'][:2]:
        score = sleep.get('sleep_performance_percentage') or \
                sleep.get('score', {}).get('sleep_performance_percentage', 100)
        if score < 50:
            poor_sleep_nights += 1
    
    if poor_sleep_nights >= 2:
        if state['last_alerts'].get('poor_sleep') != today:
            alerts.append({
                'type': 'poor_sleep',
                'severity': '😴 WARNING',
                'title': 'Sleep Score Below 50% for 2+ Nights',
                'message': f'Your sleep quality has been poor for {poor_sleep_nights} consecutive nights.',
                'recommendation': 'Establish a consistent sleep schedule. Avoid screens 1 hour before bed. Consider magnesium supplement.'
            })
            state['last_alerts']['poor_sleep'] = today
    
    # Alert 4: Overtraining Risk (strain > 17, recovery < 40%)
    if strain > 17 and rec_score < 40:
        if state['last_alerts'].get('overtraining') != today:
            alerts.append({
                'type': 'overtraining',
                'severity': '⚠️ HIGH RISK',
                'title': 'Overtraining Risk Detected',
                'message': f'High strain ({strain:.1f}) with low recovery ({rec_score}%) is a risky combination.',
                'recommendation': 'Immediately reduce training intensity. Focus on recovery protocols: sleep, nutrition, hydration.'
            })
            state['last_alerts']['overtraining'] = today
    
    # Alert 5: Elevated RHR (> 10 bpm above personal baseline)
    # Using 60 as rough baseline - could be personalized
    if rhr > 75:
        if state['last_alerts'].get('elevated_rhr') != today:
            alerts.append({
                'type': 'elevated_rhr',
                'severity': '💓 NOTICE',
                'title': 'Elevated Resting Heart Rate',
                'message': f'Your RHR ({rhr} bpm) is elevated.',
                'recommendation': 'Check for illness, dehydration, or excessive caffeine. Monitor for continued elevation.'
            })
            state['last_alerts']['elevated_rhr'] = today
    
    return alerts

def send_alert_email(alerts):
    """Send email with triggered alerts"""
    if not alerts:
        return
    
    today = datetime.now().strftime('%A, %B %d, %Y')
    
    html_body = f"""<!DOCTYPE html>
<html>
<head>
<style>
body {{ font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; }}
.alert {{ background: #ffebee; padding: 15px; margin: 15px 0; border-left: 4px solid #e74c3c; border-radius: 5px; }}
.warning {{ background: #fff8e1; padding: 15px; margin: 15px 0; border-left: 4px solid #f39c12; border-radius: 5px; }}
.notice {{ background: #e3f2fd; padding: 15px; margin: 15px 0; border-left: 4px solid #2196f3; border-radius: 5px; }}
h1 {{ color: #e74c3c; }}
.severity {{ font-weight: bold; font-size: 14px; }}
.recommendation {{ background: #e8f5e9; padding: 10px; margin-top: 10px; border-radius: 3px; }}
</style>
</head>
<body>
<h1>🚨 Whoop Health Alerts — {today}</h1>
<p>The following health metrics have triggered alerts:</p>
"""
    
    for alert in alerts:
        css_class = 'alert' if 'CRITICAL' in alert['severity'] or 'RISK' in alert['severity'] else \
                    'warning' if 'WARNING' in alert['severity'] else 'notice'
        
        html_body += f"""
<div class="{css_class}">
<div class="severity">{alert['severity']}</div>
<h3>{alert['title']}</h3>
<p>{alert['message']}</p>
<div class="recommendation"><strong>Action:</strong> {alert['recommendation']}</div>
</div>
"""
    
    html_body += """
<hr>
<p><em>These alerts are automated based on your Whoop data. Adjust thresholds in whoop_alerts.py if needed.</em></p>
<p>🏛️ Cicero Health Monitor</p>
</body>
</html>"""
    
    # Write temp file and send
    temp_file = Path('/tmp/whoop_alerts_email.html')
    temp_file.write_text(html_body)
    
    import subprocess
    result = subprocess.run([
        'python3', str(EMAIL_SCRIPT),
        '--to', '[REDACTED]',
        '--subject', f'🚨 Whoop Health Alert — {len(alerts)} Issue(s) Detected',
        '--body-file', str(temp_file),
        '--html'
    ], capture_output=True, text=True)
    
    return result.returncode == 0

def main():
    print(f"[{datetime.now()}] Checking Whoop alerts...")
    
    # Load state
    state = load_alert_state()
    
    # Fetch latest data
    data = fetch_latest_whoop()
    if not data:
        print("Failed to fetch Whoop data")
        return
    
    # Check for alerts
    alerts = check_alerts(data, state)
    
    if alerts:
        print(f"Triggered {len(alerts)} alert(s):")
        for alert in alerts:
            print(f"  - {alert['severity']}: {alert['title']}")
        
        # Send email
        if send_alert_email(alerts):
            print("Alert email sent successfully")
        else:
            print("Failed to send alert email")
    else:
        print("No alerts triggered")
    
    # Save state
    save_alert_state(state)
    print("Done.")

if __name__ == '__main__':
    main()
