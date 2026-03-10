# Telegram Health Data Automation

Send your Apple Health data (weight, steps) via Telegram — more reliable than email.

## How It Works

```
iPhone Shortcuts → Telegram Message → Cicero → Dashboard
```

## iPhone Shortcuts Setup

### Step 1: Create the Shortcut

1. Open **Shortcuts** app
2. Tap **+** to create new shortcut
3. Add these actions:

**Action 1: Get Health Sample - Weight**
```
Search: "Get Health Sample"
Select: "Get Health Sample"
Configure:
  - Get: Body Mass (Weight)
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

**Action 3: Text (format the message)**
```
Search: "Text"
Enter:
WEIGHT: [Weight variable]
STEPS: [Steps variable]
DATE: [Current Date]
```

**Action 4: Send Message via Telegram**
```
Search: "Send Message"
Select: "Send Message via Telegram"
Configure:
  - To: @geoffclapp (or your chat with Cicero)
  - Message: [Text variable from Step 3]
```

### Step 2: Set Up Automation

1. In Shortcuts, tap **"Automation"** tab
2. Tap **+** → **"Create Personal Automation"**
3. Choose **"Time of Day"**
4. Set: **9:00 PM** (or whenever you prefer)
5. Tap **Next**
6. Add action: **"Run Shortcut"**
7. Select: **"Send Health Data"**
8. Tap **Next**
9. **Turn OFF "Ask Before Running"**
10. Tap **Done**

## Message Format

Your shortcut should send messages in this format:

```
WEIGHT: 238.5
STEPS: 8432
DATE: 2026-03-08
```

Or simpler (just weight):
```
WEIGHT: 238.5
```

Or just steps:
```
STEPS: 8432
```

## What Happens Next

When I receive your message:
1. ✅ Parse weight and steps
2. 💾 Store in health database
3. 📊 Update your dashboard
4. 🔔 Confirm receipt

## Troubleshooting

### "Telegram not installed"
- Make sure Telegram app is installed and you're logged in
- You must have an active chat with me (@CiceroBot or this conversation)

### "Message not sending"
- Check that the chat ID is correct
- Verify Telegram has permission to run in background
- Try sending a test message manually first

### "Shortcuts automation not running"
- Ensure "Ask Before Running" is OFF
- Check that automation is enabled (not disabled)
- Try a different time if 9 PM conflicts with Focus mode

### Data not appearing
- I only respond to properly formatted messages
- Check that WEIGHT/STEPS are capitalized
- Make sure there's a space after the colon

## Alternative: Manual Send

Don't want automation? Just send me a message anytime:

```
WEIGHT: 238.5
STEPS: 8432
```

I'll record it and update your dashboard.

## Privacy Note

Your health data stays in our private Telegram chat and is stored securely. I don't share this data with anyone.

---

**Questions?** Just ask! 🏛️
