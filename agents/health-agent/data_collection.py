#!/usr/bin/env python3
"""
Vitus - Data Collection System
Collects user inputs for water, stress, energy, and other metrics
Stores in simple JSON files for pattern recognition
"""

import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict

DATA_DIR = Path.home() / '.openclaw' / 'workspace' / 'agents' / 'health-agent' / 'memory' / 'user_data'
DATA_DIR.mkdir(parents=True, exist_ok=True)


@dataclass
class DailyCheckIn:
    date: str
    water_intake_ml: int = 0
    water_goal_ml: int = 3000  # Default 3L
    stress_level: int = 5  # 1-10 scale
    energy_level: int = 5  # 1-10 scale
    mood: str = "neutral"  # great, good, neutral, low, bad
    sleep_quality_user: int = 5  # 1-10 user-rated
    notes: str = ""
    timestamp: str = ""
    
    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()


@dataclass
class SnackLog:
    date: str
    time: str
    snack_name: str
    calories: int = 0
    protein: int = 0
    healthy_rating: int = 3  # 1-5 scale


@dataclass
class MealLog:
    date: str
    meal_type: str  # breakfast, lunch, dinner
    foods: List[str]
    calories: int = 0
    protein: int = 0
    carbs: int = 0
    fat: int = 0
    satisfaction: int = 3  # 1-5 scale


class VitusDataCollection:
    """Handles all user-input data collection"""
    
    def __init__(self):
        self.data_dir = DATA_DIR
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
    def _get_daily_file(self, date: str = None) -> Path:
        """Get the file path for a specific date's data"""
        if date is None:
            date = datetime.now().strftime('%Y-%m-%d')
        return self.data_dir / f'{date}.json'
    
    def _load_daily_data(self, date: str = None) -> Dict:
        """Load data for a specific date"""
        file_path = self._get_daily_file(date)
        if file_path.exists():
            try:
                with open(file_path, 'r') as f:
                    return json.load(f)
            except:
                pass
        return {
            'date': date or datetime.now().strftime('%Y-%m-%d'),
            'check_ins': [],
            'water_logs': [],
            'snacks': [],
            'meals': [],
            'metrics': {}
        }
    
    def _save_daily_data(self, data: Dict, date: str = None):
        """Save data for a specific date"""
        file_path = self._get_daily_file(date)
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=2, default=str)
    
    # ==================== WATER TRACKING ====================
    
    def log_water(self, amount_ml: int, time: str = None, date: str = None) -> Dict:
        """Log water intake"""
        if time is None:
            time = datetime.now().strftime('%H:%M')
        
        data = self._load_daily_data(date)
        
        water_entry = {
            'time': time,
            'amount_ml': amount_ml,
            'timestamp': datetime.now().isoformat()
        }
        
        data['water_logs'].append(water_entry)
        
        # Update total in metrics
        total_water = sum(w['amount_ml'] for w in data['water_logs'])
        data['metrics']['total_water_ml'] = total_water
        
        self._save_daily_data(data, date)
        
        return {
            'logged': amount_ml,
            'total_today_ml': total_water,
            'goal_ml': 3000,
            'remaining_ml': max(0, 3000 - total_water),
            'percent_complete': min(100, (total_water / 3000) * 100)
        }
    
    def get_water_status(self, date: str = None) -> Dict:
        """Get current water intake status"""
        data = self._load_daily_data(date)
        total_water = sum(w['amount_ml'] for w in data['water_logs'])
        goal = 3000
        
        return {
            'total_ml': total_water,
            'goal_ml': goal,
            'remaining_ml': max(0, goal - total_water),
            'percent_complete': min(100, (total_water / goal) * 100),
            'entries': data['water_logs']
        }
    
    def get_water_recommendation(self) -> str:
        """Get a contextual water recommendation"""
        status = self.get_water_status()
        percent = status['percent_complete']
        hour = datetime.now().hour
        
        if percent < 30 and hour >= 14:
            return "🚨 You're behind on water. Drink 500ml now."
        elif percent < 50 and hour >= 18:
            return "⚠️ Only at 50% water goal. 1.5L to go — start chugging."
        elif percent >= 100:
            return "✅ Water goal hit! Great hydration today."
        elif percent >= 75:
            return "👍 Almost there. 750ml more to reach your goal."
        else:
            remaining = status['remaining_ml']
            return f"💧 {remaining/1000:.1f}L remaining today. Keep sipping."
    
    # ==================== STRESS & ENERGY ====================
    
    def log_check_in(self, stress: int = None, energy: int = None, 
                     mood: str = None, sleep_quality: int = None,
                     notes: str = "") -> Dict:
        """Log a daily check-in with stress/energy levels"""
        check_in = DailyCheckIn(
            date=datetime.now().strftime('%Y-%m-%d'),
            stress_level=stress if stress is not None else 5,
            energy_level=energy if energy is not None else 5,
            mood=mood if mood else "neutral",
            sleep_quality_user=sleep_quality if sleep_quality else 5,
            notes=notes
        )
        
        data = self._load_daily_data()
        data['check_ins'].append(asdict(check_in))
        
        # Update latest metrics
        data['metrics']['latest_stress'] = check_in.stress_level
        data['metrics']['latest_energy'] = check_in.energy_level
        data['metrics']['latest_mood'] = check_in.mood
        
        self._save_daily_data(data)
        
        return asdict(check_in)
    
    def get_today_metrics(self) -> Dict:
        """Get all metrics for today"""
        data = self._load_daily_data()
        water = self.get_water_status()
        
        return {
            'water': water,
            'stress': data['metrics'].get('latest_stress'),
            'energy': data['metrics'].get('latest_energy'),
            'mood': data['metrics'].get('latest_mood'),
            'check_ins_count': len(data['check_ins'])
        }
    
    # ==================== SNACK & MEAL SUGGESTIONS ====================
    
    SNACK_DATABASE = {
        'morning': [
            {'name': 'Greek yogurt with berries', 'calories': 150, 'protein': 15, 'why': 'High protein, low sugar'},
            {'name': 'Apple with almond butter', 'calories': 200, 'protein': 5, 'why': 'Fiber + healthy fats'},
            {'name': 'Hard-boiled eggs (2)', 'calories': 140, 'protein': 12, 'why': 'Pure protein, very filling'},
            {'name': 'Protein shake', 'calories': 120, 'protein': 25, 'why': 'Quick protein boost'},
        ],
        'afternoon': [
            {'name': 'Mixed nuts (small handful)', 'calories': 170, 'protein': 6, 'why': 'Healthy fats, sustained energy'},
            {'name': 'Turkey & cheese roll-ups', 'calories': 150, 'protein': 18, 'why': 'High protein, zero prep'},
            {'name': 'Veggies with hummus', 'calories': 120, 'protein': 4, 'why': 'Fiber + plant protein'},
            {'name': 'Cottage cheese', 'calories': 110, 'protein': 14, 'why': 'Casein protein, slow release'},
        ],
        'evening': [
            {'name': 'Casein protein shake', 'calories': 120, 'protein': 24, 'why': 'Slow-digesting for overnight'},
            {'name': 'Greek yogurt', 'calories': 100, 'protein': 17, 'why': 'Light but protein-rich'},
            {'name': 'Small handful of almonds', 'calories': 160, 'protein': 6, 'why': 'Healthy fats before bed'},
            {'name': 'Herbal tea', 'calories': 0, 'protein': 0, 'why': 'Hydration without calories'},
        ]
    }
    
    MEAL_SUGGESTIONS = {
        'breakfast': [
            {'name': 'Eggs & avocado toast', 'calories': 450, 'protein': 22, 'carbs': 35, 'fat': 28},
            {'name': 'Protein oatmeal with nuts', 'calories': 400, 'protein': 20, 'carbs': 50, 'fat': 15},
            {'name': 'Greek yogurt parfait', 'calories': 350, 'protein': 25, 'carbs': 40, 'fat': 10},
            {'name': 'Veggie omelet', 'calories': 380, 'protein': 28, 'carbs': 15, 'fat': 24},
        ],
        'lunch': [
            {'name': 'Grilled chicken salad', 'calories': 450, 'protein': 45, 'carbs': 20, 'fat': 22},
            {'name': 'Turkey & veggie wrap', 'calories': 500, 'protein': 35, 'carbs': 45, 'fat': 20},
            {'name': 'Salmon with quinoa', 'calories': 550, 'protein': 40, 'carbs': 40, 'fat': 25},
            {'name': 'Buddha bowl (tofu/chicken)', 'calories': 480, 'protein': 30, 'carbs': 50, 'fat': 22},
        ],
        'dinner': [
            {'name': 'Steak with roasted veggies', 'calories': 600, 'protein': 50, 'carbs': 25, 'fat': 35},
            {'name': 'Grilled fish with sweet potato', 'calories': 500, 'protein': 40, 'carbs': 45, 'fat': 18},
            {'name': 'Chicken stir-fry', 'calories': 480, 'protein': 42, 'carbs': 35, 'fat': 20},
            {'name': 'Bunless burger with salad', 'calories': 550, 'protein': 45, 'carbs': 15, 'fat': 35},
        ]
    }
    
    def get_snack_suggestions(self, time_of_day: str = None, calories_remaining: int = None) -> List[Dict]:
        """Get contextual snack suggestions"""
        if time_of_day is None:
            hour = datetime.now().hour
            if hour < 11:
                time_of_day = 'morning'
            elif hour < 17:
                time_of_day = 'afternoon'
            else:
                time_of_day = 'evening'
        
        snacks = self.SNACK_DATABASE.get(time_of_day, self.SNACK_DATABASE['afternoon'])
        
        # Filter by calories if specified
        if calories_remaining:
            snacks = [s for s in snacks if s['calories'] <= calories_remaining]
        
        return snacks[:3]  # Return top 3
    
    def get_meal_suggestions(self, meal_type: str, calories_remaining: int = None, 
                            protein_needed: int = None) -> List[Dict]:
        """Get meal suggestions based on remaining macros"""
        meals = self.MEAL_SUGGESTIONS.get(meal_type, [])
        
        if calories_remaining:
            meals = [m for m in meals if m['calories'] <= calories_remaining + 100]
        
        if protein_needed:
            # Sort by protein content (highest first)
            meals = sorted(meals, key=lambda x: x['protein'], reverse=True)
        
        return meals[:3]
    
    def log_snack(self, snack_name: str, calories: int = 0, protein: int = 0,
                  healthy_rating: int = 3, time: str = None) -> Dict:
        """Log a snack"""
        if time is None:
            time = datetime.now().strftime('%H:%M')
        
        snack = SnackLog(
            date=datetime.now().strftime('%Y-%m-%d'),
            time=time,
            snack_name=snack_name,
            calories=calories,
            protein=protein,
            healthy_rating=healthy_rating
        )
        
        data = self._load_daily_data()
        data['snacks'].append(asdict(snack))
        self._save_daily_data(data)
        
        return asdict(snack)
    
    def log_meal(self, meal_type: str, foods: List[str], calories: int = 0,
                 protein: int = 0, carbs: int = 0, fat: int = 0,
                 satisfaction: int = 3) -> Dict:
        """Log a meal"""
        meal = MealLog(
            date=datetime.now().strftime('%Y-%m-%d'),
            meal_type=meal_type,
            foods=foods,
            calories=calories,
            protein=protein,
            carbs=carbs,
            fat=fat,
            satisfaction=satisfaction
        )
        
        data = self._load_daily_data()
        data['meals'].append(asdict(meal))
        
        # Update daily totals
        current_cals = data['metrics'].get('total_calories', 0)
        current_protein = data['metrics'].get('total_protein', 0)
        data['metrics']['total_calories'] = current_cals + calories
        data['metrics']['total_protein'] = current_protein + protein
        
        self._save_daily_data(data)
        
        return asdict(meal)
    
    # ==================== PATTERN RECOGNITION ====================
    
    def get_weekly_summary(self, days: int = 7) -> Dict:
        """Get a summary of the last N days"""
        summaries = []
        
        for i in range(days):
            date = (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d')
            data = self._load_daily_data(date)
            
            summary = {
                'date': date,
                'water_ml': sum(w['amount_ml'] for w in data['water_logs']),
                'stress_avg': self._avg([c['stress_level'] for c in data['check_ins']]),
                'energy_avg': self._avg([c['energy_level'] for c in data['check_ins']]),
                'total_calories': data['metrics'].get('total_calories', 0),
                'total_protein': data['metrics'].get('total_protein', 0),
            }
            summaries.append(summary)
        
        return {
            'days': summaries,
            'water_average': self._avg([s['water_ml'] for s in summaries]),
            'stress_average': self._avg([s['stress_avg'] for s in summaries]),
            'energy_average': self._avg([s['energy_avg'] for s in summaries]),
        }
    
    def _avg(self, values: List[float]) -> float:
        """Calculate average, filtering out None values"""
        valid = [v for v in values if v is not None]
        return sum(valid) / len(valid) if valid else 0
    
    # ==================== CHECK-IN PROMPTS ====================
    
    def generate_check_in_prompt(self) -> str:
        """Generate a check-in prompt for the user"""
        hour = datetime.now().hour
        metrics = self.get_today_metrics()
        
        prompts = []
        
        # Water check
        water = metrics['water']
        if water['percent_complete'] < 50 and hour >= 14:
            prompts.append(f"💧 Water check: Only {water['percent_complete']:.0f}% of goal. How much have you had?")
        
        # Stress/energy check (once per day, in afternoon)
        if hour >= 14 and hour <= 18 and metrics['check_ins_count'] == 0:
            prompts.append("🧠 Quick check-in: Rate your stress (1-10) and energy (1-10) today.")
        
        return "\n".join(prompts) if prompts else None


# ==================== CLI INTERFACE ====================

if __name__ == '__main__':
    import sys
    
    collector = VitusDataCollection()
    
    if len(sys.argv) < 2:
        print("Usage: python3 data_collection.py [water|stress|energy|snack|meal|status|summary]")
        sys.exit(1)
    
    cmd = sys.argv[1]
    
    if cmd == 'water':
        if len(sys.argv) < 3:
            # Show status
            status = collector.get_water_status()
            print(f"Water today: {status['total_ml']}ml / {status['goal_ml']}ml ({status['percent_complete']:.0f}%)")
            print(collector.get_water_recommendation())
        else:
            # Log water
            amount = int(sys.argv[2])
            result = collector.log_water(amount)
            print(f"Logged {result['logged']}ml. Total: {result['total_today_ml']}ml ({result['percent_complete']:.0f}%)")
    
    elif cmd == 'stress':
        if len(sys.argv) < 3:
            print("Usage: python3 data_collection.py stress <1-10>")
        else:
            level = int(sys.argv[2])
            collector.log_check_in(stress=level)
            print(f"Logged stress level: {level}/10")
    
    elif cmd == 'energy':
        if len(sys.argv) < 3:
            print("Usage: python3 data_collection.py energy <1-10>")
        else:
            level = int(sys.argv[2])
            collector.log_check_in(energy=level)
            print(f"Logged energy level: {level}/10")
    
    elif cmd == 'snack':
        suggestions = collector.get_snack_suggestions()
        print("Snack suggestions:")
        for s in suggestions:
            print(f"  • {s['name']} ({s['calories']} cal, {s['protein']}g protein) — {s['why']}")
    
    elif cmd == 'meal':
        if len(sys.argv) < 3:
            print("Usage: python3 data_collection.py meal [breakfast|lunch|dinner]")
        else:
            meal_type = sys.argv[2]
            suggestions = collector.get_meal_suggestions(meal_type)
            print(f"{meal_type.title()} suggestions:")
            for m in suggestions:
                print(f"  • {m['name']} ({m['calories']} cal, {m['protein']}g protein)")
    
    elif cmd == 'status':
        metrics = collector.get_today_metrics()
        print("Today's Metrics:")
        print(f"  Water: {metrics['water']['total_ml']}ml ({metrics['water']['percent_complete']:.0f}%)")
        if metrics['stress']:
            print(f"  Stress: {metrics['stress']}/10")
        if metrics['energy']:
            print(f"  Energy: {metrics['energy']}/10")
    
    elif cmd == 'summary':
        summary = collector.get_weekly_summary()
        print(f"7-Day Summary:")
        print(f"  Avg water: {summary['water_average']:.0f}ml/day")
        print(f"  Avg stress: {summary['stress_average']:.1f}/10")
        print(f"  Avg energy: {summary['energy_average']:.1f}/10")
    
    else:
        print(f"Unknown command: {cmd}")
        print("Usage: python3 data_collection.py [water|stress|energy|snack|meal|status|summary]")