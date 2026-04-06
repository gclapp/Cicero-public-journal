# API Keys & Credentials Inventory

**Master File:** `~/.openclaw/config/sensitive-credentials.json`
**Permissions:** 600 (owner read/write only)
**Last Updated:** 2026-04-06

---

## Consolidated API Keys (Actual Values Stored)

| Service | Key Type | Status | Source |
|---------|----------|--------|--------|
| **OpenAI** | API Key | ✅ Active | Moved from `~/.openclaw/credentials/openai-api-key.txt` |
| **ElevenLabs** | API Key | ✅ Active | Moved from `~/.bashrc` |
| **Brave Search** | API Key | ✅ Active | Moved from `~/.bashrc` |
| **Whoop** | Client ID + Secret | ✅ Active | Referenced from `whoop-config.json` |

---

## Token References (Paths Only, Not Actual Tokens)

| Service | Token Location | Status | Auto-Refresh |
|---------|---------------|--------|--------------|
| **Google Calendar** | `~/.openclaw/credentials/calendar-token.pickle` | ✅ Active | ❌ Manual (OAuth) |
| **Google Docs** | `~/.openclaw/credentials/gdocs-token.pickle` | ✅ Active | ❌ Manual (OAuth) |
| **Gmail SMTP** | `~/.openclaw/email_config.json` | ✅ Active | ✅ Never expires |
| **Whoop Access** | `~/.whoop_token` | ✅ Active | ✅ Every 30 min |
| **Whoop Refresh** | `~/.whoop_refresh_token` | ✅ Active | ✅ Every 30 min |

---

## Other Credentials

| Service | Location | Status |
|---------|----------|--------|
| **Telegram** | `~/.openclaw/credentials/telegram-pairing.json` | ✅ Active |
| **WhatsApp** | `~/.openclaw/credentials/whatsapp/` | ✅ Active |

---

## Security Notes

- **Master file permissions:** 600 (owner only)
- **Token files:** 600 (owner only)
- **No secrets in Git:** All credential files are in `.gitignore`
- **Backup:** Encrypted backup stored separately

---

## Manual Management Required

These require browser-based OAuth and cannot be fully automated:

1. **Google Calendar** — Re-auth every ~7 days
2. **Google Docs** — Re-auth every ~7 days

**Process:** I generate auth URL → You click and approve → Send me code → I update token

---

## Auto-Refreshing

These are fully automated:

1. **Whoop** — Refreshes every 30 minutes via cron
2. **Gmail SMTP** — App password, essentially never expires

---

## Monitoring

**Daily token health check** shows status of all credentials in morning check-in.

**Alert thresholds:**
- Google tokens: Alert at 5 days, critical at 7 days
- Gmail SMTP: Alert at 25 days, critical at 60 days
- Whoop: Refreshes automatically at 45 minutes

---

## Files Consolidated

✅ `~/.bashrc` — ElevenLabs and Brave keys moved to master file
✅ `~/.openclaw/credentials/openai-api-key.txt` — Moved to master file
✅ `~/.openclaw/workspace/config/whoop-config.json` — Referenced in master file
✅ All token paths documented in master file

---

*Last verified: 2026-04-06*
*Managed by: Cicero*