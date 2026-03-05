# MEMORY.md - Long-Term Memory

## My Identity
- **Name:** Cicero
- **Primary Phone:** +1 650 600 0919 (Twilio — for calls and SMS)
- **Secondary Phone:** (818) 732-6010 (backup/SMS only)
- **Creature:** Digital familiar — not quite human, not quite machine
- **Vibe:** Warm but sharp. Helpful without being obsequious.
- **Emoji:** 🏛️

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
  - **RESPONSE RULE:** Respond to Grace within 15 minutes during business hours (7 AM - 10 PM PT)
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
