# Apple Shortcuts Health Data Setup Guide

**Last Updated:** May 25, 2026  
**Purpose:** Send water intake and step count from Apple Health to Cicero via email  
**From:** gclapp@mac.com  
**To:** [REDACTED]

---

## ⚠️ CRITICAL: Two Different Formats

Water and Steps use **completely different formats**. This is the #1 reason shortcuts fail.

| Data Type | Format | Where Data Lives |
|-----------|--------|------------------|
| **Water** | `.txt` attachments | Filename = ounces (e.g., `64.txt`) |
| **Steps** | Email body text | One line per day: `2026-05-25:10500` |

---

## Part 1: Water Intake Shortcut

### Expected Email Format

The system expects **multiple .txt file attachments** where:
- **Filename** = water amount in ounces (e.g., `48.txt`, `72.txt`, `64.txt`)
- **File content** = Can be empty or any text (only filename matters)
- **Number of files** = One per day of history (typically 10-14 days)

### Step-by-Step Shortcut Configuration

#### 1. Create the Automation
1. Open **Shortcuts** app on iPhone
2. Tap **"Automation"** tab (bottom)
3. Tap **"Create Personal Automation"** (or + if you have existing automations)
4. Select **"Time of Day"**
5. Set time: **9:00 PM** (or your preferred time)
6. Repeat: **Daily**
7. Tap **Next**

#### 2. Add "Find Health Samples" Action
1. Tap **"Add Action"**
2. Search: **"Find Health Samples"**
3. Configure EXACTLY as follows:
   - **Category:** ⚠️ **Dietary Water** (NOT just "Water")
   - **Start Date:** Tap and select **"In the last 14 days"**
   - **Group By:** **Day**
   - **Fill Missing:** **OFF** (critical - prevents fake zero data)
   - **Sort By:** **Start Date**
   - **Order:** **Oldest First**
4. Tap **Next**

#### 3. Add "Repeat with Each" Loop
1. Tap **+** to add another action
2. Search: **"Repeat"**
3. Select **"Repeat with Each"**
4. It should automatically use the Health Samples as input

#### 4. Inside the Loop - Create Text Files

**For each item in the loop, add these actions:**

**Action A: Get Numbers from Input**
1. Tap **+** inside the repeat block
2. Search: **"Get Numbers from Input"**
3. Tap **"Input"** variable
4. Select **"Quantity"** (this is the water amount)
5. Result: `Number` variable

**Action B: Round Number**
1. Tap **+**
2. Search: **"Round"**
3. Select the `Number` variable
4. Round to: **0 decimal places**
5. Result: `Rounded Number`

**Action C: Create Text File**
1. Tap **+**
2. Search: **"Text"**
3. Enter any content (e.g., "Water data")
4. Result: `Text` variable

**Action D: Set Name**
1. Tap **+**
2. Search: **"Set Name"**
3. Select the `Text` variable
4. Name: Tap and select **"Ask Each Time"** → then select `Rounded Number` variable
5. ⚠️ **CRITICAL:** Append `.txt` to the name
   - Tap the name field
   - It should look like: `Rounded Number.txt`
6. Result: `Renamed Item`

**Action E: Add to Variable**
1. Tap **+**
2. Search: **"Add to Variable"**
3. Variable name: **Files** (create new variable)
4. Content: `Renamed Item`

#### 5. After the Loop - Send Email

1. Tap to exit the repeat block (outside the loop)
2. Tap **+**
3. Search: **"Send Email"**
4. Configure:
   - **To:** `[REDACTED]`
   - **Subject:** `Water Update`
   - **Body:** Can be empty or simple text like "Daily water export"
   - **Attachments:** Tap and select the `Files` variable
5. Tap **Next**

#### 6. Disable "Ask Before Running"
1. Toggle **"Ask Before Running"** → **OFF**
2. Tap **"Don't Ask"** to confirm
3. Tap **Done**

---

## Part 2: Steps Shortcut

### Expected Email Format

The system expects **plain text in the email body** with this exact format:

```
Steps Export - Monday, May 25, 2026

2026-05-11:8234
2026-05-12:10500
2026-05-13:7200
2026-05-14:9800
2026-05-15:11200
2026-05-16:8900
2026-05-17:7600
2026-05-18:9200
2026-05-19:10800
2026-05-20:8400
2026-05-21:9500
2026-05-22:10100
2026-05-23:7800
2026-05-24:8900
2026-05-25:10500
```

**Format rules:**
- One line per day
- Format: `YYYY-MM-DD:STEP_COUNT`
- No spaces around the colon
- No commas in the step count
- Oldest date first, newest last

### Step-by-Step Shortcut Configuration

#### 1. Create the Automation
1. Open **Shortcuts** app
2. Tap **"Automation"** tab
3. Tap **"Create Personal Automation"**
4. Select **"Time of Day"**
5. Set time: **9:00 PM**
6. Repeat: **Daily**
7. Tap **Next**

#### 2. Add "Find Health Samples" Action
1. Tap **"Add Action"**
2. Search: **"Find Health Samples"**
3. Configure:
   - **Category:** **Steps**
   - **Start Date:** **"In the last 14 days"**
   - **Group By:** **Day**
   - **Fill Missing:** **OFF**
   - **Sort By:** **Start Date**
   - **Order:** **Oldest First**
4. Tap **Next**

#### 3. Add "Repeat with Each" Loop
1. Tap **+**
2. Search: **"Repeat"**
3. Select **"Repeat with Each"**
4. Input should be Health Samples

#### 4. Inside the Loop - Build Text Lines

**Action A: Format Date**
1. Tap **+** inside repeat block
2. Search: **"Format Date"**
3. Tap **"Date"** variable
4. Select **"Start Date"** (from Repeat Item)
5. Format: **Custom**
6. Custom format: `yyyy-MM-dd`
7. Result: `Formatted Date`

**Action B: Get Numbers from Input**
1. Tap **+**
2. Search: **"Get Numbers from Input"**
3. Tap **"Input"**
4. Select **"Quantity"** (this is the step count)
5. Result: `StepCount`

**Action C: Text (Create the Line)**
1. Tap **+**
2. Search: **"Text"**
3. Enter: Tap the text field
4. Select `Formatted Date` variable
5. Type a colon: `:`
6. Select `StepCount` variable
7. Final should look like: `{{Formatted Date}}:{{StepCount}}`
8. Result: `DayLine`

**Action D: Add to Variable**
1. Tap **+**
2. Search: **"Add to Variable"**
3. Variable name: **AllLines** (create new)
4. Content: `DayLine`
5. ⚠️ **CRITICAL:** Tap "New Lines" for separator

#### 5. After the Loop - Send Email

1. Exit the repeat block
2. Tap **+**
3. Search: **"Send Email"**
4. Configure:
   - **To:** `[REDACTED]`
   - **Subject:** `Steps {{Current Date}}`
   - **Body:** Create a Text action first:
     ```
     Steps Export - {{Current Date}}
     
     {{AllLines}}
     ```
   - **NO ATTACHMENTS** - data goes in body only!
5. Tap **Next**

#### 6. Disable "Ask Before Running"
1. Toggle **"Ask Before Running"** → **OFF**
2. Tap **"Don't Ask"**
3. Tap **Done**

---

## Part 3: Testing Your Shortcuts

### Test Water Shortcut

1. Open **Shortcuts** app
2. Tap **"Automation"** tab
3. Find your "Water Update" automation
4. Tap it
5. Tap **"Run"** (play button)
6. Check email arrives at [REDACTED]

**Verify:**
- [ ] Email has subject "Water Update"
- [ ] Email has multiple .txt attachments
- [ ] Filenames are numbers like `48.txt`, `72.txt`
- [ ] Files represent last 14 days of water data

### Test Steps Shortcut

1. Open **Shortcuts** app
2. Tap **"Automation"** tab
3. Find your "Steps" automation
4. Tap it
5. Tap **"Run"**
6. Check email arrives

**Verify:**
- [ ] Email has subject like "Steps May 25, 2026"
- [ ] Email body contains lines like `2026-05-25:10500`
- [ ] One line per day, oldest first
- [ ] NO attachments

---

## Part 4: Troubleshooting

### Problem: Empty Email Body

**Cause:** Using wrong format for data type

| If sending... | Data should be in... |
|---------------|---------------------|
| Water | Attachments (filename = ounces) |
| Steps | Email body (YYYY-MM-DD:count) |

**Fix:**
- Water: Make sure you're attaching files, not putting data in body
- Steps: Make sure data is in body, not attachments

### Problem: Missing Attachments

**Common causes:**
1. Not using "Set Name" action before adding to variable
2. Filename doesn't end in `.txt`
3. Variable name mismatch

**Fix:**
- Ensure "Set Name" sets name to `Rounded Number.txt`
- Check variable is `Files` in the email action

### Problem: Wrong Data Values

**Cause:** "Fill Missing" is ON, creating fake zero entries

**Fix:**
- In "Find Health Samples", set **Fill Missing: OFF**

### Problem: Steps Show Yesterday's Count

**Cause:** Timezone issues - email sent before day ends

**Fix:**
- Schedule automation for 9:00 PM or later
- Ensure "In the last 14 days" captures today

### Problem: Email Not Sending

**Check:**
1. Is "Ask Before Running" OFF?
2. Is email address correct? `[REDACTED]`
3. Is Mail app configured on iPhone?
4. Do you have internet connection?

### Problem: Data Not Processing on Server

**Check server expectations:**

**Water processor expects:**
- From: `gclapp@mac.com`
- Subject contains: `Water Update`
- Attachments: `.txt` files
- Filename = ounces (e.g., `64.txt`)

**Steps processor expects:**
- From: `gclapp@mac.com`
- Subject contains: `step` (case insensitive)
- Body format: `YYYY-MM-DD:STEP_COUNT`

---

## Part 5: Verification on Server Side

After sending test emails, verify they were processed:

```bash
# Check water data
python3 scripts/process_water_email.py

# Check steps data
python3 scripts/process_steps_email.py

# View reports
python3 scripts/process_water_email.py report
python3 scripts/process_steps_email.py report
```

**Data files:**
- Water: `data/water-intake-history.json`
- Steps: `data/steps-history.json`

---

## Quick Reference: Complete Shortcut Summary

### Water Shortcut Actions (in order):
1. Find Health Samples (Dietary Water, last 14 days, Group By Day, Oldest First)
2. Repeat with Each
   - Get Numbers from Input (Quantity)
   - Round Number (0 decimals)
   - Text (any content)
   - Set Name (`Rounded Number.txt`)
   - Add to Variable (Files)
3. Send Email (To: [REDACTED], Subject: Water Update, Attachments: Files)

### Steps Shortcut Actions (in order):
1. Find Health Samples (Steps, last 14 days, Group By Day, Oldest First)
2. Repeat with Each
   - Format Date (Start Date, yyyy-MM-dd)
   - Get Numbers from Input (Quantity)
   - Text (`{{Formatted Date}}:{{StepCount}}`)
   - Add to Variable (AllLines, New Lines)
3. Send Email (To: [REDACTED], Subject: Steps {{Current Date}}, Body: AllLines)

---

## FAQ

**Q: Can I combine water and steps into one email?**  
A: No. The processors look for different subjects and handle data differently. Keep them separate.

**Q: Why 14 days instead of just today?**  
A: Apple Health data updates slowly. Sending 14 days ensures we catch any late-syncing data and build a history.

**Q: What if I miss a day?**  
A: The automation runs daily, so you'll get the next batch. Historical data fills in gaps.

**Q: Can I change the send time?**  
A: Yes, but keep it after 9 PM to ensure the day's data is complete.

**Q: Why does water use attachments but steps use body?**  
A: Historical design decision. Water was built first using file-based approach. Steps were redesigned to use simpler text format.

---

## Support

If shortcuts still fail after following this guide:

1. Screenshot your shortcut actions
2. Forward a test email to yourself to see the raw format
3. Check the server logs: `logs/water-processor.log` and `logs/steps-processor.log`
4. Contact Cicero with details
