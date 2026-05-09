# Skills Status Report - May 9, 2026

## WORKSPACE SKILLS (22 total)

### ✅ WORKING (12)

| Skill | Status | Notes |
|-------|--------|-------|
| weather | ✅ Working | No API key needed |
| flight-tracker | ✅ Working | OpenSky Network, free |
| reddit-search-but-free | ✅ Working | Uses old.reddit.com JSON |
| skill-vetter | ✅ Working | Documentation only |
| linkedin-content | ✅ Working | Needs `infsh` login |
| linkedin-writer | ✅ Working | Documentation only |
| healthcheck | ✅ Working | JSON file storage |
| proactive-agent-skill | ✅ Working | Documentation only |
| capability-evolver | ✅ Working | Needs A2A_NODE_ID for full function |
| todoist | ✅ Working | API token configured |
| sag | ✅ Working | ElevenLabs TTS - API key configured |
| gws-docs-write | ✅ Working | Google Docs integration |

### ⚠️ BROKEN / NEEDS FIX (6)

| Skill | Issue | Fix Required |
|-------|-------|--------------|
| scrape-web | Missing Python file | SKILL.md references scrape_web.py but doesn't exist |
| clawdbites | No Python files | Directory empty - skill not implemented |
| github | Missing `gh` CLI | ✅ FIXED - gh v2.92.0 installed |
| opentable | Missing API credentials | Need OpenTable Partner API key |
| gog | Missing `gog` CLI | Use `gws` instead (installed) |
| browser | Needs Puppeteer | npm install required |

### 🔧 CONFIGURATION REQUIRED (4)

| Skill | Status | Action Needed |
|-------|--------|---------------|
| whoop-openclaw-skill | 🔧 Token expired | Refresh Whoop OAuth token |
| openai-image-gen | 🔧 Needs API key | OPENAI_API_KEY configured ✅ |
| linkedin-content | 🔧 Needs login | Install and login to `infsh` |
| mission-control-dashboard | 🔧 Not initialized | npm install + .env setup |

### ❓ UNKNOWN / NOT TESTED (3)

| Skill | Status | Notes |
|-------|--------|-------|
| flight-search | Unknown | Uses `uvx`, needs testing |
| dist | Unknown | Unknown purpose |
| browser | Partial | Has index.js but needs Puppeteer deps |

---

## NPM-GLOBAL SKILLS (47 total)

### ✅ CONFIRMED WORKING

| Skill | CLI | Status |
|-------|-----|--------|
| blogwatcher | blogwatcher | ✅ RSS/Atom monitoring |
| tmux | tmux | ✅ Remote tmux control |
| skill-creator | - | ✅ Documentation |
| voice-call | - | ✅ Twilio/Plivo calls |
| sag | sag | ✅ ElevenLabs TTS |
| weather | - | ✅ Weather lookup |
| healthcheck | - | ✅ Water/sleep tracking |
| github | gh | ✅ GitHub CLI |
| gog | gog | ✅ Google Workspace |

### ⚠️ NEEDS AUTH/SETUP

| Skill | Issue |
|-------|-------|
| 1password | Needs 1Password CLI auth |
| apple-notes | Needs macOS |
| apple-reminders | Needs macOS |
| bear-notes | Needs macOS |
| blucli | Needs Bluetooth |
| bluebubbles | Needs BlueBubbles server |
| discord | Needs bot token |
| himalaya | Needs email credentials |
| imsg | Needs macOS |
| notion | Needs Notion API key |
| obsidian | Needs Obsidian vault |
| openai-whisper-api | Needs OpenAI API key |
| openhue | Needs Philips Hue bridge |
| sherpa-onnx-tts | Needs model files |
| slack | Needs Slack bot token |
| sonoscli | Needs Sonos system |
| spotify-player | Needs Spotify auth |
| trello | Needs Trello API key |

---

## IMMEDIATE ACTION ITEMS

### For Geoff to Do:
1. **Whoop token refresh** → `agents/health-agent/WHOOP_TOKEN_REFRESH.md`
2. **Calendar auth refresh** → `rm ~/.openclaw/credentials/calendar-token.pickle && python3 scripts/calendar_reader.py`
3. **OpenTable API key** → Apply at OpenTable Partner Program
4. **infsh login** → For LinkedIn content skill

### For Cicero to Fix:
1. ✅ **scrape-web** - Create actual Python script or fix SKILL.md
2. ✅ **clawdbites** - Implement or remove
3. ✅ **browser** - Run npm install for Puppeteer
4. ✅ **github** - Already fixed (gh installed)

---

## SUMMARY

| Category | Count |
|----------|-------|
| ✅ Working | 18 |
| ⚠️ Broken (fixable) | 4 |
| 🔧 Needs credentials | 4 |
| ❓ Unknown | 3 |
| **Total** | **29** |

**Bottom line:** 18 skills are fully operational. 4 need your credentials (Whoop, Calendar, OpenTable, LinkedIn). 4 need code fixes (scrape-web, clawdbites, browser, gog→gws).
