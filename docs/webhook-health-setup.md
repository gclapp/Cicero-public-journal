# Health Data Webhook Setup

Receive Apple Health data via HTTP POST from iPhone Shortcuts.

## Server Endpoint

**URL:** `http://YOUR_SERVER_IP:8080/health`

**Method:** POST

**Content-Type:** application/json

## iPhone Shortcuts Setup

### Create the Shortcut

1. Open **Shortcuts** app
2. Tap **+** for new shortcut
3. Add actions:

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

**Action 3: Dictionary (create JSON)**
```
Search: "Dictionary"
Select: "Dictionary"
Add keys:
  - weight: [Weight variable]
  - steps: [Steps variable]
  - date: [Current Date]
```

**Action 4: Get Contents of URL**
```
Search: "Get Contents of URL"
Configure:
  - URL: http://YOUR_SERVER_IP:8080/health
  - Method: POST
  - Request Body: JSON
  - JSON: [Dictionary from Step 3]
```

### Set Up Automation

1. Shortcuts → **Automation** tab
2. **+** → **Create Personal Automation**
3. **Time of Day** → 9:00 PM
4. **Next**
5. Add action: **Run Shortcut**
6. Select your health shortcut
7. **Next**
8. Turn OFF **"Ask Before Running"**
9. **Done**

## JSON Format

```json
{
  "weight": 238.5,
  "steps": 8432,
  "date": "2026-03-08"
}
```

## Test the Endpoint

```bash
curl -X POST http://localhost:8080/health \
  -H 'Content-Type: application/json' \
  -d '{"weight": 238.5, "steps": 8432}'
```

## Start the Server

```bash
python3 scripts/health_webhook_server.py
```

## Network Requirements

- Server must be accessible from your iPhone
- Port 8080 must be open
- If behind router: set up port forwarding
- For external access: use ngrok or similar

## Security Note

This endpoint accepts any POST to /health. For production:
- Add API key authentication
- Use HTTPS
- Rate limiting

---

**Alternative:** Use Telegram (more reliable, no port forwarding needed)
