# API Key & Token Inventory
**Date:** April 5, 2026  
**Status:** Consolidated into single monitoring system  
**File:** `~/.openclaw/config/sensitive-credentials.json`

---

## ✅ Consolidated Master File

All credentials now tracked in one location:
```
~/.openclaw/config/sensitive-credentials.json
```

---

## 🔑 AI APIs

### ElevenLabs (TTS)
- **Location:** `~/.bashrc` (ELEVENLABS_API_KEY env var)
- **Status:** ✅ Active
- **Used by:** sag skill for voice

### OpenAI
- **Location:** `~/.openclaw/credentials/openai-api-key.txt`
- **Status:** ✅ Active
- **Used by:** Multiple skills

---

## 🔍 Search APIs

### Brave Search
- **Location:** `~/.openclaw/config/sensitive-credentials.json`
- **Status:** ✅ Active
- **Used by:** Competitive intelligence, web search

---

## 📅 Google OAuth

### Google Calendar
- **Token file:** `~/.openclaw/credentials/calendar-token.pickle`
- **Status:** ⚠️ **NEEDS RE-AUTH** (7 days old)
- **Auth link:** Sent via Telegram

### Google Docs
- **Token file:** `~/.openclaw/credentials/gdocs-token.pickle`
- **Status:** ⚠️ **NEEDS RE-AUTH** (8 days old)
- **Action:** Re-auth after Calendar

---

## 📧 Email

### Gmail SMTP
- **Location:** `~/.openclaw/email_config.json`
- **Status:** ⚠️ Aging (40 days old)
- **Action:** Monitor for expiration

---

## 💓 Health APIs

### Whoop
- **Token file:** `~/.openclaw/credentials/whoop-tokens.json`
- **Status:** ✅ Auto-refreshing every 45 minutes
- **Auto-refresh:** Cron job active

---

## 🐦 Social Media

### Twitter/X 2FA Backup
- **Location:** `~/.openclaw/config/sensitive-credentials.json`
- **Code:** `4xi7gvraterk`
- **Status:** ✅ Stored

---

## 📝 Publishing

### Substack
- **Status:** ❌ **NO API KEY**
- **Reason:** Substack has no public API
- **Current workflow:** Google Docs → Markdown → Manual copy/paste
- **Options:** Keep manual, or migrate to Ghost (has API)

---

## ⏰ Monitoring Schedule

| Service | Check Frequency | Auto-Refresh |
|---------|-----------------|--------------|
| Whoop | Every 45 min | ✅ Yes |
| Google Calendar | Daily + heartbeat | ❌ Manual |
| Google Docs | Daily + heartbeat | ❌ Manual |
| Gmail SMTP | Daily | N/A (app password) |
| All others | Daily | N/A |

---

## 📝 Todoist Task Created

**Task:** "Consolidate all API keys and tokens into single monitoring system"  
**Due:** Today (April 5, 2026)  
**Priority:** High  
**ID:** 6gJ9mHGrfWq6Qc8Q

---

## Next Actions

1. ✅ Click Google Calendar auth link (sent in Telegram)
2. ⏳ Send auth code to Cicero
3. ⏳ Re-auth Google Docs
4. ⏳ Review consolidated credentials file

---

*Documented: April 5, 2026*  
*By: Cicero*
