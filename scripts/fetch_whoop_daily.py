#!/usr/bin/env python3
"""
Daily Whoop data fetcher - Fetches yesterday's health data and saves summary
Run via cron every morning at 6:30 AM PT (before morning check-in)
"""

import os
import sys
import json
from datetime import datetime, timedelta
from pathlib import Path

# Add skill scripts to path
sys.path.insert(0, '/home/ubuntu/.openclaw/workspace/skills/whoop-openclaw-skill/scripts')

from whoop_client import WhoopClient

DATA_DIR = Path("/home/ubuntu/.openclaw/workspace/data/whoop")
SUMMARY_FILE = DATA_DIR / "latest-summary.txt"
TOKEN_FILE = Path("/home/ubuntu/.openclaw/credentials/whoop-tokens.json")

def save_daily_summary():
    """Fetch yesterday's Whoop data and save summary"""
    
    try:
        # Use custom token file location
        client = WhoopClient(token_file=str(TOKEN_FILE))
        
        # Get yesterday's data (most recent complete day)
        today = datetime.now().date()
        yesterday = today - timedelta(days=1)
        
        # Fetch data
        recovery = client.get_recovery(start_date=yesterday, end_date=today, limit=1)
        sleep = client.get_sleep(start_date=yesterday, end_date=today, limit=1)
        cycle = client.get_cycle(start_date=yesterday, end_date=today, limit=1)
        workouts = client.get_workout(start_date=yesterday, end_date=today, limit=10)
        
        # Extract latest records
        recovery_record = recovery.get('records', [{}])[0] if recovery.get('records') else {}
        sleep_record = sleep.get('records', [{}])[0] if sleep.get('records') else {}
        cycle_record = cycle.get('records', [{}])[0] if cycle.get('records') else {}
        workout_records = workouts.get('records', []) if workouts else []
        
        # Build summary
        summary_lines = [f"## Whoop Daily Summary - {yesterday.isoformat()}", ""]
        
        # Recovery
        if recovery_record:
            score = recovery_record.get('score', {})
            recovery_score = score.get('recovery_score', 'N/A')
            hrv = score.get('hrv_rmssd_milli', 'N/A')
            rhr = score.get('resting_heart_rate', 'N/A')
            
            summary_lines.append(f"**Recovery:** {recovery_score}%")
            summary_lines.append(f"- HRV: {hrv} ms")
            summary_lines.append(f"- RHR: {rhr} bpm")
            summary_lines.append("")
        else:
            summary_lines.append("**Recovery:** No data")
            summary_lines.append("")
        
        # Sleep
        if sleep_record:
            score = sleep_record.get('score', {})
            performance = score.get('sleep_performance_percentage', 'N/A')
            duration_ms = score.get('total_in_bed_time_milli', 0)
            hours = duration_ms / (1000 * 60 * 60) if duration_ms else 0
            efficiency = score.get('sleep_efficiency_percentage', 'N/A')
            
            summary_lines.append(f"**Sleep:** {performance}%")
            summary_lines.append(f"- Duration: {hours:.1f} hours")
            summary_lines.append(f"- Efficiency: {efficiency}%")
            summary_lines.append("")
        else:
            summary_lines.append("**Sleep:** No data")
            summary_lines.append("")
        
        # Strain/Workouts
        if cycle_record:
            score = cycle_record.get('score', {})
            strain = score.get('strain', 'N/A')
            calories = score.get('kilojoule', 0) / 4.184 if score.get('kilojoule') else 0
            
            summary_lines.append(f"**Strain:** {strain}")
            summary_lines.append(f"- Calories: {calories:.0f} kcal")
        else:
            summary_lines.append("**Strain:** No data")
        
        # Workouts
        if workout_records:
            summary_lines.append("")
            summary_lines.append(f"**Workouts:** {len(workout_records)}")
            for w in workout_records[:3]:  # Top 3 workouts
                score = w.get('score', {})
                sport = w.get('sport', 'Unknown')
                workout_strain = score.get('strain', 'N/A')
                calories = score.get('kilojoule', 0) / 4.184 if score.get('kilojoule') else 0
                summary_lines.append(f"- {sport}: Strain {workout_strain}, {calories:.0f} cal")
        
        summary = "\n".join(summary_lines)
        
        # Save summary
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        with open(SUMMARY_FILE, 'w') as f:
            f.write(summary)
        
        # Also save full JSON for historical tracking
        json_file = DATA_DIR / f"whoop-{yesterday.isoformat()}.json"
        with open(json_file, 'w') as f:
            json.dump({
                'date': yesterday.isoformat(),
                'recovery': recovery_record,
                'sleep': sleep_record,
                'cycle': cycle_record,
                'workouts': workout_records
            }, f, indent=2)
        
        print(f"✅ Whoop data saved for {yesterday}")
        print(summary)
        return True
        
    except Exception as e:
        error_msg = f"❌ Error fetching Whoop data: {e}"
        print(error_msg, file=sys.stderr)
        
        # Save error state
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        with open(SUMMARY_FILE, 'w') as f:
            f.write(f"## Whoop Daily Summary - {datetime.now().date().isoformat()}\n\n**Error:** {e}\n\nPlease check Whoop OAuth token.")
        
        return False

if __name__ == "__main__":
    success = save_daily_summary()
    sys.exit(0 if success else 1)
