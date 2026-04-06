# iPhone Health Export Shortcut

## What It Does
Automatically exports your Health data (steps, water, sleep) every night at 9:30 PM and emails it to [REDACTED].

---

## Setup Steps

### 1. Create Automation
1. Open **Shortcuts** app
2. Tap **"Automation"** at bottom
3. Tap **"Create Personal Automation"** (or "+" if you have automations)
4. Select **"Time of Day"**
5. Set time: **9:30 PM**
6. Repeat: **Daily**
7. Tap **Next**

### 2. Add Health Actions

**Steps:**
1. Tap **"Add Action"**
2. Search: **"Find Health Samples"**
3. Tap it
4. Configure:
   - Category: **Steps**
   - Date: **Today**
   - Group By: **Day**

**Water:**
1. Tap **+** (below the Steps action)
2. Search: **"Find Health Samples"**
3. Configure:
   - Category: **Dietary Water**
   - Date: **Today**
   - Group By: **Day**

**Sleep:**
1. Tap **+**
2. Search: **"Find Health Samples"**
3. Configure:
   - Category: **Sleep Analysis**
   - Date: **Today**

### 3. Format the Data

1. Tap **+**
2. Search: **"Text"**
3. Enter this exact text:

```
Health Export - {{Current Date}}

Steps: {{Steps}} steps
Water: {{Water}} oz  
Sleep: {{Sleep}} hours

Data from Apple Health
```

**Note:** The {{}} variables will auto-fill when you select the Health samples above.

### 4. Send Email

1. Tap **+**
2. Search: **"Send Email"**
3. Configure:
   - **To:** [REDACTED]
   - **Subject:** Health Export - {{Current Date}}
   - **Body:** (Tap "Text" and select the formatted text from step 3)

### 5. Make It Automatic

1. Toggle **"Ask Before Running"** → **OFF**
2. Tap **"Don't Ask"** to confirm
3. Tap **Next**
4. Name: **"Health Export to Cicero"**
5. Tap **Done**

---

## Test It

1. In Shortcuts app, go to **Automation**
2. Find **"Health Export to Cicero"**
3. Tap it
4. Tap **"Run"** (play button)
5. Check that email arrives at [REDACTED]

---

## What I Receive

```
Health Export - Monday, April 6, 2026

Steps: 8,432 steps
Water: 64 oz
Sleep: 7.2 hours

Data from Apple Health
```

---

## Troubleshooting

**"No Health data found"**
- Make sure you have an Apple Watch or iPhone is tracking steps
- Water must be logged manually in Health app (or via other apps)
- Sleep requires Apple Watch or manual entry

**Email not sending**
- Check Mail app is configured
- Verify [REDACTED] address is correct

**Shortcut not running**
- Check Settings → Shortcuts → Allow Untrusted Shortcuts is ON
- Ensure automation is enabled (toggle is green)

---

## Privacy

- Data is encrypted in transit (TLS)
- Only used for your morning check-ins
- Stored securely, never shared
