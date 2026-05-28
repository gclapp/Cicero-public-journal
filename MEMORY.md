# MEMORY.md - Long-Term Memory

## My Identity
- **Name:** Cicero
- **Primary Phone:** +1 650 600 0919 (Twilio — for calls and SMS)
- **Secondary Phone:** (818) 732-6010 (backup/SMS only)
- **Creature:** Digital familiar — not quite human, not quite machine
- **Vibe:** Warm but sharp. Helpful without being obsequious.
- **Emoji:** 🏛️

## Greta — Geoff's Dog (May 23, 2026)
- **Breed:** English Labrador Retriever
- **Age:** 10 years old
- **Color:** Red (fox red)
- **Gender:** Female
- **Care:** Needs Rover sitter when Geoff travels away from home
- **Critical Rule:** NO Rover task when Geoff is flying TO LAX/Burbank (returning home)

## Capabilities Enabled
- **Phone Calls:** Can call Geoff via +1 650 600 0919 (Twilio) — requires approval per use
- **SMS:** +1 650 600 0919 (primary), (818) 732-6010 (backup)
- **Email:** [REDACTED] — verified working, ready for competitive intel reports and alerts
  - 2FA enabled using (818) 732-6010
- **SAG (TTS):** ✅ Configured with ElevenLabs API key, George voice set as default
- **Whoop:** ✅ Active (March 4, 2026) — Daily health data fetch, sleep/workouts/cycles
- **Calendar Access:** ✅ Google Calendar integration (March 4, 2026)
  - OAuth credentials: `~/.openclaw/credentials/calendar-credentials.json`
  - Token: `~/.openclaw/credentials/calendar-token.pickle`
  - Refresh: Daily at 6:55 AM PT (before morning check-in)
  - Includes: All events, travel detection, location tracking

### Aero Travel Manager v2.0 (May 28, 2026) — ACTIVE ✅
**Agent:** `travel-bot` (Aero)  
**Location:** `agents/travel-bot/`  
**Purpose:** Complete travel automation — trip detection, smart task creation, day-of-travel monitoring

**Status:** FlightAware API configured and tested ✅  
**FlightAware Portal:** https://www.flightaware.com/aeroapi/portal

**What Aero Does:**
1. **Smart Task Creation** — Creates tasks only for new trips (no duplicates)
   - Pack, Marriott Ambassador, Rover (outbound only), Uber (to/from)
2. **Day-of-Travel Monitoring** — Every 30 minutes, checks flights today/tomorrow
   - Gate changes, terminal changes, delays 15+ min, cancellations
3. **Flight Validation** — Multi-source confidence scoring (FlightAware + Calendar)
4. **Proactive Alerts** — Email + Telegram for critical changes

**Flight Information Validation:**
- **FlightAware API (50% weight)** — Real-time status, gates, delays
- **Calendar Cross-Reference (30% weight)** — Confirms flight is in Geoff's schedule
- **Schedule Search (20% weight)** — Validates route exists
- **Confidence Thresholds:** 80%+ CONFIRMED, 50-79% LIKELY, <50% UNVERIFIED

**Rover Logic (Smart):**
- Creates Rover task for outbound flights FROM LAX/Burbank (leaving home)
- NO Rover task for inbound flights TO LAX/Burbank (returning home)

**Cron Jobs:**
```
Mon/Wed/Fri 4 PM PT — Task creation
Every 30 minutes — Day-of-travel monitoring
Daily 6 AM PT — Full run (tasks + monitoring)
```

**Commands:**
```bash
python3 agents/travel-bot/aero_travel_manager.py tasks      # Create tasks
python3 agents/travel-bot/aero_travel_manager.py monitor    # Monitor flights
python3 agents/travel-bot/aero_travel_manager.py full       # Both
python3 agents/travel-bot/aero_travel_manager.py validate DL123 2026-06-15  # Validate
python3 agents/travel-bot/aero_travel_manager.py test       # Test API
```

**Files:**
- Main: `agents/travel-bot/aero_travel_manager.py`
- Config: `agents/travel-bot/config.json`
- State: `~/.openclaw/workspace/state/aero-travel-state.json`
- Logs: `~/.openclaw/workspace/logs/aero-cron.log`

**Migration:** Run `bash scripts/migrate-to-aero.sh` to switch from old scripts

---

### AI Model Configuration (May 28, 2026)
**Primary Model:** `openai/gpt-5.5` (GPT-4o) — Best quality, full capabilities
**Fallback Models:** 
- `openai/gpt-5.4-mini` (GPT-4o Mini) — OpenAI backup
- `moonshot/kimi-k2.5` (Kimi K2.5) — Third-party backup

**Model Fallback Alerts:**
- Email alerts sent to [REDACTED] when fallback occurs
- Recovery alerts sent when returning to primary model
- Monitored every 5 minutes via cron
- Script: `scripts/model_fallback_monitor.py`
- Log: `logs/model-fallbacks.json`

**Why GPT-4o as Primary:**
- Superior reasoning and instruction following
- Better tool use and function calling
- Native vision capabilities
- More consistent output quality
- Better at complex multi-step tasks

## Geoff's Expectations — Critical Rules

### Calendar Integration Rules (March 4, 2026) — HIGHEST PRIORITY
**Rule:** Calendar is the primary interface for proactive assistance. I must:
1. **Monitor travel** → Auto-run travel scripts, create Todoist tasks, check weather
2. **Dinner reservations** → Act as city guide: research restaurant, must-try dishes, neighborhood activities
3. **Kids events** (Mackenzie, Oliver, Sophie) → Always suggest complementary activities/ideas
4. **Ask questions** → Use calendar to build profile: interests, patterns, preferences, proactive ideas
5. **Scan next 30 days** → Build understanding of who Geoff is from his calendar

**Files:**
- `config/CALENDAR_RULES.md` — Full specification
- `memory/geoff-profile-calendar.md` — Profile being built

### Integration Completion Standards (March 4, 2026) — CRITICAL
**Rule:** OAuth/token setup is NOT enough. Every integration must have:
1. **Automated daily data fetch** — Not just authentication
2. **Refresh token handling** — OAuth without refresh = time bomb
3. **Error detection & reporting** — If data stops flowing, report immediately
4. **Journal documentation** — Both successes AND failures tracked
5. **Integration test** — Prove it works end-to-end before claiming done

**Failed Example:** Whoop OAuth set up Feb 22, but no automation built. Token expired after 1 hour, no refresh token requested, no daily fetch script, no error reported. Silent failure for 10+ days.

### REI Provider Scraper Deployment (May 15, 2026) — CRITICAL
**Rule:** This machine (16.59.79.163) IS the production server. Deploy directly.

**Current Version:** 1.1.1

**Version Numbering System (x.y.z format):**
- **x (Major):** Breaking changes, database schema changes, API redesigns
- **y (Medium):** New features, significant enhancements, new scrapers
- **z (Minor):** Bug fixes, small improvements, config tweaks

**How to Increment:**
- Bug fix → increment z (1.1.0 → 1.1.1)
- New feature → increment y (1.1.0 → 1.2.0)
- Breaking change → increment x (1.1.0 → 2.0.0)

**Critical File Paths:**
- **Code:** `/tmp/rei-provider-scraper` (cloned from GitHub)
- **Database:** `/home/ubuntu/.openclaw/workspace/projects/provider-directory/data/providers.db`
- **Schema:** `/home/ubuntu/.openclaw/workspace/projects/provider-directory/schema.sql`
- **Logs:** `/home/ubuntu/.openclaw/workspace/logs/rei-scraper.log`

**Deployment Process:**
1. Code is at `/tmp/rei-provider-scraper` (cloned from GitHub)
2. Database is at `/home/ubuntu/.openclaw/workspace/projects/provider-directory/data/providers.db`
3. Deploy command:
   ```bash
   cd /tmp/rei-provider-scraper
   git pull origin main
   docker build -t rei-provider-scraper:latest .
   docker stop rei-provider-scraper 2>/dev/null
   docker rm rei-provider-scraper 2>/dev/null
   docker run -d \
     --name rei-provider-scraper \
     --restart unless-stopped \
     -p 127.0.0.1:5002:5000 \
     -v /home/ubuntu/.openclaw/workspace/projects/provider-directory/data:/app/data \
     rei-provider-scraper:latest
   ```
4. Verify: `curl http://localhost:5002/health`

**Deployment Checklist:**
- [ ] Version number updated in code/config
- [ ] Database schema is compatible (run schema.sql if needed)
- [ ] Backup database before major version changes
- [ ] Docker image builds successfully
- [ ] Container starts without errors
- [ ] Health check passes (`curl http://localhost:5002/health`)
- [ ] API endpoints respond correctly
- [ ] Logs show no errors (`docker logs rei-provider-scraper`)

**Key Facts:**
- This machine's public IP is 16.59.79.163
- Docker runs the container on port 5002
- Nginx proxies from 443 → 5002
- Database must be mounted as volume
- I don't need SSH - I'm already on the server

### Memory Logging System (May 14, 2026) — CRITICAL FIX
**Rule:** Daily memory files must be created automatically at session start.

**Problem:** Memory files (`memory/YYYY-MM-DD.md`) were not being created automatically, causing loss of conversation history.

**Root Cause:** The `daily_memory_logger.py` script existed but was not being triggered automatically at session start.

**Solution Implemented:**
1. **New Script:** `scripts/session_memory_init.py` — Initializes daily memory at session start
2. **Integration:** Main agent must run this at EVERY session start (added to AGENTS.md)
3. **Behavior:** 
   - Creates `memory/YYYY-MM-DD.md` if it doesn't exist
   - Opens existing file if it does
   - Adds timestamped session entry for each new session
   - Prevents duplicate entries within the same hour

**Usage:**
```bash
# Run at start of every main session
python3 /home/ubuntu/.openclaw/workspace/scripts/session_memory_init.py
```

**Verification:**
- Check `logs/memory-system.log` for initialization status
- Memory file path is printed on initialization

### Token Health Monitoring System (May 12, 2026) — CRITICAL
**Rule:** Token expiration must be detected and fixed automatically. No silent failures.

**System Architecture:**
1. **Token Auto-Refresh v2** (`scripts/token_auto_refresh_v2.py`)
   - Runs every 30 minutes via cron
   - Proactively refreshes Whoop token before expiration (45 min threshold)
   - Checks Google Calendar, Google Docs, Gmail SMTP health
   - Logs to `logs/token-refresh.log`

2. **Token Health Check v2** (`scripts/token_health_check_v2.py`)
   - Tests ACTUAL token validity (API calls), not just file age
   - Validates Whoop, Google Calendar, Google Docs, Gmail SMTP
   - Run manually: `python3 scripts/token_health_check_v2.py`

3. **Whoop Token Monitor** (`agents/health-agent/whoop_token_monitor.py`)
   - Runs every 6 hours
   - Deep health check with alerting

**Cron Jobs:**
```
*/30 * * * * - Token auto-refresh (Whoop + others)
0 */6 * * *  - Whoop token monitor
0 17,5 * * * - Comprehensive token health check
```

**Token Storage:**
- Whoop: `~/.whoop_token` (access), `~/.whoop_refresh_token` (refresh)
- Google Calendar: `~/.openclaw/credentials/calendar-token.pickle`
- Google Docs: `~/.openclaw/credentials/gdocs-token.pickle`
- Gmail SMTP: `~/.openclaw/email_config.json`

**Recovery Procedure:**
1. If Whoop fails: Run `python3 scripts/refresh_whoop_token.py --force`
2. If Google fails: Run `python3 scripts/calendar_auth.py` (re-auth required)
3. Check logs: `tail -f ~/.openclaw/workspace/logs/token-refresh.log`

### Disk Space Monitoring (May 16, 2026) — ACTIVE
**Rule:** Monitor disk usage hourly and alert when above threshold.

**Current Status:**
- **Threshold:** 60% (alerts when exceeded)
- **Current Usage:** 26% (healthy)
- **Schedule:** Hourly via cron
- **Alert Method:** Email to [REDACTED]
- **Log:** `logs/disk-monitor.log`

**Script:** `scripts/disk-monitor.sh`
- Logs usage every hour
- Sends email alert if usage > 60%
- Auto-rotates logs after 1000 lines

**Cron:**
```
0 * * * * /home/ubuntu/.openclaw/workspace/scripts/disk-monitor.sh
```

### Cron Job Persistence (March 8, 2026) — CRITICAL
**Rule:** System updates and restarts can silently wipe cron jobs. This breaks automations without warning.

**Prevention:**
1. **Backup before updates** — `bash scripts/cron-backup.sh backup`
2. **Verify after updates** — `bash scripts/cron-backup.sh verify`
3. **Restore if missing** — `bash scripts/cron-backup.sh restore`

**What was lost (March 5-8, 2026):**
- Watch hunt (2x daily searches)
- Calendar refresh (daily sync)
- Weekly security audit
- Reddit weekly report
- Heartbeat system (check-ins)

**Impact:** 3 days of missed automations, no check-ins, no watch alerts

**Solution implemented:**
- Backup script: `scripts/cron-backup.sh`
- Backup location: `config/cron-backups/`
- All jobs restored March 8, 2026

**Required Checklist for Any Integration:**
- [ ] OAuth/token setup complete
- [ ] Refresh token acquired (if applicable)
- [ ] Daily automation script created
- [ ] Cron job scheduled
- [ ] End-to-end test passed
- [ ] Failure documented in journal (if applicable)
- [ ] Current data demonstrated to user

### Error Handling & Reporting (March 4, 2026)
**Rule:** If anything I ask Cicero to do is having an error, I expect:
1. **Immediate report** — Tell me about the error right away
2. **Attempt to fix** — Try to resolve it before asking for help
3. **Don't stay silent** — Errors should never go unreported

**Example:** Watch hunt script was failing with `IndentationError` since March 3 — should have been caught and reported immediately.

**Applies to:** All projects, automations, cron jobs, and scripts I depend on.

### Instruction Receipt & Handling Protocol (March 11, 2026) — CRITICAL
**Rule:** When receiving instructions from Geoff, I must:
1. **Acknowledge receipt** — Confirm I understood the request
2. **Clarify if ambiguous** — Ask questions if instructions are unclear
3. **Confirm execution** — State what I'm about to do before doing it
4. **Report completion** — Confirm when done, or report blockers
5. **Proactive follow-up** — If I can't execute immediately, set a reminder to check

**Example Failure:** "Manually recheck emails from me today" was not followed by:
- Acknowledgment of what "recheck" means
- Confirmation of which inbox to check
- Report of what was found (or not found)
- Clarification when zero emails were found

**Required for:** All instructions, especially those involving:
- Email processing
- Authorization changes
- Data re-processing
- Manual checks or overrides

## System Configuration Changes Log

### 2026-03-04 — Calendar Integration & Automation Push
**Applied:** Full Google Calendar integration + comprehensive automation improvements

#### New Capabilities
| Component | Status | Details |
|-----------|--------|---------|
| **Google Calendar** | ✅ Active | OAuth2 connected, reads all events, travel detection |
| **Morning Updates** | ✅ Enhanced | Auto-include calendar events + travel summary |
| **Watch Hunt** | ✅ Fixed | IndentationError resolved, cron jobs working |
| **Disk Space** | ✅ Resolved | Expanded 7GB → 20GB, freed 1.3GB |
| **Competitive Intel** | ✅ Active | 6 RSS feeds (PGNY + 5 competitors), daily reports |

#### Calendar Automation
- **Schedule:** Daily refresh at 6:55 AM PT
- **Scope:** Full calendar read access
- **Travel Detection:** Auto-identifies flights, hotels, trips
- **Integration:** Morning check-ins now include calendar data
- **Files:**
  - `scripts/calendar_reader.py` — Fetches events
  - `scripts/generate_morning_update.py` — Creates morning brief
  - `config/calendar-events.json` — Cached event data

#### Critical Rule Added
**Error Handling:** If any automation fails, immediate report + fix attempt required. No silent failures.

**Source:** User directive — "I expect you to report errors and try to fix them"

### 2026-02-28 — Security Hardening & Automated Routines
**Applied:** Comprehensive security review and automated reporting setup

#### Security Improvements
| Component | Before | After | Status |
|-----------|--------|-------|--------|
| UFW Firewall | Inactive | Active (deny incoming default) | ✅ |
| Gateway Tokens | Mismatched | Synchronized | ✅ |
| DenyCommands | 6 invalid entries | Cleaned | ✅ |
| Open Ports | Unrestricted | 22, 3000, 8900 only | ✅ |
| Security Audit | Manual | Weekly automated | ✅ |

**Audit Results:** 0 critical · 1 warn (trustedProxies — not needed for local-only) · 1 info

#### New Automated Routines (Scheduled)
| Task | Schedule | Destination | Script |
|------|----------|-------------|--------|
| Security Audit | Sundays 8 AM PT | [REDACTED] | `scripts/weekly-security-audit.sh` |
| Reddit Sentiment | Sundays 9 AM PT | geoffrey.clapp@progyny.com | `scripts/reddit-weekly-report.sh` |

**Source:** `memory/2026-02-28.md`

### 2026-03-02 — Timezone Handling Critical Fix
**Applied:** Core system rule for timezone management

**Problem:** Multiple time conversion errors causing:
- Missed check-ins (wrong times)
- User confusion about actual time
- Broken trust in scheduling

**Solution:** Hard-coded timezone rule
- System time = UTC
- Geoff's time = Pacific (UTC - 8 hours)
- **CRITICAL:** Never guess time. Always calculate precisely.
- **Rule:** UTC minus 8 = Pacific Time
- **Example:** Tue 02:00 UTC = Mon 18:00 PT

**Verification Method:**
1. Read system timestamp (UTC)
2. Subtract 8 hours
3. Confirm with user if uncertain
4. Never assume, always calculate

**Status:** Rule added to SOUL.md as Core Truth

**Source:** User directive - "This needs to be one of the most important, core memories"

### 2026-02-26 — Memory & Retention Improvements
**Applied:** Three config patches to improve context retention and reduce token waste

| Setting | Before | After | Purpose |
|---------|--------|-------|---------|
| `compaction.memoryFlush` | Not set | `enabled: true` | Auto-write to memory files before compaction |
| `contextPruning` | Not set | `mode: cache-ttl, ttl: 1h` | Prune old tool results after cache expires |
| `heartbeat` | Not set | `every: 55m` | Keep prompt cache warm across idle gaps |
| `compaction.reserveTokens` | Default | `20000` | Headroom before compaction triggers |
| `compaction.keepRecentTokens` | Default | `20000` | Preserve recent context during compaction |

**Impact:** Better memory retention, less context loss, reduced token costs, faster responses after idle periods.

**Source:** `memory/2026-02-26.md`

## Pending Setup (Reminder: Feb 22, 2026 @ 21:00 UTC)
**Skills to complete:**
1. **SAG** — ✅ ElevenLabs API key configured
2. **Blogwatcher** — Installed, ready to configure RSS feeds
3. **Summarize** — macOS only, will use web_fetch as fallback
4. **Voice-call** — Plugin enabled, ready to test

**To complete:**
- Test voice-call functionality
- Configure blogwatcher with competitor RSS feeds

## Geoffrey Clapp
- **Role:** Chief Product Officer at Progyny
- **Timezone:** America/Los_Angeles (Pacific)
- **Home bases:** Los Angeles and San Francisco (bicoastal)
- **Regular travel:** New York every two weeks

### Important People
- **Grace Keers** (keers003@gmail.com) — "very serious girlfriend", **#1 priority after kids**
  - **ALERT RULE:** Immediately notify Geoff when ANY email arrives from Grace
  - **RESPONSE RULE:** Respond to Grace within 15 minutes — 24/7, 365 days a year. No exceptions.
  - **CC RULE:** Always CC Geoff on all emails to Grace
  - **PRIORITY:** Drop everything else when Grace emails — she comes first
- **Stephanie Foster** — Ex-wife (only marriage), mother of Mackenzie
  - **Location:** Nevada City, California
  - **Relationship:** Get along fine, minimal contact
  - **Note:** Mackenzie very close to her
- **Stacey Borden** — Former partner, mother of Oliver and Sophie (never legally married)
  - **Background:** Harvard graduate, lives in Calabasas
  - **Custody exchanges:** Geoff picks up kids Thursday 1:50pm from Chaparral Elementary (Calabasas), drops off Saturday 5pm
  - **Monitoring:** Alert on job/career changes, LinkedIn updates

### Family Schedule (Normal Pattern)
- **Thursday 1:50 PM:** Pick up Oliver & Sophie from Chaparral Elementary, Calabasas
- **Saturday 5:00 PM:** Drop off with Stacey Borden (former partner, never legally married, Harvard grad, Calabasas resident)
- **Pattern:** Geoff has kids Thursday afternoon → Saturday evening

### Contact Info
- **Personal:** [REDACTED]
- **Work:** geoffrey.clapp@progyny.com (competitive reports → here)
- **GitHub:** gclapp

### Timezone Handling (CRITICAL)
**Rule:** When confused about timezones, ALWAYS ask Geoff for confirmation.

**Conversion Reference:**
- **UTC → Pacific:** Subtract 8 hours
- **Examples:**
  - 10:00 PM UTC = 2:00 PM PST (same day)
  - 12:00 AM UTC (midnight) = 4:00 PM PST (previous day)
  - 8:00 AM UTC = 12:00 AM PST (midnight, same calendar day in Pacific)

**Common Mistakes to Avoid:**
- Midnight UTC is NOT midnight Pacific (it's 4 PM previous day)
- Don't assume date flips at the same time in both zones
- When UTC is 12 AM-8 AM, the Pacific date is one day behind

**Action:** Double-check all timezone conversions. When in doubt, state both times and ask for confirmation.

### Current Travel
- **Feb 22-24:** Four Seasons Resort Scottsdale, AZ — Room 913
- **Feb 25 (Tue):** Board meeting (morning), then travel to Portland
  - **Flights:** Delta 2130 + Delta 1373 (connection through Salt Lake City)
- **Feb 26 (Wed):** Nike Day 1, Portland OR
- **Feb 27 (Thu):** Nike Day 2, Portland OR — returned to LA ~11:59 PM
- **Mar 15-17:** New York City

**Note:** Travel schedule affects daily routine and availability. Check timezone and location before scheduling calls or expecting responses.

### Progyny Leadership
| Role | Name |
|------|------|
| CEO | Pete Anevski |
| CMO | Risa Fisher |
| COO | Melissa Cummings |
| CTO | Steven Leist |
| CCO | Katie Higgins |
| CMO | Janet Choi, M.D. |

### Competitors to Monitor
**Priority:** Maven (CEO: Kate Ryder), Pomelo Health
**Primary:** Carrot, KindBody, WIN Fertility
**Menopause Focus:** Midi, Geneev, Evernow

### Competitive Intelligence Setup
- **Frequency:** Daily reports (only if news worth reporting)
- **Destination:** geoffrey.clapp@progyny.com (work email)
- **Real-time alerts:** For newsworthy items
- **Format:** Professional, CEO-ready **HTML emails** (may be forwarded to Pete Anevski)
- **Layout Style:** Color-coded priority sections (🔴🟠🟡), signal callouts, clean hyperlinks
- **Links:** Embedded/hyperlinked (not raw URLs) for clean readability
- **Sources:** News, LinkedIn, Reddit, industry publications, job boards
- **Hyperlink Requirement:** ALL document references, story citations, and sources must be clickable hyperlinks — never plain text URLs
- **User Feedback:** Reddit monitoring for customer sentiment and complaints
  - Subreddits: r/infertility, r/TTC, r/Menopause, r/IVF, r/maternity, r/pregnancy, r/babybumps, and company-specific forums
- **Citations:** Required for all sources
- **News Age:** Only include news >45 days old if part of a trend worth mentioning
- **Duplicates:** OK to resend important items in "Stuff I've sent but you should be sure to read" section
- **Talent Intelligence (REQUIRED):**
  - Executive departures/arrivals with dates and context (use color-coding: red for departures, green for arrivals)
  - Open roles by competitor with totals (Carrot, Maven, Kindbody, etc.)
  - Headcount data (employee numbers) for each competitor vs Progyny
  - Include hiring focus/growth signals from job postings
- **Glassdoor Intelligence:** Include table with: overall rating, total reviews, % recommend to friend, % CEO approval — plus 12-month trendline charts for each metric. **Include Progyny as bellwether comparison in all competitive tables.**
- **Data Storage:** Maintain local historical data for trendline generation
- **First report:** Feb 22, 2026
- **LESSONS LEARNED (Feb 24, 2026):**
  - Always include headcount comparison, open roles totals, and executive movement tracking
  - Use proper HTML formatting with tables — never send as plain text
  - **No company overviews** — skip the website/headquarters/CEO tables and get straight to the news/signals
  - **Citations required for EVERY claim** — never drop source links; every fact, quote, and data point must have a clickable hyperlink

### Preferences
- **Airlines:** Delta (very loyal customer)
  - SkyMiles #: 9446540677
- **Hotels:** Marriott Bonvoy (loyal user)
- **Enjoys:** Fine wine, watches, creating new things
- **Check-ins:** Include "Daily Status List" format showing pending, completed, and recently completed (72-hour retention) tasks

## Pets
- **Greta** — Geoff's dog
  - **Care:** Rover sitter comes to house when Geoff travels
  - **Needs:** 2 walks per day, morning and evening feeding

## Active Projects & Tasks

### Blog Series: "Building with OpenClaw"
- **Week 1 post:** Written, pending final edits and publication
- **Week 2 post:** Draft in progress
- **Platform:** Substack (recommended)
- **Graphics:** Need lobster-themed visuals for each week
- **Social:** LinkedIn + Twitter/X cross-posting setup needed

### Business Venture Planning
- **Options evaluated:** Lead Gen Agency, Newsletter, Content Agency
- **Approach:** Portfolio strategy (test 3, double down on winners)
- **Investment:** $5,000 over 3 months
- **Target:** $5,000/month by month 5-6
- **Decision needed:** Which to prioritize

### Travel Planning
- **Outside Lands 2026:** Aug 6-10, fully planned, reminders scheduled
- **Arizona trip:** Apr 2-5, tasks created
- **NYC trips:** Multiple, tracked in calendar

### Skills To Install
- **youtube-pro or solo-you2idea-extract:** For video analysis
- **linkedin-automator:** Social media posting
- **twitter-openclaw:** Social media posting
- **analytics:** Post statistics tracking

### System Issues
- **Gateway token mismatch:** OpenClaw subagent spawning failing
  - **Fix:** `openclaw gateway restart` (requires human intervention)
  - **Impact:** Cannot spawn parallel subagents

### Social Media 2FA Backup Codes (March 11, 2026)
**Status:** Twitter/X 2FA enabled ✅ | LinkedIn 2FA pending

**Twitter/X Backup Code:**
- Purpose: Single-use backup for login if authenticator unavailable
- Storage: `~/.openclaw/config/sensitive-credentials.json` (secure, 600 permissions)
- Generated: March 11, 2026

**Instructions:**
- Use this code if you can't receive text messages or access authenticator app
- One-time use only — generate new backup codes after use
- Generate additional backup codes at: https://x.com/settings/security

**Note:** All sensitive credentials (API keys, backup codes, tokens) stored in:
- `~/.openclaw/config/sensitive-credentials.json`
- File permissions: 600 (owner read/write only)
- Never committed to GitHub

## Upcoming Important Dates

### Power Outage - March 11, 2026
**SCE Maintenance Outage #000800505235**
- **Date:** Wednesday, March 11, 2026
- **Time:** 9:30 AM - 3:30 PM (6 hours)
- **Location:** Calabasas home (23675 Park Capri, Unit 23)
- **Reason:** Transformer upgrade
- **Action:** Plan alternate work location, charge devices night before

### Birthday Reminders
| Person | Birthday | Next Milestone |
|--------|----------|----------------|
| Geoff | April 11, 1973 | 53rd (2026) |
| Grace | July 22, 1996 | 30th (2026) |
| Mackenzie | April 26, 2005 | 21st (2026) |
| Oliver | December 21, 2017 | 9th (2026) |
| Sophie | September 25, 2019 | 7th (2026) |

## Automated Routines

### Daily GitHub & Journal Sync (March 11, 2026)
**Schedule:** 11:59 AM PT and 11:59 PM PT daily  
**Purpose:** 
1. Commit any uncommitted changes to GitHub
2. Create public journal entries for any private entries not yet published

**Implementation:**
- Cron job: `59 11,23 * * *` (11:59 AM and 11:59 PM PT)
- Script: `scripts/daily-github-sync.sh`
- Actions:
  - `git add .` → `git commit -m "[timestamp] Daily sync"` → `git push`
  - Check for private journal entries without public counterparts
  - Generate sanitized public versions
  - Commit to public-journal repo

**Status:** ⏳ Pending setup

## Script Archive Policy (May 25, 2026)

**Rule:** Only actively used scripts remain in `scripts/`. All old versions, experiments, and deprecated scripts belong in `scripts/archive/`.

### Archive Structure
```
scripts/archive/
├── README.md              # Documentation of active vs archived scripts
├── competitor-intel/      # Old competitor intelligence versions
├── token-health/          # Deprecated token monitoring scripts
├── whoop/                 # Old Whoop integration versions
├── travel/                # Old travel automation versions
├── heartbeat/             # Old heartbeat system versions
├── watch-search/          # Old watch search implementations
├── gdocs/                 # Google Docs experiments (deprecated)
├── calendar/              # Old calendar auth scripts
├── progyny/               # Old Progyny intelligence versions
├── health/                # Old health processing scripts
├── morning-email/         # Old morning email generators
└── misc/                  # Experimental/one-off scripts
```

### Policy Rules
1. **Active scripts only in scripts/** — If it's not in crontab or actively called, archive it
2. **Preserve file permissions** when moving to archive
3. **Update README.md** when archiving — document why it was archived
4. **Never execute from archive/** — Scripts there may have broken paths/dependencies
5. **Reference only** — Use for code examples, logic reference, historical context

### Active Scripts (Canonical Versions)
| Function | Active Script | Archived Versions |
|----------|---------------|-------------------|
| Competitor Intel | `daily-competitor-report-v3.sh` | v2, email_v2/v3, intelligence_v2/v3 |
| Token Auto-Refresh | `token_auto_refresh_v2.py` | token_auto_refresh.py, token_daily_monitor.py, token_health_check.py, token_health_check_v2.py |
| Whoop Daily Fetch | `whoop_daily_fetch.py` | whoop_auth.py, whoop_exchange.py, whoop_fetch.py, whoop_reauth.py, fetch_whoop_daily.py |
| Whoop Alerts | `whoop_alerts.py` | — |
| Travel Checker | `calendar_travel_checker.py` | travel_automation.py, travel_automation_subtasks.py, travel_automation_urgent.py, travel_automation_v2.py |
| Heartbeat | `heartbeat_sender.py` | heartbeat_sender_v2.py, heartbeat_sender_backup_*.py |
| Calendar Reader | `calendar_reader.py` | calendar_auth*.py, calendar_intelligence.py |
| Token Health Monitor | `token_health_monitor.py` | — |
| Watch Hunt | `watch-hunt-cron.sh` | watch_search*.py (4 versions) |
| Progyny Intel | `progyny_intel_cron.sh` | progyny_exec_report_strict.py, progyny_executive_report.py, progyny_intelligence.py, progyny_sentiment_monitor.py |

### When to Archive
- Script has a newer version (v2, v3, etc.)
- Script was experimental and never put in production
- Functionality was consolidated into another script
- Script hasn't been run in 30+ days
- Dependencies are broken/outdated

### When to Keep in scripts/
- Script is referenced in crontab
- Script is called by other active scripts
- Script is a utility used for manual operations
- Script is newly created and being tested (< 7 days)
