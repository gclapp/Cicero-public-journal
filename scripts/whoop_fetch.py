#!/usr/bin/env python3
"""
Whoop Data Fetcher - Daily Automation with whoopy library
Handles OAuth2 token refresh and pulls recovery/sleep/strain data
"""

import json
import os
from pathlib import Path
from datetime import datetime, timedelta
import whoopy
from whoopy.utils.auth import TokenInfo

# Configuration
CREDENTIALS_DIR = Path.home() / ".openclaw" / "credentials"
WHOOP_CONFIG = CREDENTIALS_DIR / "whoop-config.json"
WHOOP_TOKENS = CREDENTIALS_DIR / "whoop-tokens.json"
OUTPUT_DIR = Path.home() / ".openclaw" / "workspace" / "data" / "whoop"

def load_config():
    """Load Whoop app credentials"""
    if not WHOOP_CONFIG.exists():
        print("❌ Whoop config not found.")
        return None
    
    with open(WHOOP_CONFIG, 'r') as f:
        return json.load(f)

def load_tokens():
    """Load existing tokens"""
    if not WHOOP_TOKENS.exists():
        return None
    
    with open(WHOOP_TOKENS, 'r') as f:
        return json.load(f)

def fetch_whoop_data():
    """Fetch yesterday's Whoop data using whoopy library"""
    config = load_config()
    tokens = load_tokens()
    
    if not config or not tokens:
        print("❌ Missing config or tokens")
        return None
    
    # Create token info for whoopy
    scope_str = tokens.get('scope', '')
    scopes_list = scope_str.split() if scope_str else []
    
    token_info = TokenInfo(
        access_token=tokens['access_token'],
        refresh_token=tokens.get('refresh_token'),
        expires_in=tokens.get('expires_in', 3600),
        scopes=scopes_list,
        token_type=tokens.get('token_type', 'bearer')
    )
    
    # Create client with auto-refresh
    client = whoopy.WhoopClient(
        token_info=token_info,
        client_id=config['client_id'],
        client_secret=config['client_secret'],
        redirect_uri=config['redirect_uri'],
        auto_refresh_token=True
    )
    
    # Get yesterday's date
    yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
    yesterday_dt = datetime.now() - timedelta(days=1)
    
    try:
        print(f"📊 Fetching Whoop data for {yesterday}...")
        
        # Get cycles (daily summary) - filter by date
        cycle_list = []
        try:
            for c in client.cycles.iterate():
                if hasattr(c, 'start') and c.start:
                    cycle_date = c.start.strftime('%Y-%m-%d') if isinstance(c.start, datetime) else str(c.start)[:10]
                    if cycle_date == yesterday:
                        cycle_list.append({
                            'date': cycle_date,
                            'strain': c.strain if hasattr(c, 'strain') else None,
                            'kilojoules': c.kilojoules if hasattr(c, 'kilojoules') else None,
                        })
        except Exception as e:
            print(f"  ⚠️ Cycle fetch error: {e}")
        
        # Get sleep data - filter by date
        sleep_list = []
        try:
            for s in client.sleep.iterate():
                if hasattr(s, 'start') and s.start:
                    sleep_date = s.start.strftime('%Y-%m-%d') if isinstance(s.start, datetime) else str(s.start)[:10]
                    if sleep_date == yesterday:
                        sleep_data = {
                            'date': sleep_date,
                            'score': s.score.sleep_performance_percentage if hasattr(s, 'score') and s.score else None,
                            'total_sleep_time': s.score.stage_summary.total_sleep_time_milli // 1000 if hasattr(s, 'score') and s.score and s.score.stage_summary else None,
                            'efficiency': s.score.sleep_efficiency_percentage if hasattr(s, 'score') and s.score else None,
                            'respiratory_rate': s.score.respiratory_rate if hasattr(s, 'score') and s.score else None,
                        }
                        sleep_list.append(sleep_data)
        except Exception as e:
            print(f"  ⚠️ Sleep fetch error: {e}")
        
        # Get workouts - filter by date
        workout_list = []
        try:
            for w in client.workouts.iterate():
                if hasattr(w, 'start') and w.start:
                    workout_date = w.start.strftime('%Y-%m-%d') if isinstance(w.start, datetime) else str(w.start)[:10]
                    if workout_date == yesterday:
                        workout_data = {
                            'date': workout_date,
                            'sport_name': w.sport_name if hasattr(w, 'sport_name') else 'Workout',
                            'strain': w.score.strain if hasattr(w, 'score') and w.score else None,
                            'calories': w.score.calories if hasattr(w, 'score') and w.score else None,
                            'avg_hr': w.score.average_heart_rate if hasattr(w, 'score') and w.score else None,
                            'max_hr': w.score.max_heart_rate if hasattr(w, 'score') and w.score else None,
                        }
                        workout_list.append(workout_data)
        except Exception as e:
            print(f"  ⚠️ Workouts fetch error: {e}")
        
        # Get recovery data - this endpoint might not work
        recovery_list = []
        try:
            for r in client.recovery.iterate():
                if hasattr(r, 'start') and r.start:
                    rec_date = r.start.strftime('%Y-%m-%d') if isinstance(r.start, datetime) else str(r.start)[:10]
                    if rec_date == yesterday:
                        recovery_data = {
                            'date': rec_date,
                            'score': r.score if hasattr(r, 'score') else None,
                            'resting_hr': r.resting_heart_rate if hasattr(r, 'resting_heart_rate') else None,
                            'hrv': r.hrv if hasattr(r, 'hrv') else None,
                        }
                        recovery_list.append(recovery_data)
        except Exception as e:
            print(f"  ⚠️ Recovery fetch error (may be unavailable): {e}")
        
        data = {
            'date': yesterday,
            'timestamp': datetime.now().isoformat(),
            'recovery': recovery_list,
            'sleep': sleep_list,
            'workouts': workout_list,
            'cycles': cycle_list
        }
        
        # Save to file
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        output_file = OUTPUT_DIR / f"whoop-{yesterday}.json"
        with open(output_file, 'w') as f:
            json.dump(data, f, indent=2)
        
        print(f"✅ Data saved to {output_file}")
        print(f"   Recovery: {len(recovery_list)} entries")
        print(f"   Sleep: {len(sleep_list)} entries")
        print(f"   Workouts: {len(workout_list)} entries")
        print(f"   Cycles: {len(cycle_list)} entries")
        
        # Save updated tokens if refreshed
        if client.token_info:
            updated_tokens = {
                'access_token': client.token_info.access_token,
                'refresh_token': client.token_info.refresh_token,
                'expires_in': client.token_info.expires_in,
                'scope': ' '.join(client.token_info.scopes) if client.token_info.scopes else '',
                'token_type': client.token_info.token_type
            }
            with open(WHOOP_TOKENS, 'w') as f:
                json.dump(updated_tokens, f, indent=2)
        
        return data
        
    except Exception as e:
        print(f"❌ Error fetching data: {e}")
        import traceback
        traceback.print_exc()
        return None
    finally:
        client.close()

def generate_daily_summary(data):
    """Generate human-readable summary"""
    if not data:
        return "No Whoop data available."
    
    summary = f"""## Whoop Daily Summary - {data['date']}

"""
    
    # Recovery
    if data.get('recovery') and len(data['recovery']) > 0:
        rec = data['recovery'][0]
        recovery_score = rec.get('score', 'N/A')
        summary += f"**Recovery:** {recovery_score}%\n"
        
        resting_hr = rec.get('resting_hr')
        if resting_hr:
            summary += f"- Resting HR: {resting_hr} bpm\n"
        hrv = rec.get('hrv')
        if hrv:
            summary += f"- HRV: {hrv} ms\n"
    else:
        summary += "**Recovery:** No data\n"
    
    # Sleep
    if data.get('sleep') and len(data['sleep']) > 0:
        slp = data['sleep'][0]
        sleep_score = slp.get('score', 'N/A')
        summary += f"\n**Sleep:** {sleep_score}%\n"
        
        total_sleep = slp.get('total_sleep_time')
        if total_sleep:
            hours = total_sleep // 3600
            minutes = (total_sleep % 3600) // 60
            summary += f"- Duration: {hours}h {minutes}m\n"
        
        efficiency = slp.get('efficiency')
        if efficiency:
            summary += f"- Efficiency: {efficiency:.1f}%\n"
        
        resp_rate = slp.get('respiratory_rate')
        if resp_rate:
            summary += f"- Respiratory Rate: {resp_rate:.1f} bpm\n"
    else:
        summary += "\n**Sleep:** No data\n"
    
    # Workouts
    if data.get('workouts') and len(data['workouts']) > 0:
        summary += f"\n**Workouts:** {len(data['workouts'])}\n"
        for w in data['workouts'][:3]:
            name = w.get('sport_name', 'Workout')
            strain = w.get('strain', 'N/A')
            calories = w.get('calories', 0)
            summary += f"- {name}: Strain {strain:.2f}, {calories:.0f} cal\n"
    else:
        summary += "\n**Workouts:** No data\n"
    
    # Cycles/Strain
    if data.get('cycles') and len(data['cycles']) > 0:
        cyc = data['cycles'][0]
        day_strain = cyc.get('strain', 'N/A')
        if day_strain:
            summary += f"\n**Day Strain:** {day_strain:.2f}\n"
    
    return summary

def main():
    """Main function"""
    print("🏃 Whoop Data Fetcher")
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Fetch data
    data = fetch_whoop_data()
    
    if data:
        print()
        print(generate_daily_summary(data))
        
        # Save summary for morning updates
        summary_file = OUTPUT_DIR / "latest-summary.txt"
        with open(summary_file, 'w') as f:
            f.write(generate_daily_summary(data))
        
        print(f"\n💾 Summary saved to {summary_file}")
    else:
        print("❌ Failed to fetch Whoop data")

if __name__ == "__main__":
    main()
