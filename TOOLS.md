# TOOLS.md - Local Notes

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

## Watch Hunt Automation
**Dashboard:** https://gclapp.github.io/geoff-watch-hunt/
**Repo:** https://github.com/gclapp/geoff-watch-hunt

### How It Works
1. **Twice daily** (9 AM & 6 PM PT) the cron job runs
2. Searches: Bob's Watches, Chrono24, Bulang & Sons, Bezel, eBay
3. Updates `watch-data.json` with new listings
4. Checks if existing watches are sold/removed
5. Commits & pushes to GitHub
6. Sends Telegram notification if new watches found

### Manual Run
```bash
# Run search manually
python3 ~/.openclaw/workspace/scripts/watch_search.py

# Run full update (search + push)
bash ~/.openclaw/workspace/scripts/watch-hunt-cron.sh
```

### View Logs
```bash
tail -f ~/.openclaw/workspace/logs/watch-hunt.log
```

### ⚠️ Scraping Limitations
Most watch sites block automated scraping:
- **Chrono24:** 403 Forbidden
- **Bob's Watches:** 403 Forbidden  
- **Bulang & Sons:** 403 Forbidden
- **Bezel:** Search URL issues

**Workarounds:**
1. Use sites' saved search alerts (they email you)
2. Manual browsing + send me links to track
3. Future: Browser automation with Selenium
4. Check if APIs available for partners

**Current automation still useful for:**
- Checking if tracked watches are still available
- Updating dashboard timestamps
- Logging activity
- Maintaining the tracker

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

---

Add whatever helps you do your job. This is your cheat sheet.