# Heartbeat Check-In Standards
## For Cicero — March 22, 2026

**Status:** ✅ APPROVED — Use for all scheduled check-ins

---

## Schedule

| Check-In | Time (PT) | Purpose |
|----------|-----------|---------|
| **Morning** | 7:00-7:45 AM | Full day preview, all data sources |
| **Midday** | 12:30-12:55 PM | Progress pulse, task status |
| **Afternoon** | 4:30-4:55 PM | Wrap-up prep, remaining tasks |
| **Evening** | 8:30-8:55 PM | Day review, tomorrow preview |

---

## Morning Check-In Format (HTML Email)

### Header Section
```html
<div class="header">
    <h1>☀️ Good Morning!</h1>
    <p>{Day, Month Date, Year}</p>
</div>
```

### Location Bar
```html
<div class="location">
    📍 {City}, {State} — {Status}
</div>
```
**Status options:**
- "Home" (in LA, no travel)
- "Traveling to {City}" (flight today)
- "In {City}" (already there)
- "Returning to LA" (flight back today)

### Weather Section
```html
<div class="weather">
    <div class="weather-city">
        <div class="weather-temp">{emoji} {temp}</div>
        <div>Los Angeles</div>
    </div>
    <div class="weather-city">
        <div class="weather-temp">{emoji} {temp}</div>
        <div>New York</div>
    </div>
</div>
```
**Always show:** LA + NYC (primary locations)
**Add if traveling:** Destination city

### Travel Alert (IF TRAVELING TODAY)
```html
<div class="travel-alert">
    <h3>✈️ TODAY'S TRAVEL</h3>
    <div class="flight">
        <div class="flight-time">{Time}</div>
        <p><strong>{Route}</strong></p>
        <p>Confirmation: {Code}</p>
    </div>
    <div class="hotel">
        <p><strong>🏨 Tonight's Stay</strong></p>
        <p>{Hotel Name}</p>
    </div>
</div>
```

### Stats Dashboard
```html
<div class="stats">
    <div class="stat">
        <div class="stat-number">{count}</div>
        <div class="stat-label">TODOIST TASKS</div>
    </div>
    <div class="stat">
        <div class="stat-number" style="color: {color};">{recovery}%</div>
        <div class="stat-label">WHOOP RECOVERY</div>
    </div>
    <div class="stat">
        <div class="stat-number">{weight}</div>
        <div class="stat-label">LBS</div>
    </div>
</div>
```

**Recovery color coding:**
- 🟢 Green (#16a34a): 70%+
- 🟠 Orange (#ea580c): 50-69%
- 🔴 Red (#dc2626): <50%

### This Week Section
```html
<div class="section">
    <h2>📅 This Week</h2>
    <div class="week-view">
        <!-- 7 days -->
    </div>
</div>
```

**Show:** Next 7 days with:
- Date
- Travel badges (✈️)
- Early flight warnings (🔴)
- Key events

### Health Section
```html
<div class="section">
    <h2>💓 Health</h2>
    <p><strong>Dashboard:</strong> <a href="...">Link</a></p>
    <p><strong>Whoop:</strong> {recovery}% recovery ({status})</p>
    <p><strong>Latest weight:</strong> {weight} lbs</p>
</div>
```

### Footer
```html
<div class="footer">
    <p>🏛️ Cicero | All systems operational</p>
    <p>Last updated: {timestamp}</p>
</div>
```

---

## Data Sources (MANDATORY)

Every morning check-in MUST include:

1. **✅ Location detection** — From calendar events
2. **✅ Weather** — LA + NYC minimum
3. **✅ Todoist tasks** — Today's count
4. **✅ Whoop recovery** — Latest data
5. **✅ Weight** — Latest from tracker
6. **✅ Calendar** — This week's events
7. **✅ Token health** — System status

---

## CSS Standards

### Color Palette
| Element | Color | Hex |
|---------|-------|-----|
| Header gradient start | Blue | #1e40af |
| Header gradient end | Light blue | #3b82f6 |
| Location bar bg | Light blue | #dbeafe |
| Location text | Dark blue | #1e40af |
| Section border | Blue | #3b82f6 |
| Section bg | Light gray | #f8fafc |
| Travel alert bg | Yellow | #fef3c7 |
| Travel alert border | Orange | #f59e0b |
| Hotel bg | Light green | #f0fdf4 |
| Hotel border | Green | #16a34a |

### Typography
- Body: Arial, sans-serif, 16px
- H1: 28px, white
- H2: 20px, color #1e40af
- Stat numbers: 24px, bold
- Stat labels: 11px, uppercase, #666

---

## Token Health Monitoring

**Check on EVERY heartbeat:**
1. Google Calendar token age
2. Whoop API token age
3. Gmail SMTP status
4. Whoop refresh token

**Alert thresholds:**
| Token | Alert At | Action |
|-------|----------|--------|
| Calendar | 6 days | Auto-refresh |
| Whoop | 25 days | Notify user |
| Email | 30 days | Check config |

**If ANY token fails:**
- Include 🔴 ACTION REQUIRED in email
- Attempt automatic recovery
- Provide manual steps if auto-recovery fails

---

## Email Subject Format
```
☀️ Morning Check-In — {Day}, {Month} {Date}, {Year}
```

Examples:
- `☀️ Morning Check-In — Sunday, March 22, 2026`
- `☀️ Morning Check-In — Monday, March 23, 2026`

---

## Files & Scripts

| File | Purpose |
|------|---------|
| `scripts/generate_morning_update_html.py` | Generate HTML morning update |
| `scripts/heartbeat_sender.py` | Queue check-ins (cron) |
| `scripts/deliver_checkin.py` | Deliver via Telegram + Email |
| `scripts/token_health_check.py` | Verify all tokens |
| `config/morning-update-email.html` | Generated output |
| `logs/pending-checkin.json` | Queue file |

---

## Critical Rules

1. **ALWAYS use HTML format** — No plain text emails
2. **ALWAYS include location** — State only, not full address
3. **ALWAYS verify calendar data** — Must be fresh (<1 hour old)
4. **ALWAYS check token health** — Include in every morning email
5. **ALWAYS show both LA and NYC weather** — Primary locations
6. **ALWAYS highlight travel** — Yellow alert box, flight details
7. **ALWAYS show 7-day week view** — For planning

---

## Error Handling

**If calendar data is stale (>1 hour):**
- Show warning: "⚠️ Calendar data may be outdated"
- Attempt refresh
- Include timestamp of last refresh

**If Whoop data unavailable:**
- Show "--" for recovery
- Include note: "Whoop data syncing..."

**If token expired:**
- 🔴 CRITICAL: Token expired
- Include reset instructions
- CC: geoffrey.clapp@progyny.com

---

## Approval

**Approved by:** Geoffrey Clapp  
**Date:** March 22, 2026  
**Status:** ✅ Use as standard for all heartbeat check-ins

---

**Standards file:** `config/heartbeat-standards.md` (this file)  
**Template file:** `config/morning-update-email.html`
