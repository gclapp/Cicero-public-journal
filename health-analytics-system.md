# Apple Health + Whoop Analytics System
## Automated Health Dashboard & Reporting

**Purpose:** Track weight loss, fitness, and recovery metrics automatically  
**Data Sources:** Apple Health (primary) + Whoop (supplementary)  
**Output:** Web dashboard + Weekly email reports  
**Update Frequency:** Daily (automatic), Weekly (reports)

---

## 📊 SYSTEM ARCHITECTURE

### Data Flow

```
Apple Health (iPhone)
    ↓ (Export via Shortcuts - daily/weekly)
XML Data File
    ↓ (Parse & process)
Python Analytics Engine
    ↓ (Generate insights)
Dashboard + Email Reports
    ↓
You see trends, correlations, progress
```

### Whoop Integration

```
Whoop App
    ↓ (API or manual export)
Recovery, Strain, Sleep Data
    ↓ (Merge with Apple Health)
Enhanced Analytics
    ↓
Better insights (recovery vs. weight loss)
```

---

## 🏗️ COMPONENTS

### 1. iPhone Shortcuts (Data Collection)

**Shortcut: "Send Health Data to Cicero"**
- Runs automatically: Daily at 9 PM or Weekly on Sundays
- Exports Apple Health data (last 7 days)
- Emails XML file to: [REDACTED]
- Alternative: Saves to iCloud, I pull from there

**What it exports:**
- Body Measurements (weight, body fat %)
- Activity (steps, distance, flights climbed)
- Workouts (type, duration, calories, heart rate)
- Sleep (hours, quality if available)
- Nutrition (from Lose It!)
- Heart Rate (resting, walking average)

### 2. Python Data Processor

**Script: `health_processor.py`**
- Parses Apple Health XML export
- Extracts key metrics
- Calculates trends and correlations
- Generates insights
- Updates dashboard data

**Analytics it performs:**
- Weight trend (7-day moving average)
- Caloric balance (in vs. out)
- Step count trends
- Workout frequency & intensity
- Sleep quality vs. weight loss correlation
- Recovery patterns (with Whoop data)

### 3. Web Dashboard

**URL:** https://gclapp.github.io/health-dashboard/

**Features:**
- Weight loss chart (daily + trend line)
- Calorie dashboard (intake vs. burn)
- Activity rings (steps, workouts, active calories)
- Sleep analysis
- Weekly progress summary
- Month-over-month comparison
- Goal tracking (20 lbs target)

**Sections:**
1. **Overview:** Current status, progress to goal
2. **Weight:** Charts, trends, predictions
3. **Activity:** Steps, workouts, calories burned
4. **Nutrition:** Calories consumed (from Lose It!)
5. **Sleep:** Hours, quality trends
6. **Recovery:** Whoop recovery scores
7. **Insights:** AI-generated observations

### 4. Weekly Email Reports

**Sent every Sunday evening:**
- Week summary (weight change, workouts, steps)
- Progress to 20-lb goal
- What worked well this week
- Recommendations for next week
- Charts and visualizations
- Recovery trends (Whoop data)

### 5. Whoop Integration Layer

**Enhanced metrics Whoop provides:**
- Recovery score (0-100%)
- Strain score (workout intensity)
- Sleep performance (deep, REM, light)
- HRV (heart rate variability)
- Respiratory rate
- Skin temperature

**How we use it:**
- Correlation: High recovery days → better weight loss?
- Optimization: When to push hard vs. rest
- Sleep quality impact on progress
- Strain vs. calorie burn validation

---

## 📱 IPHONE SHORTCUT SETUP

### Step 1: Create "Export Health Data" Shortcut

1. Open **Shortcuts** app
2. Tap **+** to create new shortcut
3. Add actions:

```
Action 1: "Get Health Sample"
- Type: Body Mass (Weight)
- Start Date: 7 days ago
- End Date: Today

Action 2: "Get Health Sample"  
- Type: Steps
- Start Date: 7 days ago
- End Date: Today

Action 3: "Get Health Sample"
- Type: Workouts
- Start Date: 7 days ago
- End Date: Today

Action 4: "Send Email"
- To: [REDACTED]
- Subject: Apple Health Export - [Current Date]
- Body: [Combine all data]
- Attachment: [Health data]
```

### Step 2: Automate It

1. Tap **Automation** tab
2. Create **Personal Automation**
3. Choose **Time of Day**
4. Set: 9:00 PM daily OR Sundays at 8:00 PM weekly
5. Action: Run "Export Health Data" shortcut
6. Turn OFF "Ask Before Running"

**Alternative: Manual Export Weekly**
If automation is tricky, just manually run the shortcut Sundays:
- Open Shortcuts
- Tap "Export Health Data"
- It emails me automatically

---

## 🐍 PYTHON DATA PROCESSING

### Data Parser

```python
# health_processor.py - Key functions

import xml.etree.ElementTree as ET
import pandas as pd
from datetime import datetime, timedelta

class HealthDataProcessor:
    def __init__(self, xml_file):
        self.tree = ET.parse(xml_file)
        self.root = self.tree.getroot()
        self.data = self._parse_xml()
    
    def _parse_xml(self):
        """Extract all health records from XML"""
        records = []
        for record in self.root.findall('Record'):
            records.append({
                'type': record.get('type'),
                'start_date': record.get('startDate'),
                'end_date': record.get('endDate'),
                'value': record.get('value'),
                'unit': record.get('unit')
            })
        return pd.DataFrame(records)
    
    def get_weight_data(self):
        """Extract weight measurements"""
        weight_df = self.data[self.data['type'] == 'BodyMass']
        weight_df['date'] = pd.to_datetime(weight_df['start_date'])
        weight_df['weight_lbs'] = weight_df['value'].astype(float) * 2.20462  # kg to lbs
        return weight_df[['date', 'weight_lbs']].sort_values('date')
    
    def get_steps_data(self):
        """Extract daily step counts"""
        steps_df = self.data[self.data['type'] == 'StepCount']
        steps_df['date'] = pd.to_datetime(steps_df['start_date']).dt.date
        steps_df['steps'] = steps_df['value'].astype(int)
        return steps_df.groupby('date')['steps'].sum().reset_index()
    
    def get_workouts(self):
        """Extract workout data"""
        workout_df = self.data[self.data['type'].str.contains('Workout', na=False)]
        workout_df['date'] = pd.to_datetime(workout_df['start_date'])
        workout_df['duration'] = workout_df['value'].astype(float)
        return workout_df[['date', 'type', 'duration']]
    
    def calculate_7day_trend(self, data, column):
        """Calculate 7-day moving average"""
        data['7day_avg'] = data[column].rolling(window=7, min_periods=1).mean()
        return data
    
    def generate_weekly_summary(self):
        """Generate summary stats for the week"""
        weight = self.get_weight_data()
        steps = self.get_steps_data()
        workouts = self.get_workouts()
        
        summary = {
            'weight_start': weight['weight_lbs'].iloc[0],
            'weight_end': weight['weight_lbs'].iloc[-1],
            'weight_change': weight['weight_lbs'].iloc[-1] - weight['weight_lbs'].iloc[0],
            'avg_steps': steps['steps'].mean(),
            'total_workouts': len(workouts),
            'total_workout_minutes': workouts['duration'].sum()
        }
        return summary
```

### Dashboard Generator

```python
# dashboard_generator.py

import json
from datetime import datetime

class DashboardGenerator:
    def __init__(self, health_data):
        self.data = health_data
        self.dashboard_data = {}
    
    def generate_json(self):
        """Generate JSON for web dashboard"""
        self.dashboard_data = {
            'last_updated': datetime.now().isoformat(),
            'weight_data': self._get_weight_chart_data(),
            'steps_data': self._get_steps_chart_data(),
            'workouts_data': self._get_workouts_data(),
            'summary': self._get_summary_stats(),
            'insights': self._generate_insights()
        }
        return json.dumps(self.dashboard_data, indent=2)
    
    def save_dashboard_data(self, filepath):
        """Save JSON for dashboard"""
        with open(filepath, 'w') as f:
            f.write(self.generate_json())
```

---

## 📊 DASHBOARD FEATURES

### 1. Weight Tracking

**Visualizations:**
- Line chart: Daily weight + 7-day trend line
- Goal progress bar: % to 20 lbs
- Prediction: "At current rate, you'll hit goal by [date]"
- Weekly change indicator

### 2. Activity Dashboard

**Visualizations:**
- Steps: Daily bars + 7-day average
- Workouts: Calendar heatmap (frequency)
- Active calories: Weekly burn vs. intake
- Move ring: Daily completion %

### 3. Nutrition & Calories

**From Lose It! via Apple Health:**
- Daily calorie intake
- Calorie deficit calculation
- Weekly average
- Macro breakdown (if available)

### 4. Sleep Analysis

**Visualizations:**
- Hours slept per night
- Sleep quality trend
- Correlation: Sleep vs. weight change
- Bedtime/wake time consistency

### 5. Recovery (Whoop Integration)

**Visualizations:**
- Recovery score over time
- Strain vs. Recovery balance
- Sleep performance vs. weight loss
- HRV trends (fitness indicator)

### 6. Insights (AI-Generated)

**Weekly observations:**
- "You lose more weight on days with 8+ hours sleep"
- "Steps above 10k correlate with better recovery"
- "Week 3: Your consistency is paying off"
- "Consider adding more protein on workout days"

---

## 📧 WEEKLY EMAIL REPORT

### Template Structure

```
Subject: Health Report Week of [Date] - [Weight Change] lbs

Hi Geoff,

Here's your weekly health summary:

📊 WEIGHT PROGRESS
Current: [XXX] lbs (down [X.X] lbs this week)
Goal: 20 lbs
Progress: [XX]% complete
Trend: On track / Ahead / Adjust needed

🏃 ACTIVITY
Steps: [XX,XXX] avg/day
Workouts: [X] sessions ([XXX] minutes)
Active calories: [X,XXX] avg/day

😴 SLEEP
Avg hours: [X.X]
Quality score: [XX]%
Best night: [Day] ([X] hours)

💪 RECOVERY (Whoop)
Avg recovery: [XX]%
Best day: [Day] ([XX]%)
Strain balance: Good / High / Low

📈 INSIGHTS
- [Personalized insight 1]
- [Personalized insight 2]
- [Personalized insight 3]

🎯 NEXT WEEK
- Recommendation 1
- Recommendation 2

View full dashboard: https://gclapp.github.io/health-dashboard/

🏛️ — Cicero
```

---

## 🚀 SETUP STEPS

### Phase 1: iPhone Setup (This Weekend)

1. **Create Shortcuts automation**
   - Build "Export Health Data" shortcut
   - Set to run Sundays at 8 PM
   - Test it works

2. **Enable Apple Health permissions**
   - Ensure Lose It! can write to Health
   - Ensure Shortcuts can read Health data
   - Allow Whoop to read/write Health data

### Phase 2: Dashboard Setup (Week 1)

1. **Create GitHub repo** for dashboard
2. **Build HTML/CSS/JS dashboard**
3. **Test with sample data**
4. **Deploy to GitHub Pages**

### Phase 3: Automation (Week 2)

1. **Set up Python scripts** on server
2. **Create cron job** to process data weekly
3. **Test email reports**
4. **Fine-tune insights**

### Phase 4: Whoop Integration (Week 3)

1. **Set up Whoop API** (if available)
2. **Or create manual export process**
3. **Merge Whoop data with Apple Health**
4. **Enhanced analytics**

---

## 📋 TODOIST TASKS

I'll add these to your "Weight Loss 2026" project:

**Setup Tasks:**
- Create iPhone Shortcuts automation for Health export
- Test Health data export (send to Cicero)
- Enable all Health permissions for Shortcuts
- Connect Whoop to Apple Health (if not done)

**Ongoing:**
- Review weekly health report (Sundays)
- Check dashboard trends (as needed)
- Export Whoop data monthly (if manual)

---

## 🎯 WHAT YOU'LL GET

### Daily
- Automatic data export (invisible to you)
- Dashboard updates with latest data

### Weekly
- Comprehensive email report
- Insights and recommendations
- Progress tracking

### Monthly
- Trend analysis
- Pattern identification
- Plan adjustments

### Anytime
- Web dashboard with all metrics
- Historical data
- Goal tracking

---

## 💡 ADVANCED FEATURES (Future)

Once basics work, we can add:

1. **Predictive analytics:** "Based on trends, you'll hit goal by [date]"
2. **Anomaly detection:** "Your weight spiked—check sodium intake"
3. **Comparative analysis:** "This week vs. last week vs. average"
4. **Photo timeline:** Side-by-side progress photos
5. **Meal correlation:** "You lose more on high-protein days"
6. **Travel mode:** Special tracking during NYC trips

---

## 🔐 PRIVACY & SECURITY

- All data stored in your GitHub repo (private)
- No third-party services (except GitHub)
- You control all data
- Can delete anytime
- HIPAA-style best practices

---

## 📈 SUCCESS METRICS

**System works when:**
- Data exports automatically
- Dashboard updates regularly
- Weekly reports arrive Sundays
- Insights are accurate and useful
- You check dashboard 2-3x/week

---

Ready to build this? I'll start with:
1. Creating the iPhone Shortcuts guide
2. Building the dashboard framework
3. Setting up the data processing scripts

This will be your mission control for the 20-pound goal! 🎯