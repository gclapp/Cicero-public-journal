# COMPETITIVE INTELLIGENCE SYSTEM — LOCKED CONFIGURATION
## March 28, 2026

---

## ✅ WHAT'S PERSISTED

### 1. Email Format (LOCKED)
- **Dark theme:** #0f0f0f background, #e0e0e0 text
- **Section order:** Executive Summary → Critical → High → Medium → Reddit → LinkedIn → Glassdoor
- **Visual style:** Clean, minimal, professional
- **Max-width:** 800px

### 2. Data Sources (LOCKED)
- **RSS Feeds:** Google Alerts for Maven, Carrot, Kindbody, FemTech
- **Web Search:** Brave Search API (key: BSAQvzsdCTmv48KVZCYZxO2Uc2-Wgbf)
- **Reddit:** r/infertility, r/IVF, r/TTC, r/Menopause (via reddit-search-but-free skill)
- **Glassdoor:** Employee satisfaction ratings (Progyny baseline)
- **LinkedIn:** Executive posts (when available)

### 3. Content Rules (LOCKED)
- **Article age limit:** 30 days max
- **Send limit:** 2 times per article max
- **FemTech relevance:** Must score >25
- **Priority:** Critical (funding, acquisitions) → High (launches, hires) → Medium (general)

### 4. Schedule (LOCKED)
- **7:00 AM PT** — Morning report
- **2:00 PM PT** — Afternoon update
- **Cron:** `0 14,21 * * *`

### 5. Files (LOCKED LOCATIONS)
```
scripts/competitor_intelligence_v2.py    # Data collector
scripts/competitor_email_v3.py           # Email generator
scripts/reddit_intel_collector.py        # Reddit intelligence
scripts/glassdoor_fetcher.py             # Glassdoor ratings
scripts/daily-competitor-report-v2.sh    # Cron orchestrator

config/COMPETITIVE_INTELLIGENCE_CONFIG.md  # This documentation
config/competitor-articles-v2.json         # Article data
config/reddit-intelligence.json            # Reddit data
config/glassdoor-data.json                 # Glassdoor ratings
```

---

## 🔧 HOW TO VERIFY IT'S WORKING

### Check cron is set:
```bash
crontab -l | grep competitor
```
Expected: `0 14,21 * * * /home/ubuntu/.openclaw/workspace/scripts/daily-competitor-report-v2.sh`

### Check Brave API key:
```bash
echo $BRAVE_API_KEY
```
Expected: `BSAQvzsdCTmv48KVZCYZxO2Uc2-Wgbf`

### Check Reddit skill:
```bash
cd ~/.openclaw/workspace/skills/reddit-search-but-free/scripts
npx tsx reddit.ts watchlist
```
Expected: r/infertility, r/IVF, r/TTC, r/Menopause

### Check last report:
```bash
ls -la ~/.openclaw/workspace/config/competitor-email-v3.html
```

---

## 🚨 DO NOT CHANGE WITHOUT DISCUSSION

These elements are LOCKED:
- Email visual design
- Section order
- Content filtering rules
- Schedule
- File locations

If something needs changing:
1. Tell Geoff first
2. Update COMPETITIVE_INTELLIGENCE_CONFIG.md
3. Test thoroughly
4. Commit with clear message

---

## 📊 CURRENT STATUS

| Component | Status | Last Run |
|-----------|--------|----------|
| RSS Feeds | ✅ Active | 2026-03-28 |
| Brave Search | ✅ Active | 2026-03-28 |
| Reddit | ✅ Active | 2026-03-28 |
| Glassdoor | ✅ Active | 2026-03-28 |
| LinkedIn | ⚠️ Limited | 2026-03-28 |
| Cron | ✅ Scheduled | Daily 7AM/2PM PT |

---

## 📁 BACKUP LOCATION

All code backed up to:
- **GitHub:** https://github.com/gclapp/cicero-backup
- **Commit:** 320a110 (March 28, 2026)
- **Cron backup:** `config/cron-backups/crontab-20260328-054424.txt`

---

**The system is locked, documented, and backed up.**
**Reports will generate automatically twice daily.**
**No more redoing work.**
