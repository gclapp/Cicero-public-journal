# TOOLS.md - Local Notes

## Email Configuration
- **From:** [REDACTED]
- **Method:** Gmail SMTP with app password
- **Config file:** ~/.openclaw/email_config.json (contains app password)
- **Script:** /home/ubuntu/.openclaw/workspace/scripts/send_email.py
- **Format:** ALWAYS send as HTML (not plain text)

### Usage
```bash
# Send a simple email
python3 scripts/send_email.py --to "[REDACTED]" --subject "Subject" --body "Body text"

# Send HTML email
python3 scripts/send_email.py --to "[REDACTED]" --subject "Subject" --body "<h1>HTML</h1>" --html

# Read body from file
python3 scripts/send_email.py --to "[REDACTED]" --subject "Subject" --body-file /path/to/file.txt --html

# With CC
python3 scripts/send_email.py --to "[REDACTED]" --cc "keers003@gmail.com" --subject "Subject" --body "Body"
```

### Setup (if password expires)
1. Generate app password at https://myaccount.google.com/apppasswords
2. Run: `python3 scripts/send_email.py --setup YOUR_APP_PASSWORD`

---

## TTS Configuration
- **Provider:** ElevenLabs
- **Default Voice:** George (ID: JBFqnCBsd6RMkjVDRZzb)
- **Voice Description:** Warm, captivating storyteller
- **API Key:** ✅ Configured (ELEVENLABS_API_KEY environment variable)
- **Script:** /home/ubuntu/.openclaw/workspace/scripts/elevenlabs_tts.py

## ElevenLabs Voice Settings
- **Model:** eleven_multilingual_v2
- **Stability:** 0.5
- **Similarity Boost:** 0.75

## Usage
```bash
python3 scripts/elevenlabs_tts.py "Your text here"
```

---

## GitHub Configuration
- **Username:** gclapp
- **Email:** [REDACTED] (for git commits)
- **Profile:** https://github.com/gclapp
- **Auth Method:** SSH key or Personal Access Token (PAT) required

### Creating a New Repository
```bash
cd /path/to/project
git init
git add .
git commit -m "Initial commit"
git branch -m main

# Option A: SSH (if key is set up)
git remote add origin git@github.com:gclapp/REPO_NAME.git

# Option B: HTTPS with PAT
git remote add origin https://gclapp:TOKEN@github.com/gclapp/REPO_NAME.git

git push -u origin main
```

### Setup Authentication (One-time)
**Option 1: SSH Key (Recommended)**
```bash
ssh-keygen -t ed25519 -C "[REDACTED]"
cat ~/.ssh/id_ed25519.pub  # Add this to GitHub → Settings → SSH Keys
```

**Option 2: Personal Access Token (PAT)**
1. Go to https://github.com/settings/tokens
2. Generate new token (classic) with "repo" scope
3. Store in: ~/.openclaw/github_token.txt (chmod 600)

**Current PAT (stored in public-journal remote):** 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
- Scope: repo access
- Expires: Check GitHub settings
- Usage: `https://gclapp:TOKEN@github.com/gclapp/REPO_NAME.git`

### Active Repositories
| Repo | URL | GitHub Pages |
|------|-----|--------------|
| Cicero-public-journal | https://github.com/gclapp/Cicero-public-journal | — |
| geoff-watch-hunt | https://github.com/gclapp/geoff-watch-hunt | https://gclapp.github.io/geoff-watch-hunt/ |

### Automated Cron Jobs
| Job | Schedule | Script | Purpose |
|-----|----------|--------|---------|
| Watch Hunt | 9AM & 6PM PT daily | `scripts/watch-hunt-cron.sh` | Searches for 1973 Rolex Datejust, updates dashboard |

---

## Weekly Memory Consolidation
**Status:** ✅ ACTIVE - Runs every Sunday at 11 PM PT  
**Script:** `scripts/weekly_memory_consolidation.py`  
**Purpose:** Automatically summarizes daily logs into weekly reports

### How It Works
1. **Reads:** All daily logs from the past week (`memory/2026-MM-DD.md`)
2. **Extracts:** Key facts, people mentioned, places visited, tasks completed
3. **Generates:** Weekly summary with patterns and insights
4. **Creates:** `memory/2026-Week-XX.md` file
5. **Archives:** Daily details (kept but summarized)

### What It Captures
- People contacted (with mention counts)
- Places visited
- Tasks completed vs pending
- Key decisions made
- Patterns and trends
- Weight loss tracking progress
- Relationship updates

### Example Output
```
Week 9, 2026 Summary
- Days logged: 4
- Most contact: Tanisha, Grace
- Locations: 4 different places
- Tasks: 7 completed, 1 pending (88% completion)
- Weight loss: 2 days logged
```

### Manual Run
```bash
python3 scripts/weekly_memory_consolidation.py
```

### Benefits
- **File reduction:** 7 daily logs → 1 weekly summary
- **Pattern detection:** Weekly trends invisible in daily view
- **Quick review:** See entire week at a glance
- **Long-term storage:** Efficient archive of history

---

## Weight Loss Program 2026
**Goal:** Lose 20 lbs in 10-12 weeks  
**Plan:** `weight-loss-plan.md` | **Tracker:** `memory/weight-loss-2026.md`

### Nutrition
- **Calories:** 1,800-2,000/day
- **Protein:** 150-180g/day (30-35%)
- **Strategy:** High-protein, lower-carb, healthy fats
- **Apps:** Lose It! (food) + Whoop (recovery/strain)

### Exercise (5-6 days/week)
- **Mon/Wed/Fri:** Strength training (45 min)
- **Tue:** Cardio/walk (30-40 min)
- **Thu:** Active recovery (30 min)
- **Sat:** Fun activity/hike (60+ min)
- **Sun:** Rest (Whoop recovery)

### Reminders (Todoist)
- **Daily:** 5 tasks (weigh-in, food log, workout, water, Whoop check)
- **Weekly:** Sunday meal prep, progress review
- **Monthly:** Photos, measurements

### Travel-Friendly
- Hotel gym routines (20-30 min)
- Airport: protein bars, no sugary drinks
- NYC trips: walking meetings, hotel mornings

---

## Python Learning Program 2026
**Goal:** Write production-grade Python agents  
**Plan:** `python-learning-plan.md` | **Tracker:** `memory/python-learning-2026.md`  

### Timeline
- **Weeks 1-2:** Python Fundamentals (Java → Python)
- **Weeks 3-4:** Pythonic Patterns
- **Weeks 5-6:** Agent Foundations (APIs, LLMs)
- **Weeks 7-8:** Agent Architecture
- **Weeks 9-10:** Production Agents
- **Weeks 11-12:** Multi-Agent Systems

### Projects
1. Task Manager CLI
2. Web Scraper Agent
3. Chat Agent
4. Email Agent
5. Competitive Intel Agent
6. Multi-Agent System

### Weekly Commitment
- **Mon:** New concept (1 hr)
- **Tue:** LeetCode practice (45 min)
- **Wed:** Project work (1 hr)
- **Thu:** Code review with Cicero (30 min)
- **Fri:** Integration (45 min)

### Tools
- Python 3.11+, VS Code, Git
- OpenAI API, Virtual environments
- GitHub for code reviews

---

## Health Dashboard & Weight Loss Tracking
**Dashboard:** https://gclapp.github.io/health-dashboard/  
**Repo:** https://github.com/gclapp/health-dashboard  
**Data Sources:** Apple Health (primary) + Whoop (recovery/strain)  
**Goal:** Track 20 lb weight loss with data-driven insights  

### How It Works
1. **iPhone Shortcuts** exports Apple Health data daily at 9 PM
2. **Email sent** to [REDACTED] automatically
3. **Python processor** parses and analyzes data
4. **Dashboard updates** with weight trends, activity, insights
5. **Weekly reports** emailed with progress and recommendations

### Dashboard Features
- Weight loss chart with 7-day trend
- Daily steps and activity tracking
- Calorie in/out dashboard
- Sleep analysis
- Whoop recovery integration
- AI-generated insights ("You lose more weight when you sleep 8+ hours")

### Accountability System
- **Daily:** Todoist reminder to check dashboard
- **Daily:** I review your data when emails arrive
- **Sunday:** Weekly report with progress analysis
- **Bi-weekly:** Telegram check-in on trends
- **Immediate alerts:** If weight stalls for 5+ days

### Setup Files
- `health-dashboard/SHORTCUTS_SETUP.md` - iPhone setup guide
- `health_processor.py` - Data parsing and analysis
- `health-data.json` - Dashboard data file

---

## Private Infrastructure (Planned)
**Concept:** Private digital headquarters for Geoff & Cicero  
**Purpose:** Secure hosting for all dashboards and tools  
**Estimated Cost:** $8-17/month  
**Status:** Planning phase - awaiting go-ahead

### What We'll Host
- Health/weight loss dashboard
- Watch hunt tracker
- Document repository
- Agent control panel
- File storage

### Proposed Stack
- **Hosting:** DigitalOcean VPS ($6-12/month)
- **Domain:** TBD (geoffandcicero.com or similar)
- **Security:** Password protection + SSL + Cloudflare
- **Design:** Custom branded, dark mode

### Security
- Password-protected access
- HTTPS/SSL encryption
- Cloudflare DDoS protection
- Automated backups
- Firewall protection

### Next Steps
1. Choose domain name
2. Register domain (~$12-15/year)
3. Create DigitalOcean account
4. I'll configure everything else

**Full plan:** `private-infrastructure-plan.md`

---

## Stock Price Tracker (30-Day Rolling)
**Script:** `/home/ubuntu/.openclaw/workspace/scripts/fetch_stock_data.py`  
**History File:** `/home/ubuntu/.openclaw/workspace/data/stock-history.json`  
**Current Data:** `/home/ubuntu/.openclaw/workspace/data/stock-data.json`  
**Schedule:** Daily at 6 PM PT

### Tracked Stocks
| Symbol | Company | Priority |
|--------|---------|----------|
| **PGNY** | Progyny | High (Geoff's company) |
| AAPL | Apple | Medium |
| NVDA | NVIDIA | Medium |
| OMDA | Omada Health | Medium |

### Features
- ✅ 30-day rolling price history (JSON storage)
- ✅ 30-day change percentage calculation
- ✅ Daily closing price tracking
- ✅ Market indices (S&P 500, Dow Jones)
- ✅ Formatted summary for check-ins

### Manual Run
```bash
# Fetch current prices and update history
python3 scripts/fetch_stock_data.py

# Get summary only (if data exists)
python3 -c "from scripts.fetch_stock_data import get_stock_summary; print(get_stock_summary())"
```

### Output Format
```
📈 **Markets (30-Day View)**

**Indices:**
🟢 S&P 500: 6,624.70 (+0.00% today)
🟢 Dow Jones: 46,225.15 (+0.00% today)

**Your Watchlist (30-Day Change):**
🟢 **PGNY:** $17.87 (+5.23% / 30d)
🟢 AAPL: $249.94 (+2.15% / 30d)
🔴 NVDA: $180.40 (-1.82% / 30d)
🟢 OMDA: $14.11 (+3.45% / 15d)
```

### History Data Structure
```json
{
  "metadata": {
    "stocks": ["PGNY", "AAPL", "NVDA", "OMDA"],
    "max_days": 30
  },
  "history": {
    "PGNY": [
      {"date": "2026-03-19", "price": 17.87},
      {"date": "2026-03-18", "price": 17.65}
    ]
  }
}
```

---

## Watch Hunt Automation
**Dashboard:** https://gclapp.github.io/geoff-watch-hunt/
**Repo:** https://github.com/gclapp/geoff-watch-hunt

### How It Works
1. **Twice daily** (9 AM & 6 PM PT) the cron job runs
2. **Scrapling-powered search** bypasses anti-bot protection on Chrono24
3. Updates `watch-data.json` with new listings
4. Checks if existing watches are sold/removed
5. Commits & pushes to GitHub
6. Sends Telegram notification if new watches found

### Manual Run
```bash
# Run search manually (Scrapling version)
source ~/.openclaw/venvs/scrapling/bin/activate
python3 ~/.openclaw/workspace/scripts/watch_search_scrapling.py

# Run full update (search + push)
bash ~/.openclaw/workspace/scripts/watch-hunt-cron.sh
```

### View Logs
```bash
tail -f ~/.openclaw/workspace/logs/watch-hunt.log
```

### Multi-Search Dashboard (March 2026)
**Cover Page:** https://gclapp.github.io/geoff-watch-hunt/cover.html
**Results Page:** https://gclapp.github.io/geoff-watch-hunt/index.html

**Features:**
- ✅ Create new watch searches with custom parameters
- ✅ Toggle searches on/off
- ✅ View active and completed searches
- ✅ Track results per search
- ✅ Multi-site scraping (Chrono24 + more)
- ✅ Automatic cron execution

**Supported Sites (9 Total):**
| Site | Status | Notes |
|------|--------|-------|
| **Chrono24** | ✅ Complete | Full parsing, most reliable |
| **eBay** | ✅ Complete | Full parsing, large inventory |
| **Bob's Watches** | ✅ Complete | Product grid parsing |
| **Bulang & Sons** | ✅ Complete | Collection scraping |
| **Bezel** | ✅ Complete | Listing card parsing |
| **Crown & Caliber** | ✅ Complete | Product extraction |
| **Watches of Espionage** | ✅ Complete | Collection scraping |
| **WatchRecon** | ✅ Complete | Forum aggregator |
| **Reddit r/Watchexchange** | ✅ Complete | API-based, [WTS] posts only |

**Creating a New Search:**
```bash
# Via command line
python3 scripts/search_manager.py create \
  --name "Omega Speedmaster" \
  --brand "Omega" \
  --models "145.022,145.0022" \
  --year-min 1965 \
  --year-max 1975 \
  --dials "black" \
  --materials "steel" \
  --sources "chrono24"

# Or use the web interface at cover.html
```

**Managing Searches:**
```bash
# List all searches
python3 scripts/search_manager.py list

# Toggle on/off
python3 scripts/search_manager.py toggle <search_id>

# Mark as completed
python3 scripts/search_manager.py complete <search_id>

# Delete a search
python3 scripts/search_manager.py delete <search_id>
```

**Running Searches Manually:**
```bash
# Run all active searches
source ~/.openclaw/venvs/scrapling/bin/activate
python3 scripts/watch_search_multi.py
```

### Scrapling Integration (March 2026)
**Status:** ✅ **ACTIVE** - Multi-site scraping working!

**Scrapling Setup:**
- Virtual environment: `~/.openclaw/venvs/scrapling/`
- Browser automation with Playwright/Chromium
- Bypasses Cloudflare and anti-bot systems
- Handles multiple searches per run
- Slower than raw requests (~10-15s per page) but actually works

**Current Active Searches:**
1. **1973 Rolex Datejust** - 1601, 1603, 16014 (1970-1985, blue/black/champagne/linen)
2. **Omega Speedmaster Moonwatch** - 145.022, 145.0022, 3570.50 (1965-1975, black dial)

---

## Email Configuration
- **From:** [REDACTED]
- **Method:** Gmail SMTP with app password
- **Config file:** ~/.openclaw/email_config.json (contains app password)
- **Script:** /home/ubuntu/.openclaw/workspace/scripts/send_email.py

### Usage
```bash
# Send a simple email
python3 scripts/send_email.py --to "[REDACTED]" --subject "Subject" --body "Body text"

# Send HTML email
python3 scripts/send_email.py --to "[REDACTED]" --subject "Subject" --body "<h1>HTML</h1>" --html

# Read body from file
python3 scripts/send_email.py --to "[REDACTED]" --subject "Subject" --body-file /path/to/file.txt --html

# With CC
python3 scripts/send_email.py --to "[REDACTED]" --cc "keers003@gmail.com" --subject "Subject" --body "Body"
```

### Setup (if password expires)
1. Generate app password at https://myaccount.google.com/apppasswords
2. Run: `python3 scripts/send_email.py --setup YOUR_APP_PASSWORD`

---

## Cameras
- (Add camera names/locations as needed)

## SSH
- (Add SSH hosts/aliases as needed)

## Cron Job Management ⚠️ CRITICAL

**Issue:** System updates/restarts can wipe cron jobs without warning.

**Solution:** Automated backup + restore system

### Backup/Restore Script
```bash
# Backup current crontab
bash scripts/cron-backup.sh backup

# Restore from latest backup
bash scripts/cron-backup.sh restore

# Verify all expected jobs present
bash scripts/cron-backup.sh verify
```

### Active Cron Jobs (as of March 19, 2026)
| Job | Schedule | Script | Purpose |
|-----|----------|--------|---------|
| Heartbeat | Every 55 min | `heartbeat-check.sh` | Keep cache warm, check-ins |
| Watch Hunt | 9 AM & 6 PM PT | `watch-hunt-cron.sh` | 1973 Rolex search |
| Calendar Refresh | 6:55 AM PT | `calendar_reader.py` | Daily calendar sync |
| IMAP Check | Every 15 min | `imap-check-cron.sh` | Email monitoring |
| Competitor Report | 2 PM PT daily | `daily-competitor-report.sh` | Competitive intel |
| Security Audit | Sundays 8 AM PT | `weekly-security-audit.sh` | Security report |
| Reddit Report | Sundays 9 AM PT | `reddit-weekly-report.sh` | Sentiment analysis |
| Weekly Email | Saturdays 9 AM PT | `weekly-email-report.py` | Week summary |
| Stock Tracker | 6 PM PT daily | `fetch_stock_data.py` | 30-day rolling prices |
| NYC Reminder | March 12, 2 PM PT | `sunday-nyc-reminder.sh` | Trip reminder |

### Post-Update Checklist
After ANY system update or restart:
- [ ] Run `bash scripts/cron-backup.sh verify`
- [ ] If jobs missing, run `bash scripts/cron-backup.sh restore`
- [ ] Check logs: `tail ~/.openclaw/workspace/logs/*.log`

---

## Skill Status

### ✅ Ready
- **voice-call** — ✅ Twilio configured (+1 650 600 0919), tested and working
- **email** — ✅ Gmail configured ([REDACTED]), working via scripts/send_email.py
- **blogwatcher** — Installed, needs RSS feeds configured
- **weather** — Ready
- **whoop** — Installed and configured
- **SAG (TTS)** — ✅ ElevenLabs API configured, tested and working
- **opentable** — Built and ready (needs API credentials to activate)
  - Search restaurants by location, cuisine, price, time
  - Make/cancel/view reservations
  - Find nearby restaurants
  - Share reservations (WhatsApp, SMS, Email, OpenTable)

### ⏳ Pending Setup
- **Whoop OAuth** — Need Geoff to create dev app
- **Blogwatcher** — RSS feeds to configure
- **OpenTable API** — Need credentials to activate:
  ```bash
  mkdir -p ~/.openclaw/config
  echo '{"api_key": "YOUR_KEY"}' > ~/.openclaw/config/opentable.json
  ```
- **Delta Skill** — For flight tracking and SkyMiles integration (API research needed)
- **Marriott Skill** — For Bonvoy points and hotel booking (API research needed)

### 🛠️ Future Skills to Build
| Skill | Purpose | Status | Notes |
|-------|---------|--------|-------|
| **Delta Airlines** | Flight status, gate changes, SkyMiles tracking | Researching | Delta has developer API at apiportal.delta.com |
| **Marriott Bonvoy** | Hotel bookings, points balance, loyalty status | Researching | Developer portal at devportalprod.marriott.com |
| **Beli** | Restaurant ratings and recommendations | Researching | No public API yet; may need manual export |
| **Calendar Integration** | Automated flight/hotel detection from calendar | Planned | Google Calendar API + Gmail parsing |

---

Add whatever helps you do your job. This is your cheat sheet.