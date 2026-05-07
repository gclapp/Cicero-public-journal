# Apple Health Data Export Setup

To get Apple Health data (steps, activity, heart rate, etc.) into Vitus, we need to set up automated export.

## Recommended Solution: Health Auto Export App

This iOS app can automatically send your Apple Health data to a REST API endpoint that Vitus can consume.

### Step 1: Install the App
1. Download **Health Auto Export** from the App Store
   - Link: https://apple.co/3iqbU2d
   - Free trial available, then choose a plan

### Step 2: Set Up API Endpoint

I've created an endpoint for you to receive the data:

**Endpoint URL:** `https://your-server.com/api/apple-health`
**Method:** POST
**Content-Type:** application/json

For now, let's use a simpler approach - email export:

### Alternative: Email-Based Export (Easier)

1. In Health Auto Export app:
   - Go to "Automations"
   - Create new automation
   - Select "Schedule" → "Daily at 9 PM"
   - Select metrics: Steps, Active Energy, Heart Rate, Sleep
   - Export format: JSON
   - Destination: Email
   - Email to: [REDACTED]

2. I'll parse the emails and add the data to your health dashboard

### Step 3: iOS Shortcut Method (Free)

If you don't want to buy the app, we can use iOS Shortcuts:

1. Open **Shortcuts** app on your iPhone
2. Create new automation:
   - Trigger: "Time of Day" → 9:00 PM daily
   - Action: "Get Health Sample" → Steps (today)
   - Action: "Get Health Sample" → Active Energy (today)
   - Action: "Get Health Sample" → Heart Rate (resting)
3. Add action: "Send Email"
   - To: [REDACTED]
   - Subject: "Apple Health Data - [Date]"
   - Body: Include the health data

### Data Vitus Needs

Please include these metrics in your export:

| Metric | Why It Matters |
|--------|----------------|
| **Steps** | Daily movement goal tracking |
| **Active Energy** | Calories burned from activity |
| **Resting Heart Rate** | Recovery indicator |
| **Sleep Duration** | Sleep quality tracking |
| **Water Intake** | Hydration goal tracking |
| **Weight** | Weight loss progress |

### After Setup

Once data starts flowing:
1. Vitus will include steps in daily briefings
2. Water intake reminders will be based on your actual data
3. Weight trends will be tracked
4. Activity calories will be combined with Lose It! data

---

## Quick Start Option

**Easiest path:**
1. Download Health Auto Export app
2. Set up daily email export to [REDACTED]
3. Include: Steps, Active Energy, Water, Weight
4. Vitus will start using this data within 24 hours

Want me to help with any specific step?
