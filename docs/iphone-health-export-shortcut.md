# iPhone Shortcut: Health Data Export

## What It Does
Automatically exports your Health data every night and emails it to me.

## Setup (3 minutes)

### Step 1: Create the Shortcut
1. Open **Shortcuts** app
2. Tap **"Automation"** → **"Create Personal Automation"**
3. Select **"Time of Day"**
4. Set: **9:30 PM** (30 min after Lose It!)
5. Repeat: **Daily**
6. Tap **Next**

### Step 2: Add Health Export Actions

**Action 1: Find Health Samples**
1. Tap **"Add Action"**
2. Search: **"Find Health Samples"**
3. Configure:
   - **Category:** Steps
   - **Date:** Today
   - **Group By:** Day

**Action 2: Find More Health Samples**
1. Tap **+** to add another action
2. Search: **"Find Health Samples"**
3. Configure:
   - **Category:** Water
   - **Date:** Today
   - **Group By:** Day

**Action 3: Get Sleep Analysis**
1. Tap **+**
2. Search: **"Find Health Samples"**
3. Configure:
   - **Category:** Sleep
   - **Date:** Today

### Step 3: Format & Send Email

**Action 4: Text**
1. Tap **+**
2. Search: **"Text"**
3. Enter:
```
Health Export - {{Current Date}}

Steps: {{Steps count}} steps
Water: {{Water count}} oz
Sleep: {{Sleep duration}} hours

Sent from iPhone Health
```

**Action 5: Send Email**
1. Tap **+**
2. Search: **"Send Email"**
3. Configure:
   - **To:** [REDACTED]
   - **Subject:** Health Export - {{Current Date}}
   - **Body:** (Select the Text from previous step)

### Step 4: Make It Automatic
1. Toggle **"Ask Before Running"** → **OFF**
2. Tap **"Don't Ask"**
3. Tap **Next**
4. Name it: **"Health Export to Cicero"**
5. Tap **Done**

---

## That's It!

Every night at 9:30 PM, your iPhone will automatically:
1. Read your Health data (steps, water, sleep)
2. Email it to me
3. I'll include it in your morning check-in

**Test it:** Automation → "Health Export to Cicero" → Tap "Run"

---

## What I Receive

```
Health Export - April 5, 2026

Steps: 8,432 steps
Water: 64 oz
Sleep: 6.5 hours
```

**Privacy:** Data is encrypted in transit. Only used for your tracking.