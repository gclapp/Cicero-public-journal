#!/usr/bin/env python3
"""
Vitus - Health Agent Core Monitor
Fetches Whoop data, analyzes trends, generates recommendations
Expanded for proactive coaching system
"""

import json
import requests
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any

# Paths
TOKEN_FILE = Path.home() / '.whoop_token'
REFRESH_TOKEN_FILE = Path.home() / '.whoop_refresh_token'
DATA_DIR = Path.home() / '.openclaw' / 'workspace' / 'data' / 'whoop'
MEMORY_DIR = Path.home() / '.openclaw' / 'workspace' / 'agents' / 'health-agent' / 'memory'
EMAIL_SCRIPT = Path.home() / '.openclaw' / 'workspace' / 'scripts' / 'send_email.py'

BASE_URL = 'https://api.prod.whoop.com/developer/v2'

class VitusHealthMonitor:
    def __init__(self):
        self.memory_dir = MEMORY_DIR
        self.memory_dir.mkdir(parents=True, exist_ok=True)
        self.data_dir = DATA_DIR
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
    def get_token(self):
        if TOKEN_FILE.exists():
            return TOKEN_FILE.read_text().strip()
        return None
    
    def _refresh_token(self):
        """Refresh expired access token using refresh token"""
        if not REFRESH_TOKEN_FILE.exists():
            print("❌ No refresh token found")
            return False
        
        refresh_token = REFRESH_TOKEN_FILE.read_text().strip()
        if not refresh_token:
            print("❌ Refresh token is empty")
            return False
        
        try:
            # Refresh token endpoint
            data = {
                "grant_type": "refresh_token",
                "refresh_token": refresh_token
            }
            
            response = requests.post("https://api.prod.whoop.com/oauth/oauth2/token", data=data)
            
            if response.status_code == 200:
                token_data = response.json()
                new_access_token = token_data.get("access_token")
                new_refresh_token = token_data.get("refresh_token")
                
                # Save new tokens
                TOKEN_FILE.write_text(new_access_token)
                if new_refresh_token:
                    REFRESH_TOKEN_FILE.write_text(new_refresh_token)
                
                print("✅ Whoop token auto-refreshed successfully")
                return True
            else:
                print(f"❌ Token refresh failed: {response.status_code} - {response.text[:200]}")
                return False
                
        except Exception as e:
            print(f"❌ Error refreshing token: {e}")
            return False
    
    def fetch_whoop_data(self, days=14):
        """Fetch Whoop data - uses locally cached data from whoop_daily_fetch.py"""
        today = datetime.now().strftime('%Y-%m-%d')
        cache_file = self.data_dir / f'whoop-{today}.json'
        
        if cache_file.exists():
            try:
                with open(cache_file, 'r') as f:
                    data = json.load(f)
                print(f"Loaded Whoop data from cache: {cache_file}")
                return data
            except Exception as e:
                print(f"Error loading cached data: {e}")
        
        # Try to fetch fresh data via API
        print("Cache not found, attempting API fetch...")
        token = self.get_token()
        if not token:
            return None
        
        headers = {'Authorization': f'Bearer {token}'}
        BASE_URL = 'https://api.prod.whoop.com/developer/v2'
        
        try:
            recovery = requests.get(f'{BASE_URL}/recovery', headers=headers, params={'limit': days})
            
            # If 401, try to refresh token and retry once
            if recovery.status_code == 401:
                print("🔄 Token expired (401), attempting auto-refresh...")
                if self._refresh_token():
                    # Update headers with new token
                    token = self.get_token()
                    headers = {'Authorization': f'Bearer {token}'}
                    recovery = requests.get(f'{BASE_URL}/recovery', headers=headers, params={'limit': days})
                else:
                    raise ValueError("Token refresh failed")
            
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
            # Last resort: try to load any recent cached file
            try:
                json_files = sorted(self.data_dir.glob('whoop-*.json'), reverse=True)
                if json_files:
                    with open(json_files[0], 'r') as f:
                        data = json.load(f)
                    print(f"Loaded fallback data from: {json_files[0]}")
                    return data
            except Exception as e2:
                print(f"Fallback load also failed: {e2}")
            return None
    
    def get_latest_data(self) -> Dict[str, Any]:
        """Get the most recent day's complete data"""
        data = self.fetch_whoop_data(days=7)
        if not data:
            return {}
        
        latest = {
            'recovery': data['recovery'][0] if data.get('recovery') else None,
            'sleep': data['sleep'][0] if data.get('sleep') else None,
            'workouts': [],
            'cycles': data['cycles'][0] if data.get('cycles') else None
        }
        
        # Get today's workouts (if any)
        if data.get('workouts'):
            today = datetime.now().strftime('%Y-%m-%d')
            for workout in data['workouts']:
                workout_date = workout.get('start', '')[:10]
                if workout_date == today:
                    latest['workouts'].append(workout)
        
        return latest
    
    def extract_recovery_metrics(self, recovery_data: List[Dict]) -> Dict[str, Any]:
        """Extract comprehensive recovery metrics"""
        if not recovery_data:
            return {}
        
        scores = []
        hrv_values = []
        rhr_values = []
        spo2_values = []
        skin_temp_values = []
        
        for rec in recovery_data[:14]:  # Last 14 days
            if 'score' in rec:
                score = rec['score']
                if 'recovery_score' in score:
                    scores.append(score['recovery_score'])
                if 'hrv_rmssd_milli' in score:
                    hrv_values.append(score['hrv_rmssd_milli'])
                if 'resting_heart_rate' in score:
                    rhr_values.append(score['resting_heart_rate'])
                if 'spo2_percentage' in score:
                    spo2_values.append(score['spo2_percentage'])
                if 'skin_temp_celsius' in score:
                    skin_temp_values.append(score['skin_temp_celsius'])
        
        if not scores:
            return {}
        
        # Calculate trends
        latest = scores[0] if scores else 0
        baseline = sum(scores[1:7]) / len(scores[1:7]) if len(scores) > 1 else latest
        trend = "stable"
        if len(scores) >= 3:
            if scores[0] > scores[min(2, len(scores)-1)] + 10:
                trend = "improving"
            elif scores[0] < scores[min(2, len(scores)-1)] - 10:
                trend = "declining"
        
        # Zone distribution (last 7 days)
        red_days = sum(1 for s in scores[:7] if s < 33)
        yellow_days = sum(1 for s in scores[:7] if 33 <= s < 67)
        green_days = sum(1 for s in scores[:7] if s >= 67)
        
        # HRV analysis
        hrv_latest = hrv_values[0] if hrv_values else None
        hrv_baseline = sum(hrv_values[1:7]) / len(hrv_values[1:7]) if len(hrv_values) > 1 else hrv_latest
        hrv_change_pct = ((hrv_latest - hrv_baseline) / hrv_baseline * 100) if hrv_baseline and hrv_baseline > 0 else 0
        
        # RHR analysis
        rhr_latest = rhr_values[0] if rhr_values else None
        rhr_baseline = sum(rhr_values[1:7]) / len(rhr_values[1:7]) if len(rhr_values) > 1 else rhr_latest
        rhr_change_pct = ((rhr_latest - rhr_baseline) / rhr_baseline * 100) if rhr_baseline and rhr_baseline > 0 else 0
        
        return {
            'latest_score': latest,
            'average_7d': sum(scores[:7]) / len(scores[:7]) if scores else 0,
            'trend': trend,
            'red_days': red_days,
            'yellow_days': yellow_days,
            'green_days': green_days,
            'scores': scores,
            'hrv': {
                'latest': hrv_latest,
                'baseline': hrv_baseline,
                'change_pct': hrv_change_pct,
                'values': hrv_values
            },
            'rhr': {
                'latest': rhr_latest,
                'baseline': rhr_baseline,
                'change_pct': rhr_change_pct,
                'values': rhr_values
            },
            'spo2': {
                'latest': spo2_values[0] if spo2_values else None,
                'average': sum(v for v in spo2_values if v is not None) / len([v for v in spo2_values if v is not None]) if spo2_values and any(v is not None for v in spo2_values) else None
            },
            'skin_temp': {
                'latest': skin_temp_values[0] if skin_temp_values else None,
                'average': sum(v for v in skin_temp_values if v is not None) / len([v for v in skin_temp_values if v is not None]) if skin_temp_values and any(v is not None for v in skin_temp_values) else None
            }
        }
    
    def extract_sleep_metrics(self, sleep_data: List[Dict]) -> Dict[str, Any]:
        """Extract comprehensive sleep metrics including stages"""
        if not sleep_data:
            return {}
        
        latest = sleep_data[0]
        score = latest.get('score', {})
        stage_summary = score.get('stage_summary', {})
        
        # Convert milliseconds to hours/minutes
        def ms_to_hm(ms):
            if not ms:
                return (0, 0)
            hours = ms // 3600000
            minutes = (ms % 3600000) // 60000
            return (hours, minutes)
        
        in_bed_ms = stage_summary.get('total_in_bed_time_milli', 0)
        awake_ms = stage_summary.get('total_awake_time_milli', 0)
        light_ms = stage_summary.get('total_light_sleep_time_milli', 0)
        deep_ms = stage_summary.get('total_slow_wave_sleep_time_milli', 0)
        rem_ms = stage_summary.get('total_rem_sleep_time_milli', 0)
        
        in_bed_h, in_bed_m = ms_to_hm(in_bed_ms)
        awake_h, awake_m = ms_to_hm(awake_ms)
        light_h, light_m = ms_to_hm(light_ms)
        deep_h, deep_m = ms_to_hm(deep_ms)
        rem_h, rem_m = ms_to_hm(rem_ms)
        
        # Calculate percentages
        total_sleep_ms = light_ms + deep_ms + rem_ms
        sleep_pct = {
            'light': (light_ms / total_sleep_ms * 100) if total_sleep_ms > 0 else 0,
            'deep': (deep_ms / total_sleep_ms * 100) if total_sleep_ms > 0 else 0,
            'rem': (rem_ms / total_sleep_ms * 100) if total_sleep_ms > 0 else 0
        }
        
        # Sleep efficiency
        efficiency = score.get('sleep_efficiency_percentage', 0)
        performance = score.get('sleep_performance_percentage', 0)
        consistency = score.get('sleep_consistency_percentage', 0)
        
        # Respiratory rate
        respiratory_rate = score.get('respiratory_rate', 0)
        
        # Disturbances
        disturbances = stage_summary.get('disturbance_count', 0)
        sleep_cycles = stage_summary.get('sleep_cycle_count', 0)
        
        return {
            'in_bed': {'hours': in_bed_h, 'minutes': in_bed_m, 'total_ms': in_bed_ms},
            'awake': {'hours': awake_h, 'minutes': awake_m, 'total_ms': awake_ms},
            'light_sleep': {'hours': light_h, 'minutes': light_m, 'total_ms': light_ms, 'pct': sleep_pct['light']},
            'deep_sleep': {'hours': deep_h, 'minutes': deep_m, 'total_ms': deep_ms, 'pct': sleep_pct['deep']},
            'rem_sleep': {'hours': rem_h, 'minutes': rem_m, 'total_ms': rem_ms, 'pct': sleep_pct['rem']},
            'efficiency': efficiency,
            'performance': performance,
            'consistency': consistency,
            'respiratory_rate': respiratory_rate,
            'disturbances': disturbances,
            'sleep_cycles': sleep_cycles
        }
    
    def extract_workout_metrics(self, workout_data: List[Dict]) -> Dict[str, Any]:
        """Extract comprehensive workout metrics including zones"""
        if not workout_data:
            return {'recent': [], 'today': []}
        
        today = datetime.now().strftime('%Y-%m-%d')
        yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        
        recent_workouts = []
        today_workouts = []
        
        for workout in workout_data[:7]:  # Last 7 workouts
            score = workout.get('score', {})
            zone_durations = score.get('zone_durations', {})
            
            # Convert zone durations from ms to minutes
            zones = {
                'zone_0': zone_durations.get('zone_zero_milli', 0) / 60000,
                'zone_1': zone_durations.get('zone_one_milli', 0) / 60000,
                'zone_2': zone_durations.get('zone_two_milli', 0) / 60000,
                'zone_3': zone_durations.get('zone_three_milli', 0) / 60000,
                'zone_4': zone_durations.get('zone_four_milli', 0) / 60000,
                'zone_5': zone_durations.get('zone_five_milli', 0) / 60000
            }
            
            workout_info = {
                'id': workout.get('id'),
                'sport': workout.get('sport_name', 'activity'),
                'start': workout.get('start'),
                'strain': score.get('strain', 0),
                'avg_hr': score.get('average_heart_rate', 0),
                'max_hr': score.get('max_heart_rate', 0),
                'kilojoules': score.get('kilojoule', 0),
                'calories': score.get('kilojoule', 0) * 0.239,  # Convert kJ to kcal
                'distance_m': score.get('distance_meter'),
                'altitude_gain_m': score.get('altitude_gain_meter'),
                'zones': zones,
                'zone_minutes': sum(zones.values())
            }
            
            workout_date = workout.get('start', '')[:10]
            recent_workouts.append(workout_info)
            
            if workout_date == today:
                today_workouts.append(workout_info)
        
        return {
            'recent': recent_workouts,
            'today': today_workouts,
            'count_7d': len(recent_workouts)
        }
    
    def extract_strain_metrics(self, cycle_data: List[Dict]) -> Dict[str, Any]:
        """Extract strain metrics from cycles"""
        if not cycle_data:
            return {}
        
        strains = []
        kilojoules = []
        
        for cycle in cycle_data[:7]:
            if 'score' in cycle:
                score = cycle['score']
                if 'strain' in score:
                    strains.append(score['strain'])
                if 'kilojoule' in score:
                    kilojoules.append(score['kilojoule'])
        
        if not strains:
            return {}
        
        latest_strain = strains[0]
        avg_strain = sum(strains) / len(strains)
        
        return {
            'latest': latest_strain,
            'average_7d': avg_strain,
            'values': strains,
            'kilojoules_7d': sum(kilojoules) if kilojoules else 0,
            'calories_7d': sum(kilojoules) * 0.239 if kilojoules else 0
        }
    
    def analyze_recovery_trend(self, recovery_data):
        """Legacy method - kept for compatibility"""
        metrics = self.extract_recovery_metrics(recovery_data)
        if not metrics:
            return None
        
        return {
            'average': metrics['average_7d'],
            'trend': metrics['trend'],
            'latest': metrics['latest_score'],
            'red_days': metrics['red_days'],
            'yellow_days': metrics['yellow_days'],
            'green_days': metrics['green_days'],
            'scores': metrics['scores']
        }
    
    def analyze_hrv_trend(self, recovery_data):
        """Legacy method - kept for compatibility"""
        metrics = self.extract_recovery_metrics(recovery_data)
        if not metrics or not metrics.get('hrv'):
            return None
        
        hrv = metrics['hrv']
        return {
            'average': sum(hrv['values']) / len(hrv['values']) if hrv['values'] else 0,
            'latest': hrv['latest'],
            'baseline': hrv['baseline'],
            'change_pct': hrv['change_pct'],
            'values': hrv['values']
        }
    
    def generate_workout_recommendation(self, recovery_analysis, hrv_analysis):
        """Legacy method - kept for compatibility"""
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
        """Generate morning health briefing - legacy format"""
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
    
    def _markdown_to_html(self, markdown_text):
        """Convert markdown to HTML with proper formatting"""
        import re
        
        html = markdown_text
        
        # Convert headers
        html = re.sub(r'^# (.+)$', r'<h1>\1</h1>', html, flags=re.MULTILINE)
        html = re.sub(r'^## (.+)$', r'<h2>\1</h2>', html, flags=re.MULTILINE)
        html = re.sub(r'^### (.+)$', r'<h3>\1</h3>', html, flags=re.MULTILINE)
        
        # Convert bold
        html = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', html)
        
        # Convert italic
        html = re.sub(r'\*(.+?)\*', r'<em>\1</em>', html)
        
        # Convert line breaks to <br> or <p> tags
        paragraphs = html.split('\n\n')
        formatted_paragraphs = []
        for p in paragraphs:
            p = p.strip()
            if not p:
                continue
            # Don't wrap headers in <p> tags
            if p.startswith('<h'):
                formatted_paragraphs.append(p)
            else:
                # Replace single newlines with <br>
                p = p.replace('\n', '<br>\n')
                formatted_paragraphs.append(f'<p>{p}</p>')
        
        html = '\n\n'.join(formatted_paragraphs)
        
        # Wrap in HTML document
        html_doc = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<style>
body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; line-height: 1.6; color: #333; background: #f5f5f5; }}
.container {{ background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
h1 {{ color: #2c3e50; margin-top: 0; padding-bottom: 10px; border-bottom: 2px solid #3498db; }}
h2 {{ color: #34495e; border-bottom: 1px solid #bdc3c7; padding-bottom: 8px; margin-top: 25px; }}
h3 {{ color: #7f8c8d; }}
strong {{ color: #2c3e50; }}
p {{ margin: 12px 0; }}
.green {{ color: #27ae60; font-weight: bold; }}
.yellow {{ color: #f39c12; font-weight: bold; }}
.red {{ color: #e74c3c; font-weight: bold; }}
hr {{ border: none; border-top: 1px solid #ecf0f1; margin: 20px 0; }}
.footer {{ color: #95a5a6; font-size: 0.9em; margin-top: 30px; padding-top: 15px; border-top: 1px solid #ecf0f1; }}
</style>
</head>
<body>
<div class="container">
{html}
</div>
</body>
</html>"""
        
        return html_doc

    def send_daily_briefing(self):
        """Generate and send daily briefing email"""
        briefing = self.generate_daily_briefing()
        if not briefing:
            print("Failed to generate briefing")
            return False
        
        # Save to memory
        self.save_daily_log(briefing)
        
        # Convert markdown to HTML
        html_body = self._markdown_to_html(briefing)
        
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