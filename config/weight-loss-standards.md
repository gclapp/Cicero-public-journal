# Weight Loss Email Template Standards
## For Cicero — March 22, 2026

**Status:** ✅ APPROVED by Geoff — Use as standard going forward

---

## Email Structure

### 1. Header Section
```html
<div class="header">
    <h1>🏋️ Weight Loss Program 2026</h1>
    <p>Goal: 20 lbs | Started: Feb 28, 2026 | Managed by Cicero</p>
</div>
```

**Requirements:**
- Green gradient background (#16a34a to #15803d)
- Program name prominent
- Goal, start date, and manager attribution

---

### 2. Stats Dashboard
```html
<div class="stats">
    <div class="stat">
        <div class="stat-number">{lbs_lost}</div>
        <div class="stat-label">Lbs Lost</div>
    </div>
    <div class="stat">
        <div class="stat-number">{percent_to_goal}%</div>
        <div class="stat-label">To Goal</div>
    </div>
    <div class="stat">
        <div class="stat-number">{lbs_per_week}</div>
        <div class="stat-label">Lbs/Week</div>
    </div>
    <div class="stat">
        <div class="stat-number">{current_weight}</div>
        <div class="stat-label">Current</div>
    </div>
</div>
```

**Requirements:**
- 4 stats: Lbs Lost, % to Goal, Lbs/Week, Current Weight
- Large numbers (32px), small labels (12px uppercase)
- Green accent color (#16a34a)

---

### 3. Progress Bar
```html
<div class="progress-bar">
    <div class="progress-fill" style="width: {percent}%"></div>
</div>
<p style="text-align: center; font-size: 12px; color: #666;">Progress to 20 lb goal</p>
```

**Requirements:**
- Green gradient fill
- Percentage label below

---

### 4. Latest Weigh-In Section
```html
<div class="section">
    <h2>📊 Latest Weigh-In</h2>
    <p><span class="success">🎉 New Low!</span> <strong>{weight} lbs</strong> ({date})</p>
    <p>Down <span class="highlight">{change} lbs</span> from last weigh-in — {commentary}</p>
    <p><strong>Total progress:</strong> {total_lost} lbs since {start_date}</p>
</div>
```

**Requirements:**
- Celebrate new lows with 🎉 emoji
- Show change from previous weigh-in
- Include total progress since start

---

### 5. Program Overview Section
```html
<div class="section">
    <h2>🎯 Program Overview</h2>
    <p><strong>Approach:</strong> {approach}</p>
    
    <h3>Nutrition Targets</h3>
    <ul>
        <li><strong>Calories:</strong> {range}</li>
        <li><strong>Protein:</strong> {range} ({percent})</li>
        <li><strong>Carbs:</strong> {percent} (complex only)</li>
        <li><strong>Fats:</strong> {percent} (healthy fats)</li>
    </ul>

    <h3>Exercise Schedule</h3>
    <ul>
        <li><strong>Mon/Wed/Fri:</strong> Strength training (45 min)</li>
        <li><strong>Tue:</strong> Cardio/walk (30-40 min)</li>
        <li><strong>Thu:</strong> Active recovery/yoga (30 min)</li>
        <li><strong>Sat:</strong> Fun activity/hike (60+ min)</li>
        <li><strong>Sun:</strong> Rest (Whoop recovery focus)</li>
    </ul>
</div>
```

---

### 6. Weight History Table
```html
<div class="section">
    <h2>📈 Weight History</h2>
    <table>
        <tr>
            <th>Date</th>
            <th>Weight</th>
            <th>Change</th>
            <th>Notes</th>
        </tr>
        <!-- Rows -->
    </table>
</div>
```

**Requirements:**
- Green header row
- Highlight new lows with 🎉
- Show change from previous
- Notes column for context

---

### 7. Daily Habits Checklist
```html
<div class="section">
    <h2>✅ Daily Habits Checklist</h2>
    <ul class="checklist">
        <li>Weigh-in (morning)</li>
        <li>Log all food in Lose It!</li>
        <li>Hit protein target (150-180g)</li>
        <li>Complete workout</li>
        <li>Drink 8+ glasses water</li>
        <li>Check Whoop recovery</li>
        <li>7+ hours sleep</li>
    </ul>
</div>
```

---

### 8. Weekly Goal Section (WHEN APPLICABLE)
```html
<div class="section" style="background: #fef3c7; border-left-color: #f59e0b;">
    <h2>🎯 THIS WEEK'S GOAL: Lose {X} lbs by {Day} {Time}</h2>
    <p><strong>Target:</strong> {start} → <span class="highlight">{target} lbs</span> by {deadline}</p>
    
    <h3>📋 The Math</h3>
    <ul>
        <li><strong>{X} lbs in {Y} days</strong> = {Z} lbs/day deficit</li>
        <li><strong>Required daily deficit:</strong> ~{calories} calories</li>
        <li><strong>Current burn:</strong> ~{range} calories/day</li>
        <li><strong>Target intake:</strong> {range} calories/day</li>
    </ul>
    
    <h3>🎯 Action Plan</h3>
    <table>
        <tr>
            <th>Day</th>
            <th>Calories</th>
            <th>Focus</th>
        </tr>
        <!-- Day-by-day plan -->
    </table>
    
    <h3>⚡ Accelerators</h3>
    <ul>
        <li><strong>10k steps daily</strong></li>
        <li><strong>No alcohol</strong> until {date}</li>
        <li><strong>{X}g protein daily</strong></li>
        <li><strong>{X}L water daily</strong></li>
        <li><strong>Early sleep</strong></li>
    </ul>
</div>
```

**Styling:** Yellow background (#fef3c7), orange border (#f59e0b) for emphasis

---

### 9. Cortisol/Stress Section (WHEN APPLICABLE)
```html
<div class="section" style="background: #ede9fe; border-left-color: #7c3aed;">
    <h2>🧠 Cortisol, Stress & Weight Loss</h2>
    <p><strong>Key Insight:</strong> {insight}</p>
    
    <h3>How Cortisol Affects Weight Loss</h3>
    <ul>
        <li><strong>Elevated cortisol</strong> = increased appetite, cravings</li>
        <li><strong>Chronic stress</strong> = body holds onto fat</li>
        <li><strong>Poor sleep</strong> = cortisol spike + reduced willpower</li>
    </ul>
    
    <h3>Recovery Pattern</h3>
    <table>
        <!-- Recovery data -->
    </table>
    
    <h3>🎯 Cortisol Management</h3>
    <ul>
        <li><strong>Sleep priority:</strong> 7+ hours</li>
        <li><strong>Morning light:</strong> 10 min outdoor</li>
        <li><strong>Breathing:</strong> 4-7-8 technique</li>
    </ul>
</div>
```

**Styling:** Purple background (#ede9fe), purple border (#7c3aed)

---

### 10. Travel Strategy (WHEN APPLICABLE)
```html
<div class="section">
    <h2>🧳 Travel Strategy ({Timeframe})</h2>
    <p><strong>Trip:</strong> {route}</p>
    
    <h3>Travel Rules</h3>
    <ul>
        <li>✈️ Pack protein bars for flights</li>
        <li>🚫 No sugary drinks at airports</li>
        <li>🚶 Walk everywhere</li>
        <li>🍽 Focus meals on protein + vegetables</li>
        <li>🏨 Hotel gym: 20-min sessions</li>
    </ul>
</div>
```

---

### 11. Success Metrics Table
```html
<div class="section">
    <h2>🎯 Success Metrics</h2>
    <table>
        <tr>
            <th>Metric</th>
            <th>Target</th>
            <th>Current</th>
        </tr>
        <tr>
            <td>Weight Loss</td>
            <td>20 lbs</td>
            <td class="success">{X} lbs ✅</td>
        </tr>
        <!-- More rows -->
    </table>
</div>
```

---

### 12. App Integration Section
```html
<div class="section">
    <h2>📱 App Integration</h2>
    <ul>
        <li><strong>Whoop:</strong> Recovery, strain, sleep ✅</li>
        <li><strong>Lose It!:</strong> Food logging ✅</li>
        <li><strong>Apple Health:</strong> Central data hub ✅</li>
        <li><strong>Todoist:</strong> Daily reminders ✅</li>
    </ul>
    <p><strong>Dashboard:</strong> <a href="{url}">{url}</a></p>
</div>
```

---

### 13. Long-Term Milestones
```html
<div class="section">
    <h2>🎯 Long-Term Milestones</h2>
    <ul>
        <li><strong>{weight} lbs:</strong> {X} lbs lost</li>
        <li><strong>{weight} lbs:</strong> Halfway point</li>
        <li><strong>{weight} lbs:</strong> 🎉 GOAL REACHED!</li>
    </ul>
    <p><em>At current pace: Goal reached by {date}</em></p>
</div>
```

---

### 14. Footer
```html
<div class="footer">
    <p>🏛️ Managed by Cicero | Last Updated: {date}</p>
    <p>Questions? Reply to this email or message me on Telegram.</p>
</div>
```

---

## CSS Standards

### Color Palette
| Element | Color | Hex |
|---------|-------|-----|
| Primary green | #16a34a | Header, accents |
| Dark green | #166534 | Headings |
| Light green bg | #f0fdf4 | Stats, highlights |
| Yellow highlight | #fef3c7 | Goals, warnings |
| Orange | #f59e0b | Borders, emphasis |
| Purple | #7c3aed | Cortisol section |
| Purple bg | #ede9fe | Cortisol background |

### Typography
- Body: Arial, sans-serif, 16px
- Section headings: 20px, color #166534
- Stat numbers: 32px, bold, color #16a34a
- Stat labels: 12px, uppercase, color #666

---

## Conditional Sections

Include these sections based on context:

| Section | Include When |
|---------|--------------|
| Weekly Goal | Specific short-term target set |
| Cortisol/Stress | Whoop recovery data shows stress pattern |
| Travel Strategy | Upcoming travel in next 7 days |
| Success Metrics | Any metric tracking needed |

---

## Email Subject Format
```
🏋️ Weight Loss Program {+ Context} — {Date}
```

Examples:
- `🏋️ Weight Loss Program Update — March 22, 2026`
- `🏋️ Weight Loss Program + Cortisol Strategy — March 22, 2026`
- `🏋️ Weight Loss Program Weekly Check-In — March 29, 2026`

---

## Approval

**Approved by:** Geoffrey Clapp  
**Date:** March 22, 2026  
**Status:** ✅ Use as standard going forward

---

**Template file:** `config/weight-loss-email.html`  
**Standards file:** `config/weight-loss-standards.md` (this file)
