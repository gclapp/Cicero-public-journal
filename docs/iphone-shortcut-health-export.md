# iPhone Shortcut: Auto-Export Health Data to Cicero

## What This Shortcut Does
- Runs every night at 9:00 PM automatically
- Exports your Apple Health data (nutrition, weight, sleep, workouts)
- Emails the export to [REDACTED]
- Cicero processes it and updates your daily tracking

---

## Step-by-Step Setup

### Step 1: Open Shortcuts App
1. Find and open the **Shortcuts** app on your iPhone
2. Tap **"Automation"** at the bottom
3. Tap **"Create Personal Automation"** (or + if you have existing automations)

### Step 2: Set Trigger
1. Select **"Time of Day"**
2. Set time: **9:00 PM**
3. Select **"Daily"**
4. Tap **"Next"**

### Step 3: Add Actions

**Action 1: Export Health Data**
1. Tap **"Add Action"**
2. Search: **"Export Health Data"**
3. Select it
4. (Optional) Choose specific data types:
   - Body Measurements (weight)
   - Nutrition (calories, protein, carbs, fat)
   - Sleep Analysis
   - Workouts

**Action 2: Send Email**
1. Tap **"+"** to add another action
2. Search: **"Send Email"**
3. Select it
4. Configure:
   - **To:** [REDACTED]
   - **Subject:** Health Export - {{Current Date}}
   - **Body:** (leave blank or add note)
   - **Attachment:** Health Export (magic variable from previous step)

### Step 4: Turn Off "Ask Before Running"
1. Before saving, toggle **"Ask Before Running"** to **OFF**
2. This allows it to run automatically without your input
3. Tap **"Don't Ask"** to confirm

### Step 5: Save
1. Tap **"Next"**
2. Name it: **"Health Export to Cicero"**
3. Tap **"Done"**

---

## Testing the Shortcut

**Manual Test:**
1. Go to **Automation** tab
2. Find "Health Export to Cicero"
3. Tap it, then tap **"Run"**
4. Check if email arrives at [REDACTED]

**Check Timing:**
- First automatic run: Tonight at 9:00 PM
- Check your email sent folder to confirm it sent

---

## What Happens Next

**Every Night at 9 PM:**
1. iPhone exports Health data
2. Emails it to Cicero automatically
3. Cicero processes and extracts:
   - Daily calories
   - Protein/carbs/fat
   - Weight
   - Sleep hours
   - Workout data

**In Your Morning Check-In:**
- Yesterday's nutrition summary
- Weight trend
- Sleep analysis
- Workout recap

---

## Troubleshooting

**"Export Health Data" not found?**
- Make sure you're on iOS 16+
- Try searching "Health" and look through all options

**Email not sending?**
- Check Mail app is configured
- Verify [REDACTED] is correct

**Data not showing in check-in?**
- Email may take a few minutes to arrive
- Cicero processes it within 1 hour of receipt

---

## Privacy Note

- Health data is encrypted in transit (email)
- Stored securely on Cicero's server
- Only used for your personal tracking
- Never shared or transmitted elsewhere

---

**Need help?** Text me a screenshot of where you're stuck.