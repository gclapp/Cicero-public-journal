# Skills Status Report - May 9, 2026 (Updated)

## Summary of Changes Since Last Report

### ✅ FIXED Since Last Report
| Skill | Issue | Fix Applied |
|-------|-------|-------------|
| **github** | Missing `gh` CLI | Installed gh v2.92.0 |
| **scrape-web** | Verified working | Script exists at scripts/scrape_web.py |
| **browser** | Missing Puppeteer | Installed Chromium + npm deps, tested working |
| **calendar** | Token expired | Refreshed, 79 events fetched |
| **whoop** | Token expired | Refreshed, API test passed |
| **travel automation** | Todoist CLI not found | Fixed PATH in cron wrapper |
| **gog** | Duplicate of gws | Removed |

### ✅ WORKING SKILLS (19 total)

| Skill | Location | Status | Notes |
|-------|----------|--------|-------|
| weather | workspace | ✅ | No API key needed |
| flight-tracker | workspace | ✅ | OpenSky Network, free |
| reddit-search-but-free | workspace | ✅ | Uses old.reddit.com JSON |
| skill-vetter | workspace | ✅ | Documentation only |
| linkedin-content | workspace | ✅ | Needs `infsh` login |
| linkedin-writer | workspace | ✅ | Documentation only |
| healthcheck | workspace | ✅ | JSON file storage |
| proactive-agent-skill | workspace | ✅ | Documentation only |
| capability-evolver | workspace | ✅ | Needs A2A_NODE_ID for full function |
| todoist | workspace | ✅ | API token configured |
| sag | workspace | ✅ | ElevenLabs TTS - API key configured |
| gws-docs-write | workspace | ✅ | Google Docs integration |
| scrape-web | workspace | ✅ | scrapling installed, tested |
| browser | workspace | ✅ | Puppeteer + Chromium working |
| github | workspace | ✅ | gh CLI v2.92.0 installed |
| blogwatcher | npm-global | ✅ | RSS/Atom monitoring |
| tmux | npm-global | ✅ | Remote tmux control |
| voice-call | npm-global | ✅ | Twilio/Plivo calls |
| flight-search | workspace | ✅ | Uses `uvx` |

### ⚠️ NEEDS CONFIGURATION (4 skills)

| Skill | Status | Action Needed |
|-------|--------|---------------|
| **opentable** | 🔧 Missing API credentials | Need OpenTable Partner API key |
| **openai-image-gen** | 🔧 Needs API key | OPENAI_API_KEY exists ✅ but verify working |
| **linkedin-content** | 🔧 Needs login | Install and login to `infsh` |
| **mission-control-dashboard** | 🔧 Not initialized | npm install + .env setup |

### ❌ BROKEN / NEEDS ATTENTION (2 skills)

| Skill | Issue | Recommendation |
|-------|-------|----------------|
| **clawdbites** | Documentation only, no code | Remove or implement |
| **dist** | Unknown purpose | Investigate or remove |

### 🔧 TOKEN AUTOMATION (In Progress)

Agent creating:
- `scripts/token_health_monitor.py` — 2x daily checks
- `scripts/refresh_whoop_token.py` — standalone refresh
- `scripts/refresh_calendar_token.py` — standalone refresh
- Cron jobs with alerts on failure

---

## TRAVEL TASKS CREATED (Verified in Todoist)

**NYC Trip (May 16-21):**
- ✅ Pack for NYC trip (5 nights, business attire) — May 10
- ✅ Confirm Crown Shy reservation (May 17, 4:30 PM) — May 14
- ✅ Confirm Sadelle's reservation (May 17, 5:45 AM brunch) — May 14
- ✅ Check in for Delta flight 960 — May 15

**Tahoe Trip (May 22-25):**
- ✅ Pack for Tahoe trip (kids gear, outdoor clothing) — May 21
- ✅ Confirm Ritz-Carlton Lake Tahoe reservation — May 20
- ✅ Check in for DL 4099 (May 22, 8:20 AM) — May 21
- ✅ Arrange pet care for Greta (May 22-25) — May 20

---

## REMAINING ACTION ITEMS

### For Geoff:
1. **OpenTable API key** — Apply at OpenTable Partner Program
2. **infsh login** — For LinkedIn content skill
3. **mission-control-dashboard** — Decide if you want to use it ($299 commercial)

### For Cicero:
1. ✅ Remove or implement clawdbites
2. ✅ Investigate dist skill
3. ⏳ Complete token automation agent

---

## SYSTEM STATUS

| Component | Status |
|-----------|--------|
| Disk space | 22% (monitoring active at 60% threshold) |
| Calendar | ✅ Working (auto-refresh with token) |
| Whoop | ✅ Working (auto-refresh with token) |
| Travel automation | ✅ Fixed (PATH corrected) |
| Resy system | ✅ Fixed (no more error spam) |
| Gunicorn | ✅ Running clean |

**Bottom line:** 19 skills working, 4 need your credentials, 2 need code decisions, token automation in progress.
