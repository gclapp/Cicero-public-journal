#!/usr/bin/env python3
"""
Whoop Daily Data Fetcher - Fetches all Whoop data and saves to file
Run via cron daily at 7:30 AM PT
"""

import requests
import json
import os
from datetime import datetime, timedelta
from pathlib import Path

TOKEN_FILE = Path.home() / '.whoop_token'
DATA_DIR = Path.home() / '.openclaw' / 'workspace' / 'data' / 'whoop'
LOG_FILE = Path.home() / '.openclaw' / 'workspace' / 'logs' / 'whoop-fetch.log'

def log(msg):
    ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f'[{ts}] {msg}')
    with open(LOG_FILE, 'a') as f:
        f.write(f'[{ts}] {msg}\n')

def get_token():
    if TOKEN_FILE.exists():
        return TOKEN_FILE.read_text().strip()
    return os.getenv('WHOOP_API_TOKEN', '')

def fetch_whoop_data():
    token = get_token()
    if not token:
        log('❌ No Whoop token found')
        return False
    
    headers = {'Authorization': f'Bearer {token}'}
    BASE_URL = 'https://api.prod.whoop.com/developer/v2'
    
    try:
        # Fetch recovery (most recent 7 days)
        recovery_resp = requests.get(f'{BASE_URL}/recovery', headers=headers, params={'limit': 7})
        recovery_resp.raise_for_status()
        recovery_data = recovery_resp.json()
        
        # Fetch sleep
        sleep_resp = requests.get(f'{BASE_URL}/activity/sleep', headers=headers, params={'limit': 7})
        sleep_resp.raise_for_status()
        sleep_data = sleep_resp.json()
        
        # Fetch workouts
        workout_resp = requests.get(f'{BASE_URL}/activity/workout', headers=headers, params={'limit': 7})
        workout_resp.raise_for_status()
        workout_data = workout_resp.json()
        
        # Fetch cycles
        cycle_resp = requests.get(f'{BASE_URL}/cycle', headers=headers, params={'limit': 7})
        cycle_resp.raise_for_status()
        cycle_data = cycle_resp.json()
        
        return {
            'recovery': recovery_data.get('records', []),
            'sleep': sleep_data.get('records', []),
            'workouts': workout_data.get('records', []),
            'cycles': cycle_data.get('records', [])
        }
        
    except Exception as e:
        log(f'❌ Error fetching Whoop data: {e}')
        return False

def save_data(data):
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    
    today = datetime.now().strftime('%Y-%m-%d')
    
    # Save full data
    data_file = DATA_DIR / f'whoop-{today}.json'
    with open(data_file, 'w') as f:
        json.dump(data, f, indent=2)
    
    # Generate summary
    latest_recovery = data['recovery'][0] if data['recovery'] else None
    latest_sleep = data['sleep'][0] if data['sleep'] else None
    
    if latest_recovery and 'score' in latest_recovery:
        rec_score = latest_recovery['score'].get('recovery_score', 'N/A')
        hrv = latest_recovery['score'].get('hrv_rmssd_milli', 'N/A')
        rhr = latest_recovery['score'].get('resting_heart_rate', 'N/A')
    else:
        rec_score = hrv = rhr = 'N/A'
    
    if latest_sleep:
        # Handle different API versions
        if 'sleep_performance_percentage' in latest_sleep:
            sleep_score = latest_sleep['sleep_performance_percentage']
        elif 'score' in latest_sleep and isinstance(latest_sleep['score'], dict):
            sleep_score = latest_sleep['score'].get('sleep_performance_percentage', 'N/A')
        else:
            sleep_score = 'N/A'
        
        # Get sleep duration
        if 'stage_summary' in latest_sleep:
            bed_time = latest_sleep['stage_summary'].get('total_in_bed_time_milli', 0)
        else:
            bed_time = latest_sleep.get('total_in_bed_time_milli', 0)
        
        hours = bed_time // 3600000
        minutes = (bed_time % 3600000) // 60000
        
        if 'sleep_efficiency_percentage' in latest_sleep:
            efficiency = latest_sleep['sleep_efficiency_percentage']
        elif 'score' in latest_sleep and isinstance(latest_sleep['score'], dict):
            efficiency = latest_sleep['score'].get('sleep_efficiency_percentage', 0)
        else:
            efficiency = 0
    else:
        sleep_score = 'N/A'
        hours = minutes = 0
        efficiency = 0
    
    summary = f"""## Whoop Daily Summary - {today}

**Recovery:** {rec_score}%
- HRV: {hrv} ms
- RHR: {rhr} bpm

**Sleep:** {sleep_score}%
- Duration: {hours}h {minutes}m
- Efficiency: {efficiency:.1f}%

**Workouts:** {len(data['workouts'])} recorded
"""
    
    summary_file = DATA_DIR / 'latest-summary.txt'
    with open(summary_file, 'w') as f:
        f.write(summary)
    
    log(f'✅ Whoop data saved: Recovery {rec_score}%, Sleep {sleep_score}%')
    return True

if __name__ == '__main__':
    log('Starting Whoop daily fetch...')
    data = fetch_whoop_data()
    if data:
        save_data(data)
    else:
        log('❌ Failed to fetch Whoop data')
