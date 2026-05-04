#!/usr/bin/env python3
"""
Vitus - Health Agent Core Monitor
Fetches Whoop data, analyzes trends, generates recommendations
"""

import json
import requests
from pathlib import Path
from datetime import datetime, timedelta

# Paths
TOKEN_FILE = Path.home() / '.whoop_token'
DATA_DIR = Path.home() / '.openclaw' / 'workspace' / 'data' / 'whoop'
MEMORY_DIR = Path.home() / '.openclaw' / 'workspace' / 'agents' / 'health-agent' / 'memory'
EMAIL_SCRIPT = Path.home() / '.openclaw' / 'workspace' / 'scripts' / 'send_email.py'

class VitusHealthMonitor:
    def __init__(self):
        self.memory_dir = MEMORY_DIR
        self.memory_dir.mkdir(parents=True, exist_ok=True)
        
    def get_token(self):
        if TOKEN_FILE.exists():
            return TOKEN_FILE.read_text().strip()
        return None
    
    def fetch_whoop_data(self, days=7):
        """Fetch Whoop data for analysis"""
        token = self.get_token()
        if not token:
            return None
        
        headers = {'Authorization': f'Bearer {token}'}
        BASE_URL = 'https://api.prod.whoop.com/developer/v2'
        
        try:
            recovery = requests.get(f'{BASE_URL}/recovery', headers=headers, params={'limit': days})
            recovery.raise_for_status()
            
            sleep = requests.get(f'{BASE_URL}/activity/sleep', headers=headers, params={'limit': days})
            sleep.raise_for_status()
            
            cycles = requests.get(f'{BASE_URL}/cycle', headers=headers, params={'limit': days})
            cycles.raise_for_status()
            
            workouts = requests.get(f'{BASE_URL}/activity/workout', headers=headers, params={'limit': days})
            workouts.raise_for_status()
            
            return {
                'recovery': recovery.json().get('records', []),
                'sleep': sleep.json().get('records', []),
                'cycles': cycles.json().get('records', []),
                'workouts': workouts.json().get('records', [])
            }
        except Exception as e:
            print(f"Error fetching Whoop: {e}")
            return None
    
    def analyze_recovery_trend(self, recovery_data):
        """Analyze 7-day recovery trend"""
        if not recovery_data or len(recovery_data) < 3:
            return None
        
        scores = []
        for rec in recovery_data[:7]:
            if 'score' in rec and 'recovery_score' in rec['score']:
                scores.append(rec['score']['recovery_score'])
        
        if not scores:
            return None
        
        avg = sum(scores) / len(scores)
        trend = "stable"
        if len(scores) >= 3:
            if scores[0] > scores[-1] + 10:
                trend = "improving"
            elif scores[0] < scores[-1] - 10:
                trend = "declining"
        
        red_days = sum(1 for s in scores if s < 33)
        yellow_days = sum(1 for s in scores if 33 <= s < 67)
        green_days = sum(1 for s in scores if s >= 67)
        
        return {
            'average': avg,
            'trend': trend,
            'latest': scores[0] if scores else 0,
            'red_days': red_days,
            'yellow_days': yellow_days,
            'green_days': green_days,
            'scores': scores
        }
    
    def analyze_hrv_trend(self, recovery_data):
        """Analyze HRV trend"""
        if not recovery_data:
            return None
        
        hrv_values = []
        for rec in recovery_data[:7]:
            if 'score' in rec and 'hrv_rmssd_milli' in rec['score']:
                hrv_values.append(rec['score']['hrv_rmssd_milli'])
        
        if not hrv_values:
            return None
        
        avg = sum(hrv_values) / len(hrv_values)
        latest = hrv_values[0]
        baseline = sum(hrv_values[1:]) / len(hrv_values[1:]) if len(hrv_values) > 1 else avg
        
        change_pct = ((latest - baseline) / baseline * 100) if baseline > 0 else 0
        
        return {
            'average': avg,
            'latest': latest,
            'baseline': baseline,
            'change_pct': change_pct,
            'values': hrv_values
        }
    
    def generate_workout_recommendation(self, recovery_analysis, hrv_analysis):
        """Generate workout recommendation based on recovery"""
        if not recovery_analysis:
            return "Unable to analyze recovery data"
        
        rec_score = recovery_analysis['latest']
        hrv_change = hrv_analysis['change_pct'] if hrv_analysis else 0
        
        if rec_score >= 67:
            if hrv_change > 5:
                return "🟢 EXCELLENT: Recovery strong and HRV improving. Full training load approved. Push for PRs."
            else:
                return "🟢 GOOD: Recovery green. Standard training load. Moderate intensity acceptable."
        elif rec_score >= 50:
            return "🟡 MODERATE: Recovery yellow. Reduce intensity by 20%. Focus on technique, not max effort."
        elif rec_score >= 33:
            if hrv_change < -10:
                return "🟡 CAUTION: Recovery yellow + HRV declining. Light activity only: walk, mobility, easy swim."
            else:
                return "🟡 MODERATE: Recovery yellow. Light to moderate workout. Avoid high intensity."
        else:
            return "🔴 REST DAY: Recovery critically low. No workout. Prioritize sleep, hydration, and active recovery only."
    
    def generate_daily_briefing(self):
        """Generate morning health briefing"""
        data = self.fetch_whoop_data(days=7)
        if not data:
            return None
        
        recovery_analysis = self.analyze_recovery_trend(data['recovery'])
        hrv_analysis = self.analyze_hrv_trend(data['recovery'])
        workout_rec = self.generate_workout_recommendation(recovery_analysis, hrv_analysis)
        
        today = datetime.now().strftime('%A, %B %d')
        
        briefing = f"""# 🫀 Vitus Daily Briefing — {today}

## 🔋 RECOVERY STATUS
"""
        
        if recovery_analysis:
            status_emoji = "🟢" if recovery_analysis['latest'] >= 67 else "🟡" if recovery_analysis['latest'] >= 33 else "🔴"
            briefing += f"""**Current Score:** {status_emoji} {recovery_analysis['latest']:.0f}%
**7-Day Average:** {recovery_analysis['average']:.0f}%
**Trend:** {recovery_analysis['trend'].title()}
**Zone Distribution:** {recovery_analysis['green_days']} green, {recovery_analysis['yellow_days']} yellow, {recovery_analysis['red_days']} red

"""
        
        if hrv_analysis:
            change_emoji = "📈" if hrv_analysis['change_pct'] > 5 else "📉" if hrv_analysis['change_pct'] < -10 else "➡️"
            briefing += f"""## ❤️ HRV STATUS
**Current:** {hrv_analysis['latest']:.1f} ms
**7-Day Average:** {hrv_analysis['average']:.1f} ms
**Change:** {change_emoji} {hrv_analysis['change_pct']:+.1f}%

"""
        
        briefing += f"""## 💪 WORKOUT RECOMMENDATION
{workout_rec}

---
*🫀 Vitus | Dedicated to your health*
"""
        
        return briefing
    
    def save_daily_log(self, briefing):
        """Save daily briefing to memory"""
        today = datetime.now().strftime('%Y-%m-%d')
        log_file = self.memory_dir / 'daily' / f'{today}.md'
        log_file.parent.mkdir(exist_ok=True)
        log_file.write_text(briefing)
    
    def send_daily_briefing(self):
        """Generate and send daily briefing email"""
        briefing = self.generate_daily_briefing()
        if not briefing:
            print("Failed to generate briefing")
            return False
        
        # Save to memory
        self.save_daily_log(briefing)
        
        # Convert to HTML for email
        html_body = f"""<!DOCTYPE html>
<html>
<head>
<style>
body {{ font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; line-height: 1.6; }}
h1 {{ color: #2c3e50; }}
h2 {{ color: #34495e; border-bottom: 1px solid #bdc3c7; padding-bottom: 5px; }}
.green {{ color: #27ae60; }}
.yellow {{ color: #f39c12; }}
.red {{ color: #e74c3c; }}
</style>
</head>
<body>
{briefing.replace('🟢', '<span class="green">🟢</span>').replace('🟡', '<span class="yellow">🟡</span>').replace('🔴', '<span class="red">🔴</span>')}
</body>
</html>"""
        
        temp_file = Path('/tmp/vitus_briefing.html')
        temp_file.write_text(html_body)
        
        import subprocess
        result = subprocess.run([
            'python3', str(EMAIL_SCRIPT),
            '--to', '[REDACTED]',
            '--subject', f'🫀 Vitus Daily Briefing — {datetime.now().strftime("%A, %B %d")}',
            '--body-file', str(temp_file),
            '--html'
        ], capture_output=True, text=True)
        
        return result.returncode == 0

if __name__ == '__main__':
    vitus = VitusHealthMonitor()
    print("Generating daily briefing...")
    if vitus.send_daily_briefing():
        print("Daily briefing sent successfully")
    else:
        print("Failed to send briefing")
