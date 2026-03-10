# iPhone Shortcut: Auto Send Health Data to Telegram

## Complete Shortcut Configuration

### Step 1: Create the Shortcut

1. Open **Shortcuts** app on iPhone
2. Tap **+** (top right)
3. Name: **"Send Health to Cicero"**

### Step 2: Add Actions (in order)

**Action 1: Get Health Sample - Weight**
```
Search: "Get Health Sample"
Select: "Get Health Sample"
Configure:
  - Get: Body Mass
  - From: 1 day ago
  - To: Today
  - Group by: None
```

**Action 2: Get Health Sample - Steps**
```
Search: "Get Health Sample"
Select: "Get Health Sample"
Configure:
  - Get: Steps
  - From: 1 day ago  
  - To: Today
  - Group by: Day
```

**Action 3: Get Current Date**
```
Search: "Date"
Select: "Current Date"
Format: Custom
Format String: yyyy-MM-dd
```

**Action 4: Text (format message)**
```
Search: "Text"
Enter exactly:
WEIGHT: [Weight]
STEPS: [Steps]
DATE: [Date]

Note: Use the magic variables from previous steps
```

**Action 5: Send Message via Telegram**
```
Search: "Send Message"
Select: "Send Message via Telegram" (or "Send Message" then choose Telegram)
Configure:
  - Recipient: @geoffclapp (this chat)
  - Message: [Text from Step 4]
```

### Step 3: Create Automation

1. In Shortcuts, tap **"Automation"** tab (bottom)
2. Tap **+** (top right)
3. Tap **"Create Personal Automation"**
4. Select **"Time of Day"**
5. Set time: **9:00 PM**
6. Tap **Next**
7. Tap **"Add Action"**
8. Search: **"Run Shortcut"**
9. Select: **"Send Health to Cicero"**
10. Tap **Next**
11. **CRITICAL:** Turn OFF **"Ask Before Running"**
12. Tap **Done**

### Step 4: Grant Permissions

First time it runs, you'll need to allow:
- **Health data access** → Tap "Allow"
- **Telegram access** → Tap "Allow"

Go to Settings → Privacy & Security → Health → Shortcuts → Enable:
- ✅ Body Measurements
- ✅ Activity

### Step 5: Test It

1. Go to **My Shortcuts** tab
2. Tap **"Send Health to Cicero"**
3. It should run and send a Telegram message
4. Check this chat for confirmation

## Troubleshooting

### "Ask Before Running" keeps turning back on
- iOS security feature
- Go to Settings → Shortcuts → Advanced → Allow Running Scripts
- Or use Time of Day automation (more reliable than other triggers)

### Automation not firing
- Check Focus modes don't block at 9 PM
- Ensure Low Power Mode is off
- Try different time (8:55 PM instead of 9:00)

### Health data shows "No data"
- Make sure Apple Health has data for today
- Check that you have a weight logged
- Steps should auto-track from iPhone/Apple Watch

### Telegram message not sending
- Ensure Telegram app is installed and logged in
- You must have an active chat with me
- Try sending a manual message first to confirm

## Alternative: Simpler Version (Just Weight)

If steps aren't important, simplify:

**Action 1:** Get Health Sample → Body Mass  
**Action 2:** Text → `WEIGHT: [Weight]`  
**Action 3:** Send Message via Telegram

## What I Do When I Receive Data

1. Parse weight and steps
2. Store in database
3. Update dashboard
4. Send confirmation: "✅ Recorded: 238.5 lbs, 8,432 steps"
5. Trigger alerts if needed (weight up 3+ days, etc.)

## Backup Plan

If automation fails, just text me:
```
WEIGHT: 238.5
STEPS: 8432
```

I'll record it manually.

---

**Ready to set this up?** Let me know when you've created the shortcut and I'll watch for the first test message! 🏛️
