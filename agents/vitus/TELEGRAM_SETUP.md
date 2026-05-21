# Vitus Telegram Bot Setup Guide

This guide explains how to set up Vitus as a dedicated Telegram bot for health coaching.

## Overview

**Architecture:**
```
You (Telegram) → Telegram Bot API → OpenClaw Gateway → Vitus Subagent
```

Vitus will have his own Telegram bot username (e.g., `@VitusHealthBot`) that you can message directly.

---

## Step 1: Create a Telegram Bot

1. **Open Telegram** and search for **@BotFather**
2. **Start a chat** with BotFather
3. **Send:** `/newbot`
4. **Choose a name:** `Vitus` (display name)
5. **Choose a username:** `vitus_health_bot` (must end in 'bot', unique)
6. **Save the token** BotFather gives you — it looks like:
   ```
   123456789:ABCdefGHIjklMNOpqrsTUVwxyz
   ```

---

## Step 2: Configure OpenClaw Gateway

The OpenClaw gateway needs to be configured to route messages from your bot to the Vitus agent.

### Option A: Via OpenClaw CLI (if supported)

```bash
# Configure Telegram bot for Vitus agent
openclaw gateway config set telegram.vitus.bot_token "YOUR_BOT_TOKEN"
openclaw gateway config set telegram.vitus.agent_id "vitus"
openclaw gateway config set telegram.vitus.enabled "true"
```

### Option B: Via Config File

Edit the OpenClaw gateway configuration (location varies by install):

```yaml
# ~/.openclaw/gateway/config.yaml or similar
telegram:
  bots:
    vitus:
      bot_token: "YOUR_BOT_TOKEN"
      agent_id: "vitus"
      enabled: true
      webhook_url: "https://your-gateway-url/telegram/vitus"
      allowed_users:
        - "YOUR_TELEGRAM_USER_ID"  # Restrict to your account only
```

### Option C: Environment Variables

```bash
export TELEGRAM_VITUS_BOT_TOKEN="YOUR_BOT_TOKEN"
export TELEGRAM_VITUS_AGENT_ID="vitus"
export TELEGRAM_VITUS_ENABLED="true"
```

---

## Step 3: Set Up Webhook (Production)

For production use, you need a webhook URL that Telegram can send updates to:

### If you have a public domain:

```bash
# Set webhook via Telegram API
curl -X POST "https://api.telegram.org/botYOUR_BOT_TOKEN/setWebhook" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://your-domain.com/webhook/telegram/vitus",
    "allowed_updates": ["message", "callback_query"]
  }'
```

### For local testing (using ngrok):

```bash
# 1. Install ngrok
# 2. Start ngrok
ngrok http 8080

# 3. Copy the https URL (e.g., https://abc123.ngrok.io)
# 4. Set webhook
curl -X POST "https://api.telegram.org/botYOUR_BOT_TOKEN/setWebhook" \
  -d "url=https://abc123.ngrok.io/webhook/telegram/vitus"
```

---

## Step 4: Test the Bot

1. **Search for your bot** in Telegram (e.g., `@vitus_health_bot`)
2. **Start a chat** and send `/start`
3. **You should receive:** A welcome message from Vitus

---

## Step 5: Register Vitus as an Agent

You need to register Vitus as a configured agent in OpenClaw:

```bash
# Check if agent registration is supported
openclaw agents list

# If supported, register Vitus
openclaw agents add vitus \
  --name "Vitus Health Coach" \
  --soul-file /home/ubuntu/.openclaw/agents/vitus/SOUL.md \
  --model moonshot/kimi-k2.5
```

Or create an agent configuration file:

```json
// ~/.openclaw/agents/vitus/agent.json
{
  "id": "vitus",
  "name": "Vitus Health Coach",
  "description": "World-class health and performance coach",
  "soul_file": "SOUL.md",
  "model": "moonshot/kimi-k2.5",
  "capabilities": ["health_coaching", "whoop_analysis", "weight_loss"],
  "channels": ["telegram"],
  "auto_spawn": false
}
```

---

## How It Works

### Message Flow:

```
1. You send message to @vitus_health_bot on Telegram
2. Telegram forwards message to OpenClaw webhook
3. OpenClaw routes to Vitus agent based on bot_token → agent_id mapping
4. Vitus processes message and generates response
5. Response sent back via Telegram Bot API
6. You see Vitus's reply in Telegram
```

### Example Interactions:

**You:** "How's my recovery today?"

**Vitus:** 🫀 "Your recovery is at 42% — yellow zone. Your HRV is down 12% from baseline, which tells me your body is working through something. 

**Mission today:** Active recovery. 20-minute walk, no intense exercise. In bed by 9:30 PM."

---

## Commands Vitus Supports

| Command | Description |
|---------|-------------|
| `/start` | Welcome message + capabilities |
| `/recovery` | Latest recovery summary |
| `/sleep` | Sleep analysis |
| `/weight` | Weight tracking + trend |
| `/water` | Log water intake |
| `/mission` | Today's mission |
| `/help` | List all commands |

**Natural language also works:**
- "What should I eat for lunch?"
- "I slept terribly last night"
- "Log weight: 183.5"
- "Check my HRV trend"

---

## Security Notes

1. **Keep bot token secret** — Anyone with the token can control the bot
2. **Restrict to your user ID** — Prevent others from messaging Vitus
3. **Use HTTPS webhooks** — Telegram requires SSL/TLS
4. **Store token securely** — Use environment variables or secure config

---

## Troubleshooting

### Bot not responding?
- Check webhook is set: `curl https://api.telegram.org/botTOKEN/getWebhookInfo`
- Verify OpenClaw gateway is running
- Check agent is registered: `openclaw agents list`

### Messages not routing to Vitus?
- Verify `agent_id` in config matches registered agent
- Check gateway logs for routing errors
- Ensure Vitus SOUL.md is readable

### Getting other people's messages?
- Add `allowed_users` restriction in config
- Get your Telegram user ID via @userinfobot

---

## Next Steps

1. **Create the bot** with BotFather
2. **Save the token** securely
3. **Configure OpenClaw** with the token
4. **Test messaging** Vitus
5. **Set up automated briefings** via cron + Telegram API

---

**Questions?** Ask Cicero for help with any step.
