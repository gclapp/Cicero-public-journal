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
        'gray': {'emoji': '⚪', 'label': 'UNKNOWN', 'color': '#7f8c8d', 'bg': '#ecf0f1'},
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
        """AGGRESSIVE HRV monitoring - tighter thresholds, stronger language"""
        hrv = recovery_metrics.get('hrv', {})
        if not hrv:
            return None
        change_pct = hrv.get('change_pct', 0)
        current_hrv = hrv.get('latest', 0)
        
        # CRASH: Severe drop - nervous system is failing
        if change_pct < -25:
            return CoachingInsight('recovery', 'red', 'HRV SYSTEM CRASH', 
                f'Your autonomic nervous system is FAILING. HRV down {abs(change_pct):.0f}%. This is not sustainable.', 
                'STOP. Complete rest. No work stress. No training. Sleep 9+ hours tonight or you will break down.', 
                10, {'hrv_change': change_pct, 'current_hrv': current_hrv})
        
        # DANGER: Significant drop - heading toward overtraining
        if change_pct < -15:
            return CoachingInsight('recovery', 'red', 'HRV DANGER ZONE', 
                f'HRV down {abs(change_pct):.0f}%. Your recovery capacity is COLLAPSING. You are overreaching.', 
                'Cancel hard workouts. No intensity. Bed by 9 PM. One more red day and you are FORCED rest.', 
                9, {'hrv_change': change_pct, 'current_hrv': current_hrv})
        
        # WARNING: Moderate drop - trend is wrong
        if change_pct < -8:
            return CoachingInsight('recovery', 'yellow', 'HRV Declining - Fix This Now', 
                f'HRV down {abs(change_pct):.0f}%. Your body is struggling to recover. This trend will bite you.', 
                'Reduce training 50%. No late nights. No alcohol. Fix this today or it becomes a problem tomorrow.', 
                7, {'hrv_change': change_pct, 'current_hrv': current_hrv})
        
        # GOOD: Improving - reward the behavior
        if change_pct > 15:
            return CoachingInsight('recovery', 'green', 'HRV SURGING', 
                f'HRV up {change_pct:.0f}%. Your nervous system is THRIVING. Whatever you are doing, keep doing it.', 
                'You are bulletproof today. This is the day to push limits. Attack your hardest workout.', 
                3, {'hrv_change': change_pct, 'current_hrv': current_hrv})
        
        # STABLE: Slight improvement - acknowledge it
        if change_pct > 5:
            return CoachingInsight('recovery', 'green', 'HRV Improving', 
                f'HRV up {change_pct:.0f}%. Recovery trending positive. Good habits are paying off.', 
                'Solid position. You can train hard but do not be stupid. Sleep well tonight.', 
                4, {'hrv_change': change_pct, 'current_hrv': current_hrv})
        
        return None
    
    def analyze_hydration(self, water_data: Dict) -> Optional[CoachingInsight]:
        """Analyze hydration from Apple Health water data - AGGRESSIVE COACHING"""
        if not water_data or not water_data.get('available'):
            return None
        
        recent = water_data.get('data', [])
        if not recent:
            return None
        
        # Get today and yesterday
        today = recent[0] if recent else None
        yesterday = recent[1] if len(recent) > 1 else None
        
        if not today:
            return None
        
        today_oz = today.get('ounces', 0)
        yesterday_oz = yesterday.get('ounces', 0) if yesterday else 0
        target_oz = 80  # ~2.4L / 10 cups
        
        # CRITICAL: Two days of very low hydration
        if today_oz < 20 and yesterday_oz < 20:
            return CoachingInsight(
                'hydration', 'red', 'HYDRATION EMERGENCY',
                f'CRITICAL: {today_oz:.0f}oz today, {yesterday_oz:.0f}oz yesterday. Severe dehydration affects recovery, HRV, and cognitive function.',
                '1. Drink 32oz (1L) water NOW. 2. Set hourly phone reminders. 3. Add electrolytes. 4. Track every glass in Apple Health.',
                10, {'today_oz': today_oz, 'yesterday_oz': yesterday_oz, 'target_oz': target_oz}
            )
        
        # RED: Very low today
        if today_oz < 20:
            return CoachingInsight(
                'hydration', 'red', 'CRITICAL DEHYDRATION',
                f'Only {today_oz:.0f}oz today. Dehydration impairs recovery, sleep quality, and mental performance.',
                'Drink 24oz (3 cups) immediately. Carry a water bottle. Set 3 reminders today.',
                9, {'today_oz': today_oz, 'target_oz': target_oz}
            )
        
        # YELLOW: Below target for 2+ days
        if today_oz < 40 and yesterday_oz < 40 and yesterday_oz > 0:
            return CoachingInsight(
                'hydration', 'yellow', 'Hydration Warning',
                f'{today_oz:.0f}oz today, {yesterday_oz:.0f}oz yesterday. Two days below optimal impacts recovery capacity.',
                'Target 80oz today. Drink 16oz now, then 8oz every hour. Track in Apple Health.',
                8, {'today_oz': today_oz, 'yesterday_oz': yesterday_oz, 'target_oz': target_oz}
            )
        
        # YELLOW: Below target today
        if today_oz < 40:
            return CoachingInsight(
                'hydration', 'yellow', 'Low Hydration',
                f'{today_oz:.0f}oz so far — need 40+ more oz to reach target. Hydration directly affects HRV and recovery.',
                'Drink 16oz now. Have water with every meal. Goal: 80oz by bedtime.',
                7, {'today_oz': today_oz, 'target_oz': target_oz}
            )
        
        # YELLOW: Good but not optimal
        if today_oz < 60:
            return CoachingInsight(
                'hydration', 'yellow', 'Hydration On Track',
                f'{today_oz:.0f}oz — good progress but 20+ oz short of optimal.',
                f'Need {80 - today_oz:.0f}oz more. Drink 8oz now and you\'ll hit target.',
                5, {'today_oz': today_oz, 'target_oz': target_oz}
            )

    def analyze_steps(self, steps_data: Dict) -> Optional[CoachingInsight]:
        """AGGRESSIVE steps coaching - movement is non-negotiable"""
        if not steps_data or not steps_data.get('available'):
            return None
        
        recent = steps_data.get('data', [])
        if not recent:
            return None
        
        target = steps_data.get('target_steps', 10000)
        
        # Get today and yesterday
        today = recent[0] if recent else None
        yesterday = recent[1] if len(recent) > 1 else None
        
        if not today:
            return None
        
        today_steps = today.get('steps', 0)
        yesterday_steps = yesterday.get('steps', 0) if yesterday else 0
        
        # Calculate current hour for context (assume 8 PM = 20:00 if no time data)
        hour = datetime.now().hour
        expected_by_now = (hour / 24) * target if hour > 8 else target * 0.3
        
        # CRITICAL: Sedentary for 2+ days - major health risk
        if today_steps < 2000 and yesterday_steps < 2000 and yesterday_steps > 0:
            return CoachingInsight(
                'movement', 'red', 'SEDENTARY CRISIS',
                f'CRITICAL: Only {today_steps:,} steps today, {yesterday_steps:,} yesterday. You are sedentary. This destroys cardiovascular health, metabolism, and recovery.',
                '1. Walk 15 min RIGHT NOW. 2. Set hourly movement reminders. 3. Target 5k steps minimum today. 4. Tomorrow: 10k or you are in danger zone.',
                10, {'today_steps': today_steps, 'yesterday_steps': yesterday_steps, 'target': target}
            )
        
        # RED: Very low today (< 20% of goal by evening)
        if today_steps < 2000 and hour >= 18:
            return CoachingInsight(
                'movement', 'red', 'MOVEMENT EMERGENCY',
                f'Only {today_steps:,} steps and it is 6 PM. You are sedentary. This is not "rest" - this is self-harm.',
                'Walk 20 min NOW. Then another 20 min after dinner. Target 5k minimum. Do not go to bed with < 3k steps.',
                9, {'today_steps': today_steps, 'target': target, 'hour': hour}
            )
        
        # RED: Very low regardless of time
        if today_steps < 1500:
            return CoachingInsight(
                'movement', 'red', 'CRITICAL INACTIVITY',
                f'Only {today_steps:,} steps. Your body is designed to move. This level of inactivity accelerates aging and disease.',
                'Stand up NOW. Walk 10 min. Set phone reminders every hour. Target 5k today minimum. This is not optional.',
                9, {'today_steps': today_steps, 'target': target}
            )
        
        # YELLOW: Below 50% of goal by evening
        if today_steps < (target * 0.5) and hour >= 18:
            return CoachingInsight(
                'movement', 'yellow', 'Steps Behind - Catch Up',
                f'{today_steps:,} steps at 6 PM - you are {target - today_steps:,} short. Evening walk is mandatory.',
                '30-min walk after dinner. Take calls walking. Park far away. Do not fail today.',
                7, {'today_steps': today_steps, 'target': target, 'remaining': target - today_steps}
            )
        
        # YELLOW: Two days below target
        if today_steps < (target * 0.75) and yesterday_steps < (target * 0.75) and yesterday_steps > 0:
            return CoachingInsight(
                'movement', 'yellow', 'Steps Slipping - Fix This',
                f'{today_steps:,} today, {yesterday_steps:,} yesterday. Two days below 10k. You are getting sedentary.',
                'Hit 10k today no excuses. Morning walk, lunch walk, evening walk. Break it into chunks. Just move.',
                6, {'today_steps': today_steps, 'yesterday_steps': yesterday_steps, 'target': target}
            )
        
        # YELLOW: Below target but not terrible
        if today_steps < (target * 0.75):
            return CoachingInsight(
                'movement', 'yellow', 'Steps Low - Move More',
                f'{today_steps:,} steps - need {target - today_steps:,} more to hit 10k. Your body needs movement to recover.',
                f'You need {target - today_steps:,} more steps. 15-min walk = 2k steps. Do it 2-3 times today.',
                5, {'today_steps': today_steps, 'target': target, 'remaining': target - today_steps}
            )
        
        # GREEN: Hit target
        if today_steps >= target:
            return CoachingInsight(
                'movement', 'green', 'Steps Target Crushed',
                f'{today_steps:,} steps - target achieved! You moved like a human today. This supports recovery, metabolism, and longevity.',
                'Excellent! This level of movement supports everything - recovery, sleep, mood. Keep this consistency.',
                3, {'today_steps': today_steps, 'target': target}
            )
        
        # GREEN: Close to target
        if today_steps >= (target * 0.9):
            return CoachingInsight(
                'movement', 'green', 'Steps Strong',
                f'{today_steps:,} steps - almost there! Just {target - today_steps:,} more to hit 10k.',
                'So close! 5-min walk and you hit it. Finish strong.',
                4, {'today_steps': today_steps, 'target': target, 'remaining': target - today_steps}
            )
        
        return None
    
    def analyze_integrated_health(self, whoop_data: Dict, water_data: Dict, steps_data: Dict, nutrition_data: Dict = None) -> List[CoachingInsight]:
        """
        AGGRESSIVE integrated health analysis - looks at ALL data sources together
        This is where Vitus connects the dots and sees patterns across metrics
        """
        insights = []
        
        # Extract key metrics from raw Whoop data
        # whoop_data contains keys: 'recovery', 'sleep', 'workouts', 'cycles' which are lists
        rec_score = 50
        hrv_change = 0
        sleep_hours = 0
        
        if whoop_data:
            # Get latest recovery record
            recovery_records = whoop_data.get('recovery', [])
            if recovery_records and len(recovery_records) > 0:
                latest_recovery = recovery_records[0]
                score_data = latest_recovery.get('score', {})
                if isinstance(score_data, dict):
                    rec_score = score_data.get('recovery_score', 50)
                else:
                    rec_score = score_data if isinstance(score_data, (int, float)) else 50
                hrv_data = latest_recovery.get('hrv', {})
                if isinstance(hrv_data, dict):
                    hrv_change = hrv_data.get('change_pct', 0)
            
            # Get latest sleep record
            sleep_records = whoop_data.get('sleep', [])
            if sleep_records and len(sleep_records) > 0:
                latest_sleep = sleep_records[0]
                in_bed = latest_sleep.get('in_bed', {})
                if isinstance(in_bed, dict):
                    sleep_hours = in_bed.get('hours', 0) + in_bed.get('minutes', 0) / 60
        
        # Water data
        water_oz = 0
        if water_data and water_data.get('available') and water_data.get('data'):
            water_oz = water_data['data'][0].get('ounces', 0)
        
        # Steps data
        steps = 0
        if steps_data and steps_data.get('available') and steps_data.get('data'):
            steps = steps_data['data'][0].get('steps', 0)
        
        # Nutrition data
        protein = 0
        calories = 0
        if nutrition_data and nutrition_data.get('entries'):
            latest_nutrition = nutrition_data['entries'][-1]  # Most recent
            protein = latest_nutrition.get('macros', {}).get('protein', 0)
            calories = latest_nutrition.get('food_calories', 0)
        
        # === INTEGRATED ANALYSIS ===
        
        # CRISIS: Multiple systems failing
        crisis_count = sum([
            rec_score < 33,
            sleep_hours < 5,
            water_oz < 20,
            steps < 2000
        ])
        
        if crisis_count >= 3:
            insights.append(CoachingInsight(
                'integrated', 'red', 'SYSTEMS COLLAPSE - EMERGENCY',
                f'CRITICAL: Recovery {rec_score:.0f}%, Sleep {sleep_hours:.1f}h, Water {water_oz:.0f}oz, Steps {steps:,}. THREE+ systems are failing. You are in freefall.',
                '1. STOP everything non-essential. 2. Drink 1L water NOW. 3. Walk 15 min. 4. Sleep 9+ hours tonight. 5. Eat 150g protein. This is damage control.',
                10, {'crisis_count': crisis_count, 'rec_score': rec_score, 'sleep_hours': sleep_hours, 'water_oz': water_oz, 'steps': steps}
            ))
        elif crisis_count >= 2:
            insights.append(CoachingInsight(
                'integrated', 'red', 'MULTIPLE SYSTEMS FAILING',
                f'DANGER: {crisis_count} health systems are in crisis. Recovery {rec_score:.0f}%, Sleep {sleep_hours:.1f}h, Water {water_oz:.0f}oz, Steps {steps:,}. This is unsustainable.',
                'Immediate action required: Fix hydration (32oz now), move 3k steps minimum, sleep 8.5h tonight, eat clean. Do not let a third system fail.',
                9, {'crisis_count': crisis_count, 'rec_score': rec_score, 'sleep_hours': sleep_hours, 'water_oz': water_oz, 'steps': steps}
            ))
        
        # Poor recovery + poor sleep = disaster
        if rec_score < 40 and sleep_hours < 6:
            insights.append(CoachingInsight(
                'integrated', 'red', 'RECOVERY DEATH SPIRAL',
                f'Recovery {rec_score:.0f}% with only {sleep_hours:.1f}h sleep. You are not recovering. This pattern destroys performance and health.',
                'TONIGHT IS NON-NEGOTIABLE: Bed by 9 PM. No screens. No alcohol. No caffeine after 2 PM. Sleep 9 hours or tomorrow will be worse.',
                9, {'rec_score': rec_score, 'sleep_hours': sleep_hours}
            ))
        
        # Poor recovery + low protein = can't rebuild
        if rec_score < 50 and protein < 80 and protein > 0:
            insights.append(CoachingInsight(
                'integrated', 'yellow', 'RECOVERY WITHOUT FUEL',
                f'Recovery {rec_score:.0f}% but only {protein}g protein. Your body needs protein to rebuild. You are recovering blindfolded.',
                f'Hit 160g protein TODAY. You need {160 - protein}g more. Every meal needs 30g+ protein. Recovery without nutrition is wishful thinking.',
                7, {'rec_score': rec_score, 'protein': protein, 'protein_needed': 160 - protein}
            ))
        
        # Good recovery but sabotaging it
        if rec_score >= 67:
            sabotage_count = sum([
                water_oz < 40,
                sleep_hours < 7,
                steps < 5000,
                protein < 100 and protein > 0
            ])
            
            if sabotage_count >= 2:
                insights.append(CoachingInsight(
                    'integrated', 'yellow', 'WASTING GREEN RECOVERY',
                    f'Recovery is {rec_score:.0f}% (excellent!) but you are sabotaging it: Water {water_oz:.0f}oz, Sleep {sleep_hours:.1f}h, Steps {steps:,}, Protein {protein}g.',
                    'You have a GREEN LIGHT to train hard but you are wasting it. Fix the basics: hydrate, sleep 8h, hit protein target. Do not squander this advantage.',
                    6, {'rec_score': rec_score, 'water_oz': water_oz, 'sleep_hours': sleep_hours, 'steps': steps, 'protein': protein}
                ))
        
        # Low steps + low water = sedentary and dehydrated
        if steps < 5000 and water_oz < 40:
            insights.append(CoachingInsight(
                'integrated', 'red', 'SEDENTARY & DEHYDRATED',
                f'Only {steps:,} steps and {water_oz:.0f}oz water. You are sedentary AND dehydrated. This is a health emergency.',
                'Stand up NOW. Walk 10 min. Drink 24oz water. Set hourly movement reminders. This is not "rest" - this is self-harm. Fix both today.',
                8, {'steps': steps, 'water_oz': water_oz}
            ))
        
        # HRV crash + poor sleep = nervous system breakdown
        if hrv_change < -20 and sleep_hours < 6:
            insights.append(CoachingInsight(
                'integrated', 'red', 'NERVOUS SYSTEM BREAKDOWN',
                f'HRV down {abs(hrv_change):.0f}% with {sleep_hours:.1f}h sleep. Your autonomic nervous system is failing. This is serious.',
                'COMPLETE rest today. No training. No stress. Meditate 10 min. Sleep 9+ hours tonight. If HRV is still down tomorrow, take another rest day.',
                9, {'hrv_change': hrv_change, 'sleep_hours': sleep_hours}
            ))
        
        # High strain + low calories = under-fueled
        strain = whoop_data.get('cycles', [{}])[0].get('strain', 0) if whoop_data and whoop_data.get('cycles') else 0
        if strain > 15 and calories > 0 and calories < 1800:
            insights.append(CoachingInsight(
                'integrated', 'yellow', 'UNDER-FUELED FOR TRAINING',
                f'Strain {strain:.1f} yesterday but only {calories} calories. You trained hard but did not fuel recovery.',
                f'Eat {2200 - calories} more calories TODAY. Focus on carbs and protein. You cannot recover from high strain on low calories.',
                6, {'strain': strain, 'calories': calories, 'calories_needed': 2200 - calories}
            ))
        
        # Perfect day - all systems green
        perfect_count = sum([
            rec_score >= 67,
            sleep_hours >= 7.5,
            water_oz >= 80,
            steps >= 10000,
            protein >= 140
        ])
        
        if perfect_count >= 4:
            insights.append(CoachingInsight(
                'integrated', 'green', 'ALL SYSTEMS OPTIMAL - UNSTOPPABLE',
                f'Recovery {rec_score:.0f}%, Sleep {sleep_hours:.1f}h, Water {water_oz:.0f}oz, Steps {steps:,}, Protein {protein}g. You are firing on ALL cylinders.',
                'This is your day to attack. PRs are possible. You have earned this through discipline. Maintain this standard - it is elite-level.',
                2, {'rec_score': rec_score, 'sleep_hours': sleep_hours, 'water_oz': water_oz, 'steps': steps, 'protein': protein}
            ))
        
        return insights
    
    def analyze_recovery_streak(self, recovery_metrics: Dict) -> Optional[CoachingInsight]:
        """AGGRESSIVE recovery streak monitoring - zero tolerance for red streaks"""
        scores = recovery_metrics.get('scores', [])
        if len(scores) < 2:
            return None
        
        latest = scores[0] if scores else 50
        red_streak = sum(1 for s in scores[:7] if s < 33)
        yellow_streak = sum(1 for s in scores[:5] if s < 67)
        
        # CATASTROPHIC: 3+ red days - you are destroying yourself
        if red_streak >= 3:
            return CoachingInsight('recovery', 'red', 'OVERTRAINING CRISIS', 
                f'{red_streak} RED DAYS. You are not "tough" - you are self-destructing. Your hormones, immune system, and performance are compromised.', 
                'MANDATORY 3-day rest minimum. No gym. No intense cardio. Sleep 9+ hours. Eat perfectly. Or get injured/sick.', 
                10, {'red_streak': red_streak, 'latest_score': latest})
        
        # DANGER: 2 red days - stop now or face consequences
        if red_streak == 2:
            return CoachingInsight('recovery', 'red', 'RED STREAK - STOP NOW', 
                'Two red days. Your body is screaming at you. One more and you enter the danger zone.', 
                'TODAY IS REST. No exceptions. Light walk only. Bed by 9 PM. Tomorrow you either recover or crash.', 
                9, {'red_streak': red_streak, 'latest_score': latest})
        
        # WARNING: Single red day after greens - catch it early
        if latest < 33 and red_streak == 1:
            return CoachingInsight('recovery', 'yellow', 'RED DAY - Wake Up Call', 
                f'Recovery crashed to {latest:.0f}%. This is your body saying "back off" - listen now or pay later.', 
                'No hard training today. Mobility work only. Prioritize sleep tonight. Do not let this become a streak.', 
                8, {'red_streak': red_streak, 'latest_score': latest})
        
        # YELLOW WARNING: 3+ days below 67% - sliding toward red
        if yellow_streak >= 3 and latest < 67:
            return CoachingInsight('recovery', 'yellow', 'Recovery Sliding - Fix This', 
                f'{yellow_streak} days below optimal. You are not recovering fully. This leads to red days.', 
                'Reduce training 30%. No late nights. Perfect nutrition. Turn this around before it is too late.', 
                6, {'yellow_streak': yellow_streak, 'latest_score': latest})
        
        # EXCELLENT: 5+ green days - you are crushing it
        green_streak = sum(1 for s in scores[:7] if s >= 67)
        if green_streak >= 5:
            return CoachingInsight('recovery', 'green', 'GREEN STREAK - UNSTOPPABLE', 
                f'{green_streak} days of green recovery. You are a recovery MACHINE. This is elite-level discipline.', 
                'You have earned the right to push hard. Attack PRs. This is your window - use it.', 
                2, {'green_streak': green_streak, 'latest_score': latest})
        
        # GOOD: 3-4 green days - solid position
        if green_streak >= 3:
            return CoachingInsight('recovery', 'green', 'Recovery Strong', 
                f'{green_streak} green days. Your recovery game is on point. Keep the consistency.', 
                'Good position to train hard. Stay disciplined with sleep and nutrition.', 
                3, {'green_streak': green_streak, 'latest_score': latest})
        
        return None
    
    def analyze_sleep_quality(self, sleep_metrics: Dict) -> Optional[CoachingInsight]:
        """AGGRESSIVE sleep monitoring - sleep is non-negotiable"""
        if not sleep_metrics:
            return None
        
        in_bed = sleep_metrics.get('in_bed', {})
        total_hours = in_bed.get('hours', 0) + in_bed.get('minutes', 0) / 60
        sleep_needed = sleep_metrics.get('sleep_needed', {}).get('hours', 8)
        
        # CATASTROPHIC: < 5 hours - you are basically drunk
        if total_hours < 5:
            return CoachingInsight('sleep', 'red', 'SLEEP CRISIS - DANGER', 
                f'Only {in_bed.get("hours", 0)}h {in_bed.get("minutes", 0)}m sleep. Your cognitive function is impaired. Reaction time is worse than alcohol. You are a liability today.', 
                'NO important decisions. NO driving if tired. Nap 20-30 min NOW. Tonight: bed by 9 PM, no excuses. This is damage control.', 
                10, {'sleep_hours': total_hours, 'sleep_needed': sleep_needed})
        
        # DANGER: 5-6 hours - severe sleep debt accumulating
        if total_hours < 6:
            return CoachingInsight('sleep', 'red', 'SEVERE SLEEP DEBT', 
                f'{in_bed.get("hours", 0)}h {in_bed.get("minutes", 0)}m is NOT enough. You are building sleep debt that will crush your recovery and HRV.', 
                'Tonight: bed by 9 PM. No screens after 8:30 PM. No alcohol. Take this seriously or face red recovery tomorrow.', 
                9, {'sleep_hours': total_hours, 'sleep_needed': sleep_needed})
        
        # WARNING: 6-7 hours - below optimal, trending wrong
        if total_hours < 7:
            return CoachingInsight('sleep', 'yellow', 'Sleep Deficient - Fix Tonight', 
                f'{in_bed.get("hours", 0)}h {in_bed.get("minutes", 0)}m is below your need. This is why recovery is not optimal.', 
                'Tonight: bed by 9:30 PM. Wind-down starts at 9 PM. Do not let this become a pattern.', 
                7, {'sleep_hours': total_hours, 'sleep_needed': sleep_needed})
        
        # SUBOPTIMAL: 7-7.5 hours - okay but not great
        if total_hours < 7.5:
            return CoachingInsight('sleep', 'yellow', 'Sleep Adequate - Aim Higher', 
                f'{in_bed.get("hours", 0)}h {in_bed.get("minutes", 0)}m is okay, but 8+ hours is where magic happens.', 
                'Try for 8 hours tonight. The difference between 7 and 8 hours is massive for recovery.', 
                5, {'sleep_hours': total_hours, 'sleep_needed': sleep_needed})
        
        # EXCELLENT: 8+ hours - this is the goal
        if total_hours >= 8:
            return CoachingInsight('sleep', 'green', 'SLEEP MASTER', 
                f'{in_bed.get("hours", 0)}h {in_bed.get("minutes", 0)}m - ELITE sleep. This is how you recover like a pro.', 
                'Perfect. This sleep quality is why your HRV and recovery are strong. Protect this routine at all costs.', 
                2, {'sleep_hours': total_hours, 'sleep_needed': sleep_needed})
        
        return None
    
    def analyze_strain_recovery_balance(self, recovery_metrics: Dict, strain_metrics: Dict) -> Optional[CoachingInsight]:
        """AGGRESSIVE strain/recovery balance - no room for stupidity"""
        if not recovery_metrics or not strain_metrics:
            return None
        
        rec_score = recovery_metrics.get('latest_score', 0)
        strain_score = strain_metrics.get('latest', 0)
        
        # CATASTROPHIC: Very high strain + very low recovery = you're destroying yourself
        if strain_score > 18 and rec_score < 33:
            return CoachingInsight('workout', 'red', 'TRAINING SUICIDE', 
                f'Strain {strain_score:.1f} with recovery {rec_score:.0f}%. You are not "tough" - you are self-harming. This breaks athletes.', 
                'MANDATORY 2-day rest minimum. No training. No excuses. You need to recover or you will get injured.', 
                10, {'strain': strain_score, 'recovery': rec_score})
        
        # DANGER: High strain + low recovery = bad decision
        if strain_score > 16 and rec_score < 40:
            return CoachingInsight('workout', 'red', 'RECOVERY DESTROYED', 
                f'High strain ({strain_score:.1f}) with low recovery ({rec_score:.0f}%). You dug a hole and kept digging.', 
                'Rest today. Light walk only. Eat perfectly. Sleep 9 hours. Do not make this worse.', 
                9, {'strain': strain_score, 'recovery': rec_score})
        
        # WARNING: Moderate strain + poor recovery = risky
        if strain_score > 14 and rec_score < 50:
            return CoachingInsight('workout', 'yellow', 'Strain/Recovery Imbalance', 
                f'Strain {strain_score:.1f} with recovery {rec_score:.0f}%. You are pushing harder than you can recover from.', 
                'Reduce intensity 50% today. Focus on technique, not weight. Tonight: perfect sleep and nutrition.', 
                7, {'strain': strain_score, 'recovery': rec_score})
        
        # EXCELLENT: Optimal zone - this is where gains happen
        if 12 <= strain_score <= 16 and rec_score >= 67:
            return CoachingInsight('workout', 'green', 'TRAINING PERFECTION', 
                f'Strain {strain_score:.1f} with recovery {rec_score:.0f}%. This is the ZONE. You are training like an elite athlete.', 
                'Perfect balance. This is sustainable progress. Keep this rhythm and you will transform.', 
                2, {'strain': strain_score, 'recovery': rec_score})
        
        # GOOD: Moderate strain + good recovery = building fitness
        if 10 <= strain_score <= 14 and rec_score >= 60:
            return CoachingInsight('workout', 'green', 'Smart Training', 
                f'Strain {strain_score:.1f} with recovery {rec_score:.0f}%. You are building fitness without breaking down.', 
                'Solid work. You can push a bit harder if recovery stays green. Stay consistent.', 
                3, {'strain': strain_score, 'recovery': rec_score})
        
        # OPPORTUNITY: Low strain + high recovery = time to attack
        if strain_score < 10 and rec_score >= 75:
            return CoachingInsight('workout', 'blue', 'ATTACK DAY', 
                f'Low strain ({strain_score:.1f}) with high recovery ({rec_score:.0f}%). You are primed for a breakthrough.', 
                'Today is the day to go for it. PR attempt, heavy session, or long effort. You are bulletproof.', 
                4, {'strain': strain_score, 'recovery': rec_score})
        
        # UNDERTRAINED: Very low strain + good recovery = leaving gains on table
        if strain_score < 8 and rec_score >= 67:
            return CoachingInsight('workout', 'yellow', 'Undertrained - Push Harder', 
                f'Only {strain_score:.1f} strain with {rec_score:.0f}% recovery. You are recovering well but not training hard enough.', 
                'Increase volume or intensity. You have capacity - use it. Do not waste green recovery on easy days.', 
                5, {'strain': strain_score, 'recovery': rec_score})
        
        return None
    
    def generate_todays_mission(self, recovery_metrics: Dict, sleep_metrics: Dict, strain_metrics: Dict, user_data: Dict) -> Dict:
        """AGGRESSIVE mission generation - no excuses, maximum accountability"""
        rec_score = recovery_metrics.get('latest_score', 50)
        hrv_change = recovery_metrics.get('hrv', {}).get('change_pct', 0)
        
        # CATASTROPHIC: Recovery in the red - you are broken
        if rec_score < 33:
            return {
                'title': '🔴 MISSION: FORCED REST', 
                'subtitle': 'Your body is BROKEN. Listen to it or pay the price.', 
                'priority': 'red', 
                'actions': [
                    'NO TRAINING - Do not even think about it',
                    'Sleep 9+ hours tonight - non-negotiable',
                    'Eat perfectly - no sugar, no alcohol',
                    'Light walk only - 20 minutes max',
                    'Check recovery tomorrow - if still red, another rest day'
                ], 
                'why': f'Recovery at {rec_score:.0f}%. You are not "tough" - you are self-destructing. Rest is not optional.'
            }
        
        # DANGER: Recovery below 40% - walking a tightrope
        if rec_score < 40:
            return {
                'title': '🟡 MISSION: DAMAGE CONTROL', 
                'subtitle': 'You are one bad decision from red recovery', 
                'priority': 'yellow', 
                'actions': [
                    'No intense training today - mobility only',
                    'In bed by 9 PM - no excuses',
                    'Perfect nutrition - 180g protein, zero alcohol',
                    'Hydrate 3L minimum',
                    'Tomorrow you either recover or crash - choose wisely'
                ], 
                'why': f'Recovery at {rec_score:.0f}%. You are overreaching. Back off NOW before it becomes a problem.'
            }
        
        # SLEEP CRISIS: Less than 6 hours - you are impaired
        if sleep_metrics:
            total_hours = sleep_metrics.get('in_bed', {}).get('hours', 0) + sleep_metrics.get('in_bed', {}).get('minutes', 0) / 60
            if total_hours < 5:
                return {
                    'title': '🔴 MISSION: SLEEP DEBT CRISIS', 
                    'subtitle': 'You are cognitively impaired. This is damage control.', 
                    'priority': 'red', 
                    'actions': [
                        'Nap 20-30 min TODAY - non-negotiable',
                        'NO important decisions until rested',
                        'Tonight: bed by 9 PM, screens off 8:30 PM',
                        'No training - you will injure yourself',
                        'This is not "being busy" - this is self-neglect'
                    ], 
                    'why': f"Only {sleep_metrics['in_bed']['hours']}h sleep. Your reaction time is worse than drunk driving. Fix this."
                }
            
            if total_hours < 6:
                return {
                    'title': '🟡 MISSION: SLEEP RECOVERY', 
                    'subtitle': 'You are building sleep debt that will crush you', 
                    'priority': 'yellow', 
                    'actions': [
                        'Nap if possible - even 20 min helps',
                        'Tonight: bed by 9 PM - no exceptions',
                        'No screens after 8:30 PM - blue light destroys sleep',
                        'No alcohol - it ruins sleep quality',
                        'Light activity only - save the hard stuff for tomorrow'
                    ], 
                    'why': f"{sleep_metrics['in_bed']['hours']}h sleep is NOT enough. This is why your recovery suffers."
                }
        
        # HRV CRASH: Nervous system is failing
        if hrv_change < -20:
            return {
                'title': '🔴 MISSION: NERVOUS SYSTEM RECOVERY', 
                'subtitle': 'Your autonomic nervous system is FAILING', 
                'priority': 'red', 
                'actions': [
                    'COMPLETE REST - No training, no stress',
                    '10-minute meditation - calm your nervous system',
                    'Sleep 9+ hours - your body needs it',
                    'No caffeine after noon - it is making this worse',
                    'Check HRV tomorrow - if still crashing, see a doctor'
                ], 
                'why': f'HRV down {abs(hrv_change):.0f}%. This is not normal. You are breaking down.'
            }
        
        # HRV DECLINE: Trending wrong
        if hrv_change < -12:
            return {
                'title': '🟡 MISSION: STRESS REDUCTION', 
                'subtitle': 'Your recovery capacity is dropping. Fix this now.', 
                'priority': 'yellow', 
                'actions': [
                    'No hard training today - reduce volume 50%',
                    '10-minute meditation this morning',
                    'In bed by 9:30 PM - sleep fixes HRV',
                    'Identify stress source - work, life, training?',
                    'Tomorrow you either recover or enter the danger zone'
                ], 
                'why': f'HRV down {abs(hrv_change):.0f}%. This trend leads to red recovery. Stop it now.'
            }
        
        # RED STREAK: Multiple red days
        if recovery_metrics.get('red_days', 0) >= 2:
            return {
                'title': '🟡 MISSION: BREAK THE RED STREAK', 
                'subtitle': 'Two red days. One more and you are in crisis.', 
                'priority': 'yellow', 
                'actions': [
                    'NO training today - active recovery only',
                    '30-minute easy walk - keep heart rate low',
                    'Stretching session 15 min - focus on hips and back',
                    'Sleep 8+ hours tonight - this is mandatory',
                    'Tomorrow we check recovery - green or another rest day'
                ], 
                'why': '2+ red days is a warning. 3+ red days is a crisis. Do not let this become a streak.'
            }
        
        # STRAIN/RECOVERY MISMATCH: High strain, poor recovery
        strain_score = strain_metrics.get('latest', 0)
        if strain_score > 16 and rec_score < 50:
            return {
                'title': '🟡 MISSION: RECOVERY REPAIR', 
                'subtitle': 'You dug a hole yesterday. Do not make it deeper.', 
                'priority': 'yellow', 
                'actions': [
                    'Rest day - light walk only',
                    'Extra protein - 180g target for repair',
                    'Hydrate 3.5L - flush the system',
                    'Mobility work 20 min - help the body recover',
                    'In bed by 9 PM - sleep is your only way out'
                ], 
                'why': f"Yesterday's strain ({strain_score:.1f}) with today's recovery ({rec_score:.0f}%) is unsustainable."
            }
        
        # Check Apple Health water data for hydration priority - AGGRESSIVE
        apple_health_water = user_data.get('apple_health_water')
        if apple_health_water and apple_health_water.get('available'):
            recent_data = apple_health_water.get('data', [])
            if recent_data:
                today_water = recent_data[0]
                yesterday_water = recent_data[1] if len(recent_data) > 1 else None
                
                today_oz = today_water.get('ounces', 0)
                yesterday_oz = yesterday_water.get('ounces', 0) if yesterday_water else 0
                
                # CRITICAL: Two days severe dehydration - same priority as red recovery
                if today_oz < 20 and yesterday_oz < 20:
                    return {
                        'title': '🔴 MISSION: HYDRATION EMERGENCY', 
                        'subtitle': 'You are SEVERELY DEHYDRATED. This is killing your recovery.', 
                        'priority': 'red', 
                        'actions': [
                            'Drink 32oz (1L) water RIGHT NOW - before you do anything else',
                            'Set phone reminders every hour - no excuses',
                            'Carry a water bottle everywhere - sip constantly',
                            'Add electrolytes to one drink - you need minerals',
                            'Track every glass in Apple Health - accountability'
                        ], 
                        'why': f'CRITICAL: {today_oz:.0f}oz today, {yesterday_oz:.0f}oz yesterday. Dehydration destroys HRV, recovery, and cognitive function. Fix this NOW.'
                    }
                
                # DANGER: Very low today
                if today_oz < 20:
                    return {
                        'title': '🔴 MISSION: DEHYDRATION CRISIS', 
                        'subtitle': 'Your body is desperate for water. This is not optional.', 
                        'priority': 'red', 
                        'actions': [
                            'Drink 24oz (3 cups) IMMEDIATELY - set a timer',
                            'Carry a water bottle all day - never empty',
                            'Set 3 phone reminders today - 10am, 2pm, 6pm',
                            'Track every glass in Apple Health - no guessing',
                            'Goal: 80oz by bedtime - that is 10 cups'
                        ], 
                        'why': f'Only {today_oz:.0f}oz today. Dehydration impairs recovery, mental performance, and energy. You are operating at a deficit.'
                    }
                
                # WARNING: Below target for 2 days
                if today_oz < 40 and yesterday_oz < 40 and yesterday_oz > 0:
                    return {
                        'title': '🟡 MISSION: HYDRATION FOCUS', 
                        'subtitle': 'Two days below target. Your recovery is suffering.', 
                        'priority': 'yellow', 
                        'actions': [
                            'Drink 16oz water RIGHT NOW - chug it',
                            'Track every glass in Apple Health - build the habit',
                            'Goal: 80oz (10 cups) today - non-negotiable',
                            'Drink 8oz before every meal - automatic hydration',
                            'Check your pee - should be light yellow'
                        ], 
                        'why': f'{today_oz:.0f}oz today, {yesterday_oz:.0f}oz yesterday. Two days below optimal impacts recovery capacity. Turn this around.'
                    }
                
                # CAUTION: Below target today
                if today_oz < 40:
                    return {
                        'title': '🟡 MISSION: HYDRATION BOOST', 
                        'subtitle': 'Water intake is too low. Fix it before it becomes a problem.', 
                        'priority': 'yellow', 
                        'actions': [
                            'Drink 16oz water now - do not wait',
                            'Set hourly reminders - phone alerts',
                            'Goal: 80oz today - you need {80 - today_oz:.0f}oz more',
                            'Drink with every meal - automatic 24oz',
                            'Track in Apple Health - what gets measured gets managed'
                        ], 
                        'why': f'{today_oz:.0f}oz so far. Hydration directly affects HRV and recovery. Do not leave gains on the table.'
                    }
        
        # Fallback to manual water tracking
        water = user_data.get('water', {})
        if water.get('percent_complete', 100) < 40:
            return {
                'title': '🟡 MISSION: HYDRATION NOW', 
                'subtitle': 'Water tracking shows you are behind. Catch up.', 
                'priority': 'yellow', 
                'actions': [
                    'Drink 500ml water immediately - chug it',
                    'Set hourly reminders - phone alerts',
                    'Carry a water bottle everywhere - sip constantly',
                    'Track every glass - accountability'
                ], 
                'why': f"Only {water['percent_complete']:.0f}% of water goal. Dehydration is silent recovery killer."
            }
        
        # Default daily missions - AGGRESSIVE when no red flags
        weekday = datetime.now().weekday()
        
        # Check if we are in a good position to push
        can_push_hard = rec_score >= 67 and (not sleep_metrics or sleep_metrics.get('in_bed', {}).get('hours', 0) >= 7)
        
        if can_push_hard:
            # GREEN missions - we are crushing it, time to attack
            missions = {
                0: {'title': '🟢 MISSION: ATTACK MONDAY', 'subtitle': 'You are primed. Start the week with dominance.', 'priority': 'green', 'actions': ['Hit 180g protein - fuel the machine', 'Lift HEAVY - this is PR day', 'Hydrate 3L+ - performance requires fluid', 'Sleep 8+ hours tonight - protect the gains'], 'why': f'Recovery at {rec_score:.0f}%. You are bulletproof. This is the day to push limits.'},
                1: {'title': '🟢 MISSION: ENGINE BUILDING', 'subtitle': 'Build the aerobic engine that powers everything.', 'priority': 'green', 'actions': ['40 min zone 2 cardio - no excuses', 'Heart rate 120-140 - stay disciplined', 'Hydrate during - 500ml minimum', 'Protein 160g - recovery fuel'], 'why': 'Tuesday cardio builds the base. Elite athletes have big engines. Build yours.'},
                2: {'title': '🟢 MISSION: POWER WEDNESDAY', 'subtitle': 'Mid-week strength. Maintain momentum.', 'priority': 'green', 'actions': ['Hit 180g protein - muscle synthesis', 'Lift heavy - progressive overload', 'Track every rep - data drives progress', 'Hydrate 3L - cellular performance'], 'why': 'Wednesday separates contenders from pretenders. Show up strong.'},
                3: {'title': '🟢 MISSION: ACTIVE RECOVERY', 'subtitle': 'Move to recover. Prepare for Friday assault.', 'priority': 'green', 'actions': ['30 min easy walk - blood flow', 'Stretch 15 min - hips and shoulders', 'Meal prep - set up weekend success', 'Bed by 10 PM - build the battery'], 'why': 'Thursday is setup day. Recover hard so you can attack Friday harder.'},
                4: {'title': '🟢 MISSION: FRIDAY FINISHER', 'subtitle': 'End the week strong. Leave nothing.', 'priority': 'green', 'actions': ['Hit 180g protein - finish strong', 'Lift heavy - last chance this week', 'Track PRs - measure progress', 'Plan weekend activity - active recovery'], 'why': 'Friday is your victory lap. You have earned the right to push. Finish strong.'},
                5: {'title': '🟢 MISSION: PLAY HARD', 'subtitle': 'Move because you love it. Play like a kid.', 'priority': 'green', 'actions': ['Hike, surf, or sport - 90+ min', 'Make it social - joy multiplies', 'No intensity pressure - just move', 'Hydrate 3L - all day activity'], 'why': 'Saturday is for joy. Active recovery that does not feel like work. Play hard.'},
                6: {'title': '🟢 MISSION: SUNDAY SETUP', 'subtitle': 'Prepare to dominate next week.', 'priority': 'green', 'actions': ['Meal prep - remove weekday excuses', 'Review the week - what worked?', 'Set sleep alarm - Monday starts Sunday night', 'Plan training week - intention drives action'], 'why': 'Sunday preparation enables Monday success. Champions are made on Sundays.'}
            }
        else:
            # YELLOW missions - we are okay but not optimal, be smart
            missions = {
                0: {'title': '🟡 MISSION: SMART MONDAY', 'subtitle': 'Start smart. Build the week sustainably.', 'priority': 'yellow', 'actions': ['Hit 160g protein - solid foundation', 'Lift moderate - technique focus', 'Hydrate 2.5L - minimum effective dose', 'Sleep 8 hours - non-negotiable'], 'why': f'Recovery at {rec_score:.0f}%. Good but not great. Build the week smart.'},
                1: {'title': '🟡 MISSION: STEADY CARDIO', 'subtitle': 'Build endurance without breaking down.', 'priority': 'yellow', 'actions': ['30 min zone 2 - consistency beats intensity', 'Heart rate controlled - discipline', 'Hydrate - 2L minimum', 'Protein 160g - recovery focus'], 'why': 'Tuesday builds the engine. Steady work compounds.'},
                2: {'title': '🟡 MISSION: CONTROLLED STRENGTH', 'subtitle': 'Wednesday power - but respect your body.', 'priority': 'yellow', 'actions': ['Protein 160g - fuel the work', 'Lift moderate - no ego', 'Track weights - progressive when ready', 'Hydrate 2.5L - performance support'], 'why': 'Wednesday is maintenance. Do not dig a hole.'},
                3: {'title': '🟡 MISSION: RECOVERY DAY', 'subtitle': 'Back off. Prepare for Friday.', 'priority': 'yellow', 'actions': ['Light walk 20 min - move gently', 'Stretch 10 min - maintenance', 'Early meal prep - set up success', 'Bed by 9:30 PM - prioritize sleep'], 'why': 'Thursday recovery sets up Friday. Be patient.'},
                4: {'title': '🟡 MISSION: FRIDAY SMART', 'subtitle': 'End the week well. Do not force it.', 'priority': 'yellow', 'actions': ['Protein 160g - consistent nutrition', 'Lift moderate - technique day', 'Track progress - data matters', 'Weekend activity planned - active recovery'], 'why': 'Friday finish - smart, not reckless.'},
                5: {'title': '🟡 MISSION: GENTLE SATURDAY', 'subtitle': 'Move easy. Recover hard.', 'priority': 'yellow', 'actions': ['Easy hike or walk - 60 min', 'Low intensity - heart rate <120', 'Social activity - joy matters', 'Hydrate 2.5L - all day'], 'why': 'Saturday recovery. Move enough to feel good, not enough to fatigue.'},
                6: {'title': '🟡 MISSION: SUNDAY PREP', 'subtitle': 'Set up the week. Prioritize recovery.', 'priority': 'yellow', 'actions': ['Light meal prep - simple is fine', 'Review week - learn and adjust', 'Early bedtime - 9:30 PM target', 'Gentle stretching - 10 min'], 'why': 'Sunday setup with recovery focus. Next week starts tonight.'}
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
        
        # Add hydration analysis from Apple Health
        apple_health_water = self.data.get_apple_health_water(days=7)
        hydration_insight = self.analyze_hydration(apple_health_water)
        if hydration_insight:
            insights.append(hydration_insight)
        
        # Add steps analysis from Apple Health
        apple_health_steps = self.data.get_apple_health_steps(days=7)
        steps_insight = self.analyze_steps(apple_health_steps)
        if steps_insight:
            insights.append(steps_insight)
        
        # Add INTEGRATED analysis - looks at ALL data sources together
        # This is the key differentiator - Vitus connects the dots
        integrated_insights = self.analyze_integrated_health(
            whoop_data, 
            apple_health_water, 
            apple_health_steps,
            loseit_data
        )
        insights.extend(integrated_insights)
        
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
    
    def generate_midday_checkin(self) -> str:
        """Generate a lighter midday check-in focused on hydration, movement, and lunch"""
        whoop_data = self.monitor.fetch_whoop_data(days=3)
        user_data = self.data.get_today_metrics()
        
        # Get Apple Health data
        apple_health_water = self.data.get_apple_health_water(days=3)
        apple_health_steps = self.data.get_apple_health_steps(days=3)
        
        today = datetime.now().strftime('%A, %B %d')
        
        html = f"""<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"><title>Vitus Midday Check-In</title></head>
<body style="font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;max-width:600px;margin:0 auto;padding:20px;background:#f8f9fa;">
<div style="background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);padding:30px;border-radius:12px 12px 0 0;text-align:center;">
    <div style="font-size:32px;margin-bottom:10px;">☀️</div>
    <h1 style="color:white;margin:0;font-size:24px;">Midday Check-In</h1>
    <p style="color:rgba(255,255,255,0.9);margin:5px 0 0 0;">{today}</p>
</div>
<div style="background:white;padding:30px;border-radius:0 0 12px 12px;box-shadow:0 4px 6px rgba(0,0,0,0.1);">
"""
        
        # Hydration check
        if apple_health_water and apple_health_water.get('available'):
            recent_data = apple_health_water.get('data', [])
            if recent_data:
                today_water = recent_data[0].get('ounces', 0)
                water_ml = int(today_water * 29.5735)
                progress = min(today_water / 80 * 100, 100)  # 80oz goal
                
                if today_water < 40:
                    water_status = '🔴 Behind'
                    water_color = '#e74c3c'
                    water_action = 'Drink 16oz water now!'
                elif today_water < 64:
                    water_status = '🟡 Getting there'
                    water_color = '#f39c12'
                    water_action = 'Drink 8oz with lunch'
                else:
                    water_status = '🟢 On track'
                    water_color = '#27ae60'
                    water_action = 'Keep sipping!'
                
                html += f"""
<div style="background:#f8f9fa;border-radius:8px;padding:15px;margin:15px 0;">
    <div style="font-weight:bold;font-size:16px;margin-bottom:10px;">💧 Hydration Check</div>
    <div style="font-size:24px;color:{water_color};font-weight:bold;">{today_water:.0f} oz ({water_ml}ml)</div>
    <div style="color:{water_color};margin:5px 0;">{water_status}</div>
    <div style="background:#ecf0f1;height:8px;border-radius:4px;margin:10px 0;">
        <div style="background:{water_color};width:{progress}%;height:100%;border-radius:4px;"></div>
    </div>
    <div style="color:#7f8c8d;font-size:14px;">{water_action}</div>
</div>
"""
        
        # Movement check
        if apple_health_steps and apple_health_steps.get('available'):
            steps_data = apple_health_steps.get('data', [])
            if steps_data:
                today_steps = steps_data[0].get('steps', 0)
                progress = min(today_steps / 8000 * 100, 100)
                
                if today_steps < 3000:
                    move_status = '🔴 Low movement'
                    move_color = '#e74c3c'
                    move_action = 'Take a 10-min walk after lunch'
                elif today_steps < 6000:
                    move_status = '🟡 Decent'
                    move_color = '#f39c12'
                    move_action = 'Aim for a quick walk this afternoon'
                else:
                    move_status = '🟢 Great!'
                    move_color = '#27ae60'
                    move_action = 'Keep it up!'
                
                html += f"""
<div style="background:#f8f9fa;border-radius:8px;padding:15px;margin:15px 0;">
    <div style="font-weight:bold;font-size:16px;margin-bottom:10px;">👟 Movement Check</div>
    <div style="font-size:24px;color:{move_color};font-weight:bold;">{today_steps:,} steps</div>
    <div style="color:{move_color};margin:5px 0;">{move_status}</div>
    <div style="background:#ecf0f1;height:8px;border-radius:4px;margin:10px 0;">
        <div style="background:{move_color};width:{progress}%;height:100%;border-radius:4px;"></div>
    </div>
    <div style="color:#7f8c8d;font-size:14px;">{move_action}</div>
</div>
"""
        
        # Recovery context from Whoop
        if whoop_data and whoop_data.get('recovery'):
            latest_rec = whoop_data['recovery'][0]
            score_data = latest_rec.get('score', {})
            rec_score = score_data.get('recovery_score', 0) if isinstance(score_data, dict) else score_data
            
            if rec_score < 50:
                rec_msg = "Your recovery is low today — take it easy, maybe a light walk instead of intense exercise."
                rec_emoji = "🔴"
            elif rec_score < 70:
                rec_msg = "Moderate recovery — you can push a bit if you feel good, but listen to your body."
                rec_emoji = "🟡"
            else:
                rec_msg = "Great recovery! You're ready to take on the afternoon with energy."
                rec_emoji = "🟢"
            
            html += f"""
<div style="background:#f8f9fa;border-radius:8px;padding:15px;margin:15px 0;">
    <div style="font-weight:bold;font-size:16px;margin-bottom:10px;">{rec_emoji} Recovery Context</div>
    <div style="color:#2c3e50;">{rec_msg}</div>
</div>
"""
        
        # Lunch suggestion
        html += """
<div style="background:#e8f5e9;border-radius:8px;padding:15px;margin:15px 0;border-left:4px solid #27ae60;">
    <div style="font-weight:bold;font-size:16px;margin-bottom:10px;">🥗 Lunch Reminder</div>
    <div style="color:#2c3e50;">Aim for protein + vegetables. Think: salad with chicken, grain bowl, or leftovers with a side of greens.</div>
</div>
"""
        
        html += """
<div style="text-align:center;margin-top:30px;padding-top:20px;border-top:1px solid #ecf0f1;color:#7f8c8d;font-size:12px;">
    Vitus 🫀 Your Health Coach
</div>
</div>
</body>
</html>"""
        
        return html
    
    def generate_evening_briefing(self) -> str:
        """Generate evening wind-down briefing with sleep prep"""
        whoop_data = self.monitor.fetch_whoop_data(days=3)
        user_data = self.data.get_today_metrics()
        
        # Get Apple Health data
        apple_health_water = self.data.get_apple_health_water(days=3)
        apple_health_steps = self.data.get_apple_health_steps(days=3)
        
        today = datetime.now().strftime('%A, %B %d')
        tomorrow = (datetime.now() + timedelta(days=1)).strftime('%A, %B %d')
        
        html = f"""<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"><title>Vitus Evening Briefing</title></head>
<body style="font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;max-width:600px;margin:0 auto;padding:20px;background:#f8f9fa;">
<div style="background:linear-gradient(135deg,#2c3e50 0%,#4a6741 100%);padding:30px;border-radius:12px 12px 0 0;text-align:center;">
    <div style="font-size:32px;margin-bottom:10px;">🌙</div>
    <h1 style="color:white;margin:0;font-size:24px;">Evening Wind-Down</h1>
    <p style="color:rgba(255,255,255,0.9);margin:5px 0 0 0;">{today}</p>
</div>
<div style="background:white;padding:30px;border-radius:0 0 12px 12px;box-shadow:0 4px 6px rgba(0,0,0,0.1);">
"""
        
        # Today's summary
        html += """
<div style="background:#f8f9fa;border-radius:8px;padding:15px;margin:15px 0;">
    <div style="font-weight:bold;font-size:16px;margin-bottom:15px;">📊 Today's Summary</div>
"""
        
        # Water summary
        if apple_health_water and apple_health_water.get('available'):
            recent_data = apple_health_water.get('data', [])
            if recent_data:
                today_water = recent_data[0].get('ounces', 0)
                html += f'<div style="margin:5px 0;">💧 Water: <strong>{today_water:.0f} oz</strong></div>'
        
        # Steps summary
        if apple_health_steps and apple_health_steps.get('available'):
            steps_data = apple_health_steps.get('data', [])
            if steps_data:
                today_steps = steps_data[0].get('steps', 0)
                html += f'<div style="margin:5px 0;">👟 Steps: <strong>{today_steps:,}</strong></div>'
        
        html += '</div>'
        
        # Recovery for tomorrow context
        if whoop_data and whoop_data.get('recovery'):
            latest_rec = whoop_data['recovery'][0]
            score_data = latest_rec.get('score', {})
            rec_score = score_data.get('recovery_score', 0) if isinstance(score_data, dict) else score_data
            
            html += f"""
<div style="background:#f8f9fa;border-radius:8px;padding:15px;margin:15px 0;">
    <div style="font-weight:bold;font-size:16px;margin-bottom:10px;">🫀 Recovery Score</div>
    <div style="font-size:32px;font-weight:bold;color:{'#27ae60' if rec_score >= 67 else '#f39c12' if rec_score >= 33 else '#e74c3c'};">{rec_score:.0f}%</div>
    <div style="color:#7f8c8d;margin-top:5px;">This affects how you should approach {tomorrow}</div>
</div>
"""
        
        # Sleep prep
        html += """
<div style="background:#e3f2fd;border-radius:8px;padding:15px;margin:15px 0;border-left:4px solid #2196f3;">
    <div style="font-weight:bold;font-size:16px;margin-bottom:10px;">😴 Sleep Prep</div>
    <div style="color:#2c3e50;margin-bottom:10px;">Wind down for better recovery:</div>
    <ul style="margin:0;padding-left:20px;color:#2c3e50;">
        <li>No screens 30 min before bed</li>
        <li>Dim lights around 9 PM</li>
        <li>Room temp: 65-68°F</li>
        <li>Last call for water (small sip only)</li>
    </ul>
</div>
"""
        
        # Tomorrow preview
        html += f"""
<div style="background:#f5f5f5;border-radius:8px;padding:15px;margin:15px 0;">
    <div style="font-weight:bold;font-size:16px;margin-bottom:10px;">📅 Tomorrow ({tomorrow})</div>
    <div style="color:#7f8c8d;">Check your morning briefing at 7 AM for personalized recommendations based on tonight's sleep.</div>
</div>
"""
        
        html += """
<div style="text-align:center;margin-top:30px;padding-top:20px;border-top:1px solid #ecf0f1;color:#7f8c8d;font-size:12px;">
    Sleep well! 🌙<br>
    Vitus 🫀 Your Health Coach
</div>
</div>
</body>
</html>"""
        
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
        
        # Water progress - use Apple Health data if available
        water = user_data.get('water', {})
        apple_health_water = user_data.get('apple_health_water')
        
        if apple_health_water and apple_health_water.get('available'):
            # Use Apple Health water data with enhanced visualization
            recent_data = apple_health_water.get('data', [])
            if recent_data:
                today_water = recent_data[0]
                yesterday_water = recent_data[1] if len(recent_data) > 1 else None
                
                water_oz = today_water.get('ounces', 0)
                water_ml = int(water_oz * 29.5735)
                target_oz = 80  # ~2.4L / 10 cups
                percent = min(100, (water_oz / target_oz) * 100)
                
                # Determine hydration status color
                if water_oz >= 80:
                    hydration_status = 'green'
                    status_emoji = '✅'
                    status_text = 'On Target'
                elif water_oz >= 40:
                    hydration_status = 'yellow'
                    status_emoji = '⚠️'
                    status_text = 'Below Target'
                elif water_oz > 0:
                    hydration_status = 'red'
                    status_emoji = '🔴'
                    status_text = 'Low Hydration'
                else:
                    hydration_status = 'gray'
                    status_emoji = '❓'
                    status_text = 'No Data'
                
                # Build enhanced 7-day chart with target line
                chart_days = recent_data[:7]
                max_oz = max(80, max(day.get('ounces', 0) for day in chart_days)) if chart_days else 80
                
                chart_html = '<div style="position:relative;height:100px;margin:15px 0;padding:15px;background:linear-gradient(to bottom, #f8f9fa 0%, #e9ecef 100%);border-radius:12px;border:1px solid #dee2e6;">'
                chart_html += '<div style="position:absolute;top:5px;left:10px;font-size:11px;color:#6c757d;font-weight:bold;">7-Day Hydration</div>'
                chart_html += '<div style="position:absolute;top:5px;right:10px;font-size:11px;color:#28a745;font-weight:bold;">Target: 80oz</div>'
                
                # Target line at 80oz
                target_y = 85 - (80 / max_oz * 70)  # Scale to chart height
                chart_html += f'<div style="position:absolute;left:50px;right:15px;top:{target_y}px;height:2px;background:#28a745;opacity:0.5;z-index:1;"></div>'
                chart_html += f'<div style="position:absolute;left:15px;top:{target_y-6}px;font-size:9px;color:#28a745;">80oz</div>'
                
                # Bars
                bar_container = '<div style="display:flex;align-items:flex-end;justify-content:space-between;height:70px;margin-top:20px;margin-left:45px;margin-right:10px;gap:6px;">'
                
                for i, day in enumerate(reversed(chart_days)):
                    oz = day.get('ounces', 0)
                    height_pct = (oz / max_oz * 100) if max_oz > 0 else 0
                    
                    # Color based on target achievement
                    if oz >= 80:
                        bar_color = '#28a745'
                        glow = 'box-shadow:0 0 8px rgba(40,167,69,0.4);'
                    elif oz >= 40:
                        bar_color = '#ffc107'
                        glow = ''
                    elif oz > 0:
                        bar_color = '#dc3545'
                        glow = ''
                    else:
                        bar_color = '#adb5bd'
                        glow = ''
                    
                    day_name = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'][datetime.strptime(day['date'], '%Y-%m-%d').weekday()]
                    is_today = i == 6  # Last bar is today
                    
                    bar_container += f'''<div style="flex:1;display:flex;flex-direction:column;align-items:center;position:relative;">
                        <div style="position:absolute;top:-18px;font-size:10px;font-weight:bold;color:{bar_color};">{oz:.0f}</div>
                        <div style="width:100%;height:{height_pct}%;background:{bar_color};border-radius:4px 4px 0 0;{glow}transition:all 0.3s;"></div>
                        <div style="font-size:10px;color:{'#212529' if is_today else '#6c757d'};margin-top:4px;font-weight:{'bold' if is_today else 'normal'};">{day_name}</div>
                    </div>'''
                
                bar_container += '</div>'
                chart_html += bar_container + '</div>'
                
                # Stats row
                valid_days = [d for d in recent_data if d.get('ounces', 0) > 0]
                avg_oz = sum(d['ounces'] for d in valid_days) / len(valid_days) if valid_days else 0
                
                stats_html = f'''<div style="display:grid;grid-template-columns:repeat(3,1fr);gap:10px;margin:15px 0;">
                    <div style="text-align:center;padding:10px;background:#f8f9fa;border-radius:8px;">
                        <div style="font-size:24px;font-weight:bold;color:{bar_color};">{water_oz:.0f}</div>
                        <div style="font-size:11px;color:#6c757d;">Today (oz)</div>
                    </div>
                    <div style="text-align:center;padding:10px;background:#f8f9fa;border-radius:8px;">
                        <div style="font-size:24px;font-weight:bold;color:#495057;">{avg_oz:.0f}</div>
                        <div style="font-size:11px;color:#6c757d;">7-Day Avg</div>
                    </div>
                    <div style="text-align:center;padding:10px;background:#f8f9fa;border-radius:8px;">
                        <div style="font-size:24px;font-weight:bold;color:{('#28a745' if percent >= 100 else '#ffc107' if percent >= 50 else '#dc3545')};">{percent:.0f}%</div>
                        <div style="font-size:11px;color:#6c757d;">Of Target</div>
                    </div>
                </div>'''
                
                # Yesterday comparison
                yesterday_html = ""
                if yesterday_water and yesterday_water.get('ounces', 0) > 0:
                    diff = water_oz - yesterday_water['ounces']
                    diff_color = '#28a745' if diff > 0 else '#dc3545' if diff < 0 else '#6c757d'
                    diff_icon = '↑' if diff > 0 else '↓' if diff < 0 else '→'
                    yesterday_html = f'<div style="text-align:center;padding:8px;background:#e9ecef;border-radius:6px;margin-top:10px;font-size:13px;color:#495057;">Yesterday: {yesterday_water["ounces"]:.0f}oz <span style="color:{diff_color};font-weight:bold;">{diff_icon} {abs(diff):.0f}oz</span></div>'
                
                # Coaching message based on hydration status
                coaching_messages = {
                    'green': 'Excellent hydration! You\'re meeting your 80oz target. This supports recovery, energy, and performance.',
                    'yellow': f'You\'re at {water_oz:.0f}oz — aim for 80oz today. Hydration directly impacts recovery and HRV.',
                    'red': f'Critical: Only {water_oz:.0f}oz logged. Dehydration impairs recovery, sleep, and cognitive function. Drink 16oz now.',
                    'gray': 'No water data logged today. Start tracking in Apple Health or drink 16oz now to get started.'
                }
                
                water_html = f'''<div style="background:white;padding:20px;margin:15px 0;border-radius:12px;box-shadow:0 2px 8px rgba(0,0,0,0.08);border-left:4px solid {self.COLORS[hydration_status]};">
                    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:15px;">
                        <div style="display:flex;align-items:center;gap:10px;">
                            <span style="font-size:28px;">💧</span>
                            <div>
                                <div style="font-weight:bold;color:#2c3e50;font-size:16px;">Hydration Status</div>
                                <div style="font-size:12px;color:#6c757d;">Apple Health Data</div>
                            </div>
                        </div>
                        <div style="background:{self.RISK_LEVELS[hydration_status]['bg']};color:{self.RISK_LEVELS[hydration_status]['color']};padding:6px 14px;border-radius:20px;font-size:13px;font-weight:bold;border:1px solid {self.RISK_LEVELS[hydration_status]['color']};">
                            {status_emoji} {status_text}
                        </div>
                    </div>
                    
                    {chart_html}
                    {stats_html}
                    {yesterday_html}
                    
                    <div style="margin-top:15px;padding:12px;background:{self.RISK_LEVELS[hydration_status]['bg']};border-radius:8px;border-left:3px solid {self.RISK_LEVELS[hydration_status]['color']};">
                        <div style="font-size:13px;color:#2c3e50;line-height:1.5;">
                            <strong>Coach's Note:</strong> {coaching_messages[hydration_status]}
                        </div>
                    </div>
                    
                    <div style="margin-top:12px;font-size:12px;color:#6c757d;text-align:center;">
                        Target: 80oz (10 cups / 2.4L) per day for optimal recovery
                    </div>
                </div>'''
            else:
                water_html = '<div style="background:white;padding:15px;margin:15px 0;border-radius:8px;box-shadow:0 1px 3px rgba(0,0,0,0.1);"><div style="color:#7f8c8d;">💧 No water data available from Apple Health yet.</div></div>'
        else:
            # Fallback to manual tracking
            water_html = f'<div style="background:white;padding:15px;margin:15px 0;border-radius:8px;box-shadow:0 1px 3px rgba(0,0,0,0.1);"><div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:10px;"><span style="font-weight:bold;color:#2c3e50;">💧 Hydration</span><span style="color:#7f8c8d;">{water.get("total_ml", 0)}ml / {water.get("goal_ml", 3000)}ml</span></div>{self._progress_bar(water.get("percent_complete", 0), "green" if water.get("percent_complete", 0) >= 75 else "yellow" if water.get("percent_complete", 0) >= 40 else "red")}<div style="font-size:13px;color:#7f8c8d;margin-top:5px;">{self.data.get_water_recommendation()}</div></div>'
        
        # Steps section - Apple Health data
        apple_health_steps = user_data.get('apple_health_steps')
        steps_html = ''
        
        if apple_health_steps and apple_health_steps.get('available'):
            recent_steps = apple_health_steps.get('data', [])
            if recent_steps:
                today_steps_data = recent_steps[0]
                yesterday_steps_data = recent_steps[1] if len(recent_steps) > 1 else None
                
                today_steps = today_steps_data.get('steps', 0)
                target_steps = apple_health_steps.get('target_steps', 10000)
                steps_percent = min(100, (today_steps / target_steps) * 100)
                
                # Determine steps status
                if today_steps >= target_steps:
                    steps_status = 'green'
                    steps_emoji = '✅'
                    steps_status_text = 'Goal Crushed'
                elif today_steps >= target_steps * 0.75:
                    steps_status = 'green'
                    steps_emoji = '👍'
                    steps_status_text = 'On Track'
                elif today_steps >= target_steps * 0.5:
                    steps_status = 'yellow'
                    steps_emoji = '⚠️'
                    steps_status_text = 'Below Target'
                elif today_steps > 0:
                    steps_status = 'red'
                    steps_emoji = '🔴'
                    steps_status_text = 'Too Low'
                else:
                    steps_status = 'gray'
                    steps_emoji = '❓'
                    steps_status_text = 'No Data'
                
                # Build steps chart
                steps_chart_days = recent_steps[:7]
                max_steps = max(target_steps, max(day.get('steps', 0) for day in steps_chart_days)) if steps_chart_days else target_steps
                
                steps_chart_html = '<div style="position:relative;height:100px;margin:15px 0;padding:15px;background:linear-gradient(to bottom, #f8f9fa 0%, #e9ecef 100%);border-radius:12px;border:1px solid #dee2e6;">'
                steps_chart_html += '<div style="position:absolute;top:5px;left:10px;font-size:11px;color:#6c757d;font-weight:bold;">7-Day Steps</div>'
                steps_chart_html += '<div style="position:absolute;top:5px;right:10px;font-size:11px;color:#28a745;font-weight:bold;">Target: 10k</div>'
                
                # Target line at 10k
                target_y_steps = 85 - (target_steps / max_steps * 70)
                steps_chart_html += f'<div style="position:absolute;left:50px;right:15px;top:{target_y_steps}px;height:2px;background:#28a745;opacity:0.5;z-index:1;"></div>'
                steps_chart_html += f'<div style="position:absolute;left:15px;top:{target_y_steps-6}px;font-size:9px;color:#28a745;">10k</div>'
                
                # Bars
                steps_bar_container = '<div style="display:flex;align-items:flex-end;justify-content:space-between;height:70px;margin-top:20px;margin-left:45px;margin-right:10px;gap:6px;">'
                
                for i, day in enumerate(reversed(steps_chart_days)):
                    steps_count = day.get('steps', 0)
                    height_pct = (steps_count / max_steps * 100) if max_steps > 0 else 0
                    
                    if steps_count >= target_steps:
                        bar_color = '#28a745'
                    elif steps_count >= target_steps * 0.75:
                        bar_color = '#6c757d'
                    elif steps_count >= target_steps * 0.5:
                        bar_color = '#ffc107'
                    elif steps_count > 0:
                        bar_color = '#dc3545'
                    else:
                        bar_color = '#adb5bd'
                    
                    day_name = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'][datetime.strptime(day['date'], '%Y-%m-%d').weekday()]
                    is_today = i == 6
                    
                    steps_bar_container += f'''<div style="flex:1;display:flex;flex-direction:column;align-items:center;position:relative;">
                        <div style="position:absolute;top:-18px;font-size:10px;font-weight:bold;color:{bar_color};">{steps_count//1000}k</div>
                        <div style="width:100%;height:{height_pct}%;background:{bar_color};border-radius:4px 4px 0 0;"></div>
                        <div style="font-size:10px;color:{'#212529' if is_today else '#6c757d'};margin-top:4px;font-weight:{'bold' if is_today else 'normal'};">{day_name}</div>
                    </div>'''
                
                steps_bar_container += '</div>'
                steps_chart_html += steps_bar_container + '</div>'
                
                # Stats
                valid_steps_days = [d for d in recent_steps if d.get('steps', 0) > 0]
                avg_steps = int(sum(d['steps'] for d in valid_steps_days) / len(valid_steps_days)) if valid_steps_days else 0
                
                steps_stats_html = f'''<div style="display:grid;grid-template-columns:repeat(3,1fr);gap:10px;margin:15px 0;">
                    <div style="text-align:center;padding:10px;background:#f8f9fa;border-radius:8px;">
                        <div style="font-size:24px;font-weight:bold;color:{bar_color};">{today_steps//1000}k</div>
                        <div style="font-size:11px;color:#6c757d;">Today</div>
                    </div>
                    <div style="text-align:center;padding:10px;background:#f8f9fa;border-radius:8px;">
                        <div style="font-size:24px;font-weight:bold;color:#495057;">{avg_steps//1000}k</div>
                        <div style="font-size:11px;color:#6c757d;">7-Day Avg</div>
                    </div>
                    <div style="text-align:center;padding:10px;background:#f8f9fa;border-radius:8px;">
                        <div style="font-size:24px;font-weight:bold;color:{('#28a745' if steps_percent >= 100 else '#ffc107' if steps_percent >= 75 else '#dc3545')};">{steps_percent:.0f}%</div>
                        <div style="font-size:11px;color:#6c757d;">Of Goal</div>
                    </div>
                </div>'''
                
                steps_coaching = {
                    'green': 'Excellent movement! 10k+ steps supports recovery, metabolism, and longevity.',
                    'yellow': f'{today_steps:,} steps - good but not great. Aim for 10k to optimize health.',
                    'red': f'Only {today_steps:,} steps. This is sedentary. Move more or your health suffers.',
                    'gray': 'No steps data. Start moving - even a 10-min walk helps.'
                }
                
                steps_html = f'''<div style="background:white;padding:20px;margin:15px 0;border-radius:12px;box-shadow:0 2px 8px rgba(0,0,0,0.08);border-left:4px solid {self.COLORS[steps_status]};">
                    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:15px;">
                        <div style="display:flex;align-items:center;gap:10px;">
                            <span style="font-size:28px;">👟</span>
                            <div>
                                <div style="font-weight:bold;color:#2c3e50;font-size:16px;">Daily Steps</div>
                                <div style="font-size:12px;color:#6c757d;">Apple Health Data</div>
                            </div>
                        </div>
                        <div style="background:{self.RISK_LEVELS[steps_status]['bg']};color:{self.RISK_LEVELS[steps_status]['color']};padding:6px 14px;border-radius:20px;font-size:13px;font-weight:bold;border:1px solid {self.RISK_LEVELS[steps_status]['color']};">
                            {steps_emoji} {steps_status_text}
                        </div>
                    </div>
                    
                    {steps_chart_html}
                    {steps_stats_html}
                    
                    <div style="margin-top:15px;padding:12px;background:{self.RISK_LEVELS[steps_status]['bg']};border-radius:8px;border-left:3px solid {self.RISK_LEVELS[steps_status]['color']};">
                        <div style="font-size:13px;color:#2c3e50;line-height:1.5;">
                            <strong>Coach's Note:</strong> {steps_coaching[steps_status]}
                        </div>
                    </div>
                </div>'''
        
        # Nutrition section
        snacks = self.data.get_snack_suggestions()
        snacks_html = ''.join([f'<div style="padding:8px;margin:5px 0;background:#f8f9fa;border-radius:4px;"><strong>{s["name"]}</strong><br><span style="font-size:12px;color:#7f8c8d;">{s["calories"]} cal • {s["protein"]}g protein • {s["why"]}</span></div>' for s in snacks])
        
        nutrition_html = f'<div style="background:white;padding:15px;margin:15px 0;border-radius:8px;box-shadow:0 1px 3px rgba(0,0,0,0.1);"><div style="font-weight:bold;color:#2c3e50;margin-bottom:10px;">🍽️ Nutrition Targets</div><div style="display:grid;grid-template-columns:1fr 1fr;gap:10px;margin:10px 0;"><div>Calories: <strong>{nutrition["calories"]}</strong></div><div>Protein: <strong>{nutrition["protein"]}g</strong></div><div>Carbs: <strong>{nutrition["carbs"]}g</strong></div><div>Fat: <strong>{nutrition["fat"]}g</strong></div></div><div style="margin-top:15px;"><div style="font-weight:bold;color:#2c3e50;margin-bottom:5px;">💡 Smart Snacks</div>{snacks_html}</div></div>'
        
        # Sleep prep section
        sleep_html = f'<div style="background:{self.RISK_LEVELS["yellow" if sleep_prep["priority"] == "medium" else "red" if sleep_prep["priority"] == "high" else "green"]["bg"]};border:1px solid {self.RISK_LEVELS["yellow" if sleep_prep["priority"] == "medium" else "red" if sleep_prep["priority"] == "high" else "green"]["color"]};border-radius:8px;padding:15px;margin:15px 0;"><div style="font-weight:bold;color:#2c3e50;margin-bottom:10px;">🌙 Tonight: Sleep Prep</div><div style="font-size:14px;color:#7f8c8d;margin-bottom:10px;">{sleep_prep["message"]}</div><div style="font-weight:bold;margin:10px 0;">Target bedtime: {sleep_prep["bedtime"]}</div><ul style="margin:0;padding-left:20px;">{"".join([f"<li style=\"margin:5px 0;\">{a}</li>" for a in sleep_prep["actions"]])}</ul></div>'
        
        # Insights section - with special highlighting for integrated analysis
        insights_html = ''
        if insights:
            # Separate integrated insights from individual metric insights
            integrated_insights_list = [ins for ins in insights if ins.category == 'integrated']
            other_insights = [ins for ins in insights if ins.category != 'integrated']
            
            # Show integrated insights first (these are the most important)
            if integrated_insights_list:
                integrated_html = []
                for ins in integrated_insights_list[:2]:  # Top 2 integrated
                    risk = self.RISK_LEVELS.get(ins.severity, self.RISK_LEVELS['blue'])
                    integrated_html.append(f'<div style="background:{risk["bg"]};border:2px solid {risk["color"]};border-left:6px solid {risk["color"]};padding:15px;margin:12px 0;border-radius:8px;box-shadow:0 2px 4px rgba(0,0,0,0.1);"><div style="font-weight:bold;color:{risk["color"]};margin-bottom:8px;font-size:16px;">🎯 {ins.title}</div><div style="font-size:14px;color:#2c3e50;margin-bottom:8px;line-height:1.5;">{ins.message}</div><div style="font-size:13px;color:#7f8c8d;background:white;padding:10px;border-radius:6px;"><strong>Action Required:</strong> {ins.action}</div></div>')
                insights_html += '<div style="margin:20px 0;"><div style="font-weight:bold;color:#2c3e50;margin-bottom:10px;font-size:20px;">🧠 Vitus Integrated Assessment</div><div style="font-size:13px;color:#6c757d;margin-bottom:15px;">Connecting all your data to see the big picture</div>' + ''.join(integrated_html) + '</div>'
            
            # Show other insights
            if other_insights:
                other_html = []
                for ins in other_insights[:3]:  # Top 3 other
                    risk = self.RISK_LEVELS.get(ins.severity, self.RISK_LEVELS['blue'])
                    other_html.append(f'<div style="background:{risk["bg"]};border-left:4px solid {risk["color"]};padding:12px;margin:10px 0;border-radius:0 8px 8px 0;"><div style="font-weight:bold;color:{risk["color"]};margin-bottom:5px;">{ins.title}</div><div style="font-size:14px;color:#2c3e50;margin-bottom:5px;">{ins.message}</div><div style="font-size:13px;color:#7f8c8d;"><strong>Action:</strong> {ins.action}</div></div>')
                insights_html += '<div style="margin:20px 0;"><div style="font-weight:bold;color:#2c3e50;margin-bottom:10px;font-size:18px;">📊 Individual Metrics</div>' + ''.join(other_html) + '</div>'
        
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
        {steps_html}
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
        elif cmd == 'midday':
            briefing = coach.generate_midday_checkin()
            print("Midday check-in generated. Sending email...")
            if coach.send_briefing_email(briefing):
                print("✅ Midday check-in sent successfully")
            else:
                print("❌ Failed to send check-in")
        elif cmd == 'evening':
            briefing = coach.generate_evening_briefing()
            print("Evening briefing generated. Sending email...")
            if coach.send_briefing_email(briefing):
                print("✅ Evening briefing sent successfully")
            else:
                print("❌ Failed to send briefing")
        else:
            print("Usage: python3 coach_engine.py [morning|midday|evening]")
    else:
        briefing = coach.generate_morning_briefing()
        print(briefing)