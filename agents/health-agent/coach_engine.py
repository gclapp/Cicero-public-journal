#!/usr/bin/env python3
"""
Vitus 2.0 - World-Class Health Coaching Engine
Gripping, actionable, visual coaching with color-coded risk levels
"""

import json
import re
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict

from health_monitor import VitusHealthMonitor
from data_collection import VitusDataCollection


@dataclass
class CoachingInsight:
    category: str
    severity: str  # red, yellow, green, info
    title: str
    message: str
    action: str
    priority: int = 5  # 1-10, higher = more important
    data_point: Optional[Dict] = None


class VitusCoachEngine:
    """World-class health coach - gripping, actionable, visual"""
    
    # Color codes for HTML emails
    COLORS = {
        'red': '#e74c3c',
        'yellow': '#f39c12',
        'green': '#27ae60',
        'blue': '#3498db',
        'purple': '#9b59b6',
        'dark': '#2c3e50',
        'gray': '#7f8c8d',
        'light_gray': '#ecf0f1',
        'bg_green': '#d5f5e3',
        'bg_yellow': '#fef9e7',
        'bg_red': '#fadbd8',
    }
    
    # Risk level definitions
    RISK_LEVELS = {
        'red': {'emoji': '🔴', 'label': 'CRITICAL', 'color': '#e74c3c', 'bg': '#fadbd8'},
        'yellow': {'emoji': '🟡', 'label': 'CAUTION', 'color': '#f39c12', 'bg': '#fef9e7'},
        'green': {'emoji': '🟢', 'label': 'OPTIMAL', 'color': '#27ae60', 'bg': '#d5f5e3'},
        'blue': {'emoji': '🔵', 'label': 'INFO', 'color': '#3498db', 'bg': '#ebf5fb'},
    }
    
    def __init__(self):
        self.monitor = VitusHealthMonitor()
        self.data = VitusDataCollection()
        self.memory_dir = Path.home() / '.openclaw' / 'workspace' / 'agents' / 'health-agent' / 'memory'
        self.memory_dir.mkdir(parents=True, exist_ok=True)
        self.patterns_file = self.memory_dir / 'patterns.json'
        self.history_file = self.memory_dir / 'history.json'
    
    def _progress_bar(self, percent: float, color: str = 'blue', width: int = 200) -> str:
        """Generate an HTML progress bar"""
        bar_color = self.COLORS.get(color, self.COLORS['blue'])
        filled_width = int((percent / 100) * width)
        return f'<div style="width:{width}px;height:20px;background:#ecf0f1;border-radius:10px;overflow:hidden;margin:5px 0;"><div style="width:{filled_width}px;height:100%;background:{bar_color};border-radius:10px;"></div></div><div style="font-size:12px;color:#7f8c8d;">{percent:.0f}%</div>'
    
    def _risk_badge(self, level: str, text: str = None) -> str:
        risk = self.RISK_LEVELS.get(level, self.RISK_LEVELS['blue'])
        display_text = text or risk['label']
        bg = risk['bg']
        color = risk['color']
        emoji = risk['emoji']
        return f'<span style="background:{bg};color:{color};padding:4px 12px;border-radius:12px;font-weight:bold;font-size:12px;border:1px solid {color}">{emoji} {display_text}</span>'
    
    def _metric_card(self, title: str, value: str, unit: str = '', risk_level: str = 'blue', trend: str = None) -> str:
        risk = self.RISK_LEVELS.get(risk_level, self.RISK_LEVELS['blue'])
        trend_html = f'<div style="font-size:14px;margin-top:5px;">{trend}</div>' if trend else ''
        color = risk['color']
        return f'<div style="background:white;border-left:4px solid {color};padding:15px;margin:10px 0;border-radius:0 8px 8px 0;box-shadow:0 1px 3px rgba(0,0,0,0.1);"><div style="font-size:12px;color:#7f8c8d;text-transform:uppercase;letter-spacing:1px;">{title}</div><div style="font-size:28px;font-weight:bold;color:{color};margin:5px 0;">{value}<span style="font-size:16px;color:#7f8c8d;">{unit}</span></div>{self._risk_badge(risk_level)}{trend_html}</div>'
    
    def _action_box(self, title: str, actions: List[str], priority: str = 'high') -> str:
        colors = {
            'high': {'bg': '#fadbd8', 'border': '#e74c3c', 'text': '#c0392b'},
            'medium': {'bg': '#fef9e7', 'border': '#f39c12', 'text': '#d68910'},
            'low': {'bg': '#d5f5e3', 'border': '#27ae60', 'text': '#27ae60'},
        }
        c = colors.get(priority, colors['medium'])
        bg = c['bg']
        border = c['border']
        text = c['text']
        actions_html = ''.join([f'<li style="margin:8px 0;color:{c["text"]}">{a}</li>' for a in actions])
        return f'<div style="background:{bg};border:1px solid {border};border-radius:8px;padding:15px;margin:15px 0;"><div style="font-weight:bold;color:{text};margin-bottom:10px;font-size:16px;">▶ {title}</div><ul style="margin:0;padding-left:20px;">{actions_html}</ul></div>'
    
    def analyze_hrv_decline(self, recovery_metrics: Dict) -> Optional[CoachingInsight]:
        hrv = recovery_metrics.get('hrv', {})
        if not hrv:
            return None
        change_pct = hrv.get('change_pct', 0)
        if change_pct < -20:
            return CoachingInsight('recovery', 'red', 'HRV CRASH', 'Your nervous system is under serious stress.', 'Complete rest day. No training. Prioritize sleep.', 10, {'hrv_change': change_pct})
        elif change_pct < -10:
            return CoachingInsight('recovery', 'yellow', 'HRV Declining', 'Your recovery capacity is dropping.', 'Reduce training load. Early bedtime tonight.', 7, {'hrv_change': change_pct})
        elif change_pct > 10:
            return CoachingInsight('recovery', 'green', 'HRV Improving', 'Your body is adapting well.', 'Great recovery habits. You can push harder today.', 4, {'hrv_change': change_pct})
        return None
    
    def analyze_recovery_streak(self, recovery_metrics: Dict) -> Optional[CoachingInsight]:
        scores = recovery_metrics.get('scores', [])
        if len(scores) < 3:
            return None
        red_streak = sum(1 for s in scores[:5] if s < 33)
        if red_streak >= 3:
            return CoachingInsight('recovery', 'red', 'OVERTRAINING ALERT', f'{red_streak} days in the red. Your body is breaking down.', 'MANDATORY rest until recovery improves. No exceptions.', 10, {'red_streak': red_streak})
        elif red_streak == 2:
            return CoachingInsight('recovery', 'yellow', 'Recovery Warning', 'Two red days in a row.', 'Light activity only. Sleep 8+ hours tonight.', 8, {'red_streak': red_streak})
        green_streak = sum(1 for s in scores[:5] if s >= 67)
        if green_streak >= 5:
            return CoachingInsight('recovery', 'green', 'Recovery Streak!', f'{green_streak} days of green recovery.', 'Excellent habits. Cleared for high-intensity training.', 3, {'green_streak': green_streak})
        return None
    
    def analyze_sleep_quality(self, sleep_metrics: Dict) -> Optional[CoachingInsight]:
        if not sleep_metrics:
            return None
        in_bed = sleep_metrics.get('in_bed', {})
        total_hours = in_bed.get('hours', 0) + in_bed.get('minutes', 0) / 60
        if total_hours < 5:
            return CoachingInsight('sleep', 'red', 'CRITICAL SLEEP DEBT', f'Only {in_bed.get("hours", 0)}h {in_bed.get("minutes", 0)}m in bed.', 'Tonight: bed by 9:30 PM. No screens. Consider a nap.', 10, {'sleep_hours': total_hours})
        elif total_hours < 6:
            return CoachingInsight('sleep', 'yellow', 'Insufficient Sleep', f'{in_bed.get("hours", 0)}h {in_bed.get("minutes", 0)}m is below optimal.', 'Aim for 8+ hours tonight. Wind-down at 9:30 PM.', 7, {'sleep_hours': total_hours})
        elif total_hours >= 8:
            return CoachingInsight('sleep', 'green', 'Great Sleep', f'{in_bed.get("hours", 0)}h {in_bed.get("minutes", 0)}m — excellent.', 'Keep this consistency. Your recovery will benefit.', 2, {'sleep_hours': total_hours})
        return None
    
    def analyze_strain_recovery_balance(self, recovery_metrics: Dict, strain_metrics: Dict) -> Optional[CoachingInsight]:
        if not recovery_metrics or not strain_metrics:
            return None
        rec_score = recovery_metrics.get('latest_score', 0)
        strain_score = strain_metrics.get('latest', 0)
        if strain_score > 17 and rec_score < 40:
            return CoachingInsight('workout', 'red', 'STRAIN/RECOVERY MISMATCH', f'High strain ({strain_score:.1f}) with low recovery ({rec_score:.0f}%).', 'MANDATORY rest day. Light walking only.', 10, {'strain': strain_score, 'recovery': rec_score})
        if 12 <= strain_score <= 16 and rec_score >= 67:
            return CoachingInsight('workout', 'green', 'Perfect Training Balance', f'Optimal strain ({strain_score:.1f}) with excellent recovery ({rec_score:.0f}%).', 'You are in the sweet spot. Training load is perfect.', 2, {'strain': strain_score, 'recovery': rec_score})
        if strain_score < 8 and rec_score >= 80:
            return CoachingInsight('workout', 'blue', 'Ready to Push', f'Low strain ({strain_score:.1f}) with high recovery ({rec_score:.0f}%).', 'Well-rested and undertrained. Perfect for a challenging workout.', 4, {'strain': strain_score, 'recovery': rec_score})
        return None
    
    def generate_todays_mission(self, recovery_metrics: Dict, sleep_metrics: Dict, strain_metrics: Dict, user_data: Dict) -> Dict:
        rec_score = recovery_metrics.get('latest_score', 50)
        hrv_change = recovery_metrics.get('hrv', {}).get('change_pct', 0)
        
        if rec_score < 33:
            return {'title': 'MISSION: COMPLETE REST', 'subtitle': 'Your body is asking for recovery', 'priority': 'red', 'actions': ['No workout today — non-negotiable', 'In bed by 9:30 PM', 'Drink 3L water minimum', 'No alcohol, limit caffeine'], 'why': f'Recovery at {rec_score:.0f}% — pushing now would be counterproductive'}
        
        if sleep_metrics:
            total_hours = sleep_metrics.get('in_bed', {}).get('hours', 0) + sleep_metrics.get('in_bed', {}).get('minutes', 0) / 60
            if total_hours < 6:
                return {'title': 'MISSION: SLEEP CATCH-UP', 'subtitle': 'Tonight is about recovery', 'priority': 'yellow', 'actions': ['Nap if possible (20-30 min)', 'Screens off by 9 PM', 'Bed by 9:30 PM', 'Light activity only today'], 'why': f"Only {sleep_metrics['in_bed']['hours']}h sleep — prioritize tonight"}
        
        if hrv_change < -15:
            return {'title': 'MISSION: STRESS REDUCTION', 'subtitle': 'Your nervous system needs care', 'priority': 'yellow', 'actions': ['10-minute meditation this morning', 'No intense exercise', 'Early bedtime (10 PM)', 'Limit stimulants'], 'why': f'HRV down {abs(hrv_change):.0f}% — manage stress today'}
        
        if recovery_metrics.get('red_days', 0) >= 2:
            return {'title': 'MISSION: ACTIVE RECOVERY', 'subtitle': 'Break the red streak', 'priority': 'yellow', 'actions': ['30-minute easy walk', 'Stretching session (15 min)', 'Focus on sleep tonight', 'No strength training'], 'why': '2+ red days — time to back off'}
        
        strain_score = strain_metrics.get('latest', 0)
        if strain_score > 17 and rec_score < 60:
            return {'title': 'MISSION: REPLENISH', 'subtitle': 'Recover from yesterday\'s effort', 'priority': 'yellow', 'actions': ['Extra protein today (180g target)', '20-minute mobility work', 'Hydrate aggressively (3.5L)', 'Early bedtime'], 'why': f"Yesterday's strain ({strain_score:.1f}) needs recovery"}
        
        water = user_data.get('water', {})
        if water.get('percent_complete', 100) < 40:
            return {'title': 'MISSION: HYDRATION', 'subtitle': 'Water is your priority today', 'priority': 'yellow', 'actions': ['Drink 500ml water right now', 'Set hourly reminders', 'Carry a water bottle everywhere', 'Track every glass'], 'why': f"Only {water['percent_complete']:.0f}% of water goal — critical for recovery"}
        
        weekday = datetime.now().weekday()
        missions = {
            0: {'title': 'MISSION: STRENGTH FOCUS', 'subtitle': 'Start the week strong', 'priority': 'green', 'actions': ['Hit protein target (160g+)', 'Lift heavy if recovery allows', 'Set week intentions'], 'why': 'Monday strength sets the tone for the week'},
            1: {'title': 'MISSION: CARDIO DAY', 'subtitle': 'Build your aerobic base', 'priority': 'green', 'actions': ['30-40 min zone 2 cardio', 'Stay hydrated', 'Focus on form'], 'why': 'Tuesday cardio builds endurance'},
            2: {'title': 'MISSION: STRENGTH FOCUS', 'subtitle': 'Mid-week power session', 'priority': 'green', 'actions': ['Hit protein target (160g+)', 'Lift heavy', 'Track your weights'], 'why': 'Wednesday strength maintains momentum'},
            3: {'title': 'MISSION: ACTIVE RECOVERY', 'subtitle': 'Prepare for the weekend', 'priority': 'green', 'actions': ['Light movement', 'Meal prep for weekend', 'Early wind-down'], 'why': 'Thursday recovery sets up weekend performance'},
            4: {'title': 'MISSION: STRENGTH FOCUS', 'subtitle': 'Finish the week strong', 'priority': 'green', 'actions': ['Hit protein target (160g+)', 'Lift heavy if recovery allows', 'Plan weekend activity'], 'why': 'Friday strength caps the work week'},
            5: {'title': 'MISSION: FUN ACTIVITY', 'subtitle': 'Move because you enjoy it', 'priority': 'green', 'actions': ['Hike, sport, or outdoor activity', 'Make it social', 'No pressure on intensity'], 'why': 'Saturday is for joy in movement'},
            6: {'title': 'MISSION: WEEKLY RESET', 'subtitle': 'Prepare for next week', 'priority': 'green', 'actions': ['Meal prep', 'Review the week', 'Set sleep schedule for Monday'], 'why': 'Sunday preparation enables Monday success'}
        }
        return missions.get(weekday, missions[0])
    
    def generate_nutrition_plan(self, recovery_metrics: Dict, strain_metrics: Dict, loseit_data: Optional[Dict] = None) -> Dict:
        rec_score = recovery_metrics.get('latest_score', 50)
        strain_score = strain_metrics.get('latest', 10)
        base_cal = 2000
        cal_adj = 300 if strain_score > 15 else 150 if strain_score > 10 else 0
        protein = 180 if rec_score < 50 else 160
        carbs = 150 if rec_score < 50 else 200
        targets = {'calories': base_cal + cal_adj, 'protein': protein, 'carbs': carbs, 'fat': 65, 'hydration': '3-4 liters', 'focus': 'recovery' if rec_score < 50 else 'performance'}
        if loseit_data and loseit_data.get('food_calories'):
            targets['yesterday_actual'] = loseit_data['food_calories']
            targets['yesterday_deficit'] = targets['calories'] - loseit_data['food_calories']
        return targets
    
    def generate_sleep_prep(self, recovery_metrics: Dict, tomorrow_schedule: str = None) -> Dict:
        rec_score = recovery_metrics.get('latest_score', 50)
        if rec_score < 50:
            return {'priority': 'high', 'bedtime': '9:30 PM', 'actions': ['Last meal by 7 PM', 'No screens after 8:30 PM', 'Bedroom temp: 65-68°F', 'Consider magnesium supplement'], 'message': 'Your recovery needs priority sleep tonight.'}
        elif rec_score < 67:
            return {'priority': 'medium', 'bedtime': '10:00 PM', 'actions': ['Last meal by 7:30 PM', 'No screens after 9 PM', 'Bedroom temp: 65-68°F', 'Light stretching before bed'], 'message': 'Aim for 8+ hours to maintain recovery.'}
        else:
            return {'priority': 'normal', 'bedtime': '10:30 PM', 'actions': ['Last meal by 8 PM', 'No screens after 9:30 PM', 'Bedroom temp: 65-68°F'], 'message': 'Your recovery is strong. Maintain the habit.'}
    
    def generate_morning_briefing(self, loseit_data: Optional[Dict] = None) -> str:
        whoop_data = self.monitor.fetch_whoop_data(days=14)
        if not whoop_data:
            return self._generate_no_data_briefing()
        
        rec_metrics = self.monitor.extract_recovery_metrics(whoop_data.get('recovery', []))
        sleep_metrics = self.monitor.extract_sleep_metrics(whoop_data.get('sleep', []))
        strain_metrics = self.monitor.extract_strain_metrics(whoop_data.get('cycles', []))
        workout_metrics = self.monitor.extract_workout_metrics(whoop_data.get('workouts', []))
        user_data = self.data.get_today_metrics()
        
        insights = []
        for analyzer in [self.analyze_hrv_decline, self.analyze_recovery_streak, self.analyze_sleep_quality]:
            result = analyzer(rec_metrics if 'recovery' in analyzer.__name__ else sleep_metrics)
            if result:
                insights.append(result)
        strain_result = self.analyze_strain_recovery_balance(rec_metrics, strain_metrics)
        if strain_result:
            insights.append(strain_result)
        
        insights.sort(key=lambda x: x.priority, reverse=True)
        
        mission = self.generate_todays_mission(rec_metrics, sleep_metrics, strain_metrics, user_data)
        nutrition = self.generate_nutrition_plan(rec_metrics, strain_metrics, loseit_data)
        sleep_prep = self.generate_sleep_prep(rec_metrics)
        
        html = self._build_html_briefing(mission, rec_metrics, sleep_metrics, strain_metrics, workout_metrics, user_data, nutrition, insights, sleep_prep)
        
        self._save_to_history({'recovery': rec_metrics, 'sleep': sleep_metrics, 'strain': strain_metrics, 'mission': mission, 'insights': [asdict(i) for i in insights]})
        
        return html
    
    def _build_html_briefing(self, mission, rec_metrics, sleep_metrics, strain_metrics, workout_metrics, user_data, nutrition, insights, sleep_prep) -> str:
        today = datetime.now().strftime('%A, %B %d')
        rec_score = rec_metrics.get('latest_score', 0)
        
        # Mission section
        mission_html = f'<div style="background:{self.RISK_LEVELS[mission["priority"]]["bg"]};border:2px solid {self.RISK_LEVELS[mission["priority"]]["color"]};border-radius:12px;padding:20px;margin:20px 0;"><div style="font-size:24px;font-weight:bold;color:{self.RISK_LEVELS[mission["priority"]]["color"]};margin-bottom:5px;">{mission["title"]}</div><div style="font-size:16px;color:#2c3e50;margin-bottom:15px;">{mission["subtitle"]}</div><div style="font-size:14px;color:#7f8c8d;margin-bottom:15px;font-style:italic;">Why: {mission["why"]}</div>{self._action_box("Your Actions Today", mission["actions"], "high" if mission["priority"] == "red" else "medium" if mission["priority"] == "yellow" else "low")}</div>'
        
        # Status dashboard
        status_html = '<div style="display:grid;grid-template-columns:1fr 1fr;gap:10px;margin:20px 0;">'
        rec_risk = 'green' if rec_score >= 67 else 'yellow' if rec_score >= 33 else 'red'
        status_html += self._metric_card('Recovery', f"{rec_score:.0f}", '%', rec_risk, f"Trend: {rec_metrics.get('trend', 'stable').title()}")
        
        hrv = rec_metrics.get('hrv', {})
        if hrv:
            hrv_change = hrv.get('change_pct', 0)
            hrv_risk = 'green' if hrv_change > 5 else 'yellow' if hrv_change > -10 else 'red'
            status_html += self._metric_card('HRV', f"{hrv_change:+.0f}", '%', hrv_risk, f"Current: {hrv.get('latest', 0):.0f}ms")
        
        if sleep_metrics:
            sleep_hours = sleep_metrics.get('in_bed', {}).get('hours', 0)
            sleep_mins = sleep_metrics.get('in_bed', {}).get('minutes', 0)
            total_sleep = sleep_hours + sleep_mins / 60
            sleep_risk = 'green' if total_sleep >= 7 else 'yellow' if total_sleep >= 6 else 'red'
            status_html += self._metric_card('Sleep', f"{sleep_hours}", f"h {sleep_mins}m", sleep_risk)
        
        if strain_metrics:
            strain = strain_metrics.get('latest', 0)
            strain_risk = 'green' if 12 <= strain <= 16 else 'yellow'
            status_html += self._metric_card("Yesterday's Strain", f"{strain:.1f}", '', strain_risk)
        
        status_html += '</div>'
        
        # Water progress
        water = user_data.get('water', {})
        water_html = f'<div style="background:white;padding:15px;margin:15px 0;border-radius:8px;box-shadow:0 1px 3px rgba(0,0,0,0.1);"><div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:10px;"><span style="font-weight:bold;color:#2c3e50;">💧 Hydration</span><span style="color:#7f8c8d;">{water.get("total_ml", 0)}ml / {water.get("goal_ml", 3000)}ml</span></div>{self._progress_bar(water.get("percent_complete", 0), "green" if water.get("percent_complete", 0) >= 75 else "yellow" if water.get("percent_complete", 0) >= 40 else "red")}<div style="font-size:13px;color:#7f8c8d;margin-top:5px;">{self.data.get_water_recommendation()}</div></div>'
        
        # Nutrition section
        snacks = self.data.get_snack_suggestions()
        snacks_html = ''.join([f'<div style="padding:8px;margin:5px 0;background:#f8f9fa;border-radius:4px;"><strong>{s["name"]}</strong><br><span style="font-size:12px;color:#7f8c8d;">{s["calories"]} cal • {s["protein"]}g protein • {s["why"]}</span></div>' for s in snacks])
        
        nutrition_html = f'<div style="background:white;padding:15px;margin:15px 0;border-radius:8px;box-shadow:0 1px 3px rgba(0,0,0,0.1);"><div style="font-weight:bold;color:#2c3e50;margin-bottom:10px;">🍽️ Nutrition Targets</div><div style="display:grid;grid-template-columns:1fr 1fr;gap:10px;margin:10px 0;"><div>Calories: <strong>{nutrition["calories"]}</strong></div><div>Protein: <strong>{nutrition["protein"]}g</strong></div><div>Carbs: <strong>{nutrition["carbs"]}g</strong></div><div>Fat: <strong>{nutrition["fat"]}g</strong></div></div><div style="margin-top:15px;"><div style="font-weight:bold;color:#2c3e50;margin-bottom:5px;">💡 Smart Snacks</div>{snacks_html}</div></div>'
        
        # Sleep prep section
        sleep_html = f'<div style="background:{self.RISK_LEVELS["yellow" if sleep_prep["priority"] == "medium" else "red" if sleep_prep["priority"] == "high" else "green"]["bg"]};border:1px solid {self.RISK_LEVELS["yellow" if sleep_prep["priority"] == "medium" else "red" if sleep_prep["priority"] == "high" else "green"]["color"]};border-radius:8px;padding:15px;margin:15px 0;"><div style="font-weight:bold;color:#2c3e50;margin-bottom:10px;">🌙 Tonight: Sleep Prep</div><div style="font-size:14px;color:#7f8c8d;margin-bottom:10px;">{sleep_prep["message"]}</div><div style="font-weight:bold;margin:10px 0;">Target bedtime: {sleep_prep["bedtime"]}</div><ul style="margin:0;padding-left:20px;">{"".join([f"<li style=\"margin:5px 0;\">{a}</li>" for a in sleep_prep["actions"]])}</ul></div>'
        
        # Insights section
        insights_html = ''
        if insights:
            insights_list = []
            for ins in insights[:3]:  # Top 3 insights
                risk = self.RISK_LEVELS.get(ins.severity, self.RISK_LEVELS['blue'])
                insights_list.append(f'<div style="background:{risk["bg"]};border-left:4px solid {risk["color"]};padding:12px;margin:10px 0;border-radius:0 8px 8px 0;"><div style="font-weight:bold;color:{risk["color"]};margin-bottom:5px;">{ins.title}</div><div style="font-size:14px;color:#2c3e50;margin-bottom:5px;">{ins.message}</div><div style="font-size:13px;color:#7f8c8d;"><strong>Action:</strong> {ins.action}</div></div>')
            insights_html = '<div style="margin:20px 0;"><div style="font-weight:bold;color:#2c3e50;margin-bottom:10px;font-size:18px;">📊 Key Insights</div>' + ''.join(insights_list) + '</div>'
        
        # Complete HTML document
        html_doc = f'''<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Vitus Morning Briefing</title>
</head>
<body style="font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;margin:0;padding:20px;background:#f5f5f5;">
<div style="max-width:600px;margin:0 auto;background:white;border-radius:12px;overflow:hidden;box-shadow:0 4px 6px rgba(0,0,0,0.1);">
    <div style="background:linear-gradient(135deg, #667eea 0%, #764ba2 100%);padding:30px;text-align:center;">
        <div style="font-size:32px;margin-bottom:10px;">🫀</div>
        <div style="color:white;font-size:24px;font-weight:bold;">Vitus Morning Briefing</div>
        <div style="color:rgba(255,255,255,0.8);font-size:16px;margin-top:5px;">{today}</div>
    </div>
    <div style="padding:20px;">
        {mission_html}
        <div style="margin:20px 0;">
            <div style="font-weight:bold;color:#2c3e50;margin-bottom:10px;font-size:18px;">📈 Your Status</div>
            {status_html}
        </div>
        {water_html}
        {nutrition_html}
        {sleep_html}
        {insights_html}
    </div>
    <div style="background:#f8f9fa;padding:20px;text-align:center;border-top:1px solid #ecf0f1;">
        <div style="color:#7f8c8d;font-size:14px;">🫀 Vitus | Your World-Class Health Coach</div>
        <div style="color:#95a5a6;font-size:12px;margin-top:5px;">Data-driven. Action-oriented. Results-focused.</div>
    </div>
</div>
</body>
</html>'''
        
        return html_doc
    
    def _generate_no_data_briefing(self) -> str:
        return '''<!DOCTYPE html>
<html><head><meta charset="UTF-8"></head>
<body style="font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;margin:0;padding:20px;background:#f5f5f5;">
<div style="max-width:600px;margin:0 auto;background:white;border-radius:12px;padding:30px;text-align:center;">
    <div style="font-size:48px;margin-bottom:20px;">⚠️</div>
    <h2 style="color:#e74c3c;">Unable to Fetch Health Data</h2>
    <p style="color:#7f8c8d;">Your Whoop token may have expired. Please check the WHOOP_TOKEN_REFRESH.md file for instructions on refreshing your token.</p>
    <div style="margin-top:20px;padding:15px;background:#fadbd8;border-radius:8px;">
        <strong>Next Steps:</strong><br>
        1. Check agents/health-agent/WHOOP_TOKEN_REFRESH.md<br>
        2. Follow the web-based refresh method<br>
        3. Send the new token to [REDACTED]
    </div>
</div>
</body></html>'''
    
    def _save_to_history(self, data: Dict):
        history = []
        if self.history_file.exists():
            try:
                with open(self.history_file, 'r') as f:
                    history = json.load(f)
            except:
                pass
        history.append({'date': datetime.now().strftime('%Y-%m-%d'), **data})
        cutoff = (datetime.now() - timedelta(days=90)).strftime('%Y-%m-%d')
        history = [h for h in history if h.get('date', '') >= cutoff]
        with open(self.history_file, 'w') as f:
            json.dump(history, f, indent=2, default=str)
    
    def send_briefing_email(self, briefing: str, subject_suffix: str = "Morning Briefing"):
        EMAIL_SCRIPT = Path.home() / '.openclaw' / 'workspace' / 'scripts' / 'send_email.py'
        temp_file = Path('/tmp/vitus_briefing.html')
        temp_file.write_text(briefing)
        import subprocess
        result = subprocess.run(['python3', str(EMAIL_SCRIPT), '--to', '[REDACTED]',
                                '--subject', f'🫀 Vitus {subject_suffix} - {datetime.now().strftime("%A, %B %d")}',
                                '--body-file', str(temp_file), '--html'], capture_output=True, text=True)
        return result.returncode == 0


if __name__ == '__main__':
    import sys
    coach = VitusCoachEngine()
    
    if len(sys.argv) > 1:
        cmd = sys.argv[1]
        if cmd == 'morning':
            briefing = coach.generate_morning_briefing()
            print("Briefing generated. Sending email...")
            if coach.send_briefing_email(briefing):
                print("✅ Morning briefing sent successfully")
            else:
                print("❌ Failed to send briefing")
        else:
            print("Usage: python3 coach_engine.py [morning]")
    else:
        briefing = coach.generate_morning_briefing()
        print(briefing)