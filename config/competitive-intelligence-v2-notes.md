# Competitive Intelligence System v2 — Fixes & Enhancements

## Problems Identified (March 22, 2026)

### 1. Stale Content Issue
- **Problem:** Same Costco/Sesame article from March 9 was being sent repeatedly
- **Root Cause:** `competitor-seen.json` was empty/corrupted, deduplication failed
- **Fix:** Created new `competitor-seen-v2.json` with proper structure + article age checking (>7 days = stale)

### 2. Missing LinkedIn Monitoring
- **Problem:** No tracking of executive posts, company announcements, or LinkedIn activity
- **Fix:** Created `linkedin_monitor.py` that searches for:
  - Executive team updates (Kate Ryder, etc.)
  - Job changes and appointments
  - Company announcements and milestones

### 3. Missing Job Change Tracking
- **Problem:** No tracking of executive departures/hires
- **Fix:** Added job change detection to LinkedIn monitor + dedicated tracking in seen file

### 4. Limited Sources
- **Problem:** Only Google Alerts RSS feeds (often stale)
- **Fix:** Added:
  - Web search via Brave API (real-time news)
  - Industry news feeds (fertility, femtech, healthcare)
  - LinkedIn executive monitoring
  - Job board monitoring (placeholder for future)

## New System Architecture

### Scripts
| Script | Purpose | Schedule |
|--------|---------|----------|
| `competitor_intelligence_v2.py` | RSS + web search monitoring | 2x daily |
| `linkedin_monitor.py` | Executive + job change tracking | 2x daily |
| `competitor_email_v2.py` | HTML email generation | On demand |
| `daily-competitor-report-v2.sh` | Master orchestrator | 2x daily |

### Data Files
| File | Purpose |
|------|---------|
| `competitive-intelligence-config.json` | Sources, companies, exec teams |
| `competitor-seen-v2.json` | Deduplication + tracking |
| `competitor-articles-v2.json` | News articles |
| `linkedin-updates.json` | Executive updates |
| `competitor-email-v2.html` | Generated email |

### Monitored Companies
- **Maven** (high priority) — Kate Ryder, Samantha Wertheimer, Nisha Gopal, Shaina Harris
- **Carrot** (high priority) — Tammy Sun, Juli Insinger, Rachel Simmons
- **KindBody** (high priority) — Gina Bartasi, Stephanie Gorman, Anate Brauer
- **WIN Fertility** (medium priority)
- **Progyny** (bellwether) — for comparison

### Signal Categories
1. **Critical:** Funding, acquisition, IPO, major investment
2. **High:** Partnerships, executive hires, expansions, product launches
3. **Medium:** Hiring, growth, awards, general news
4. **Job Changes:** Executive moves, departures, appointments
5. **Executive Updates:** LinkedIn posts, interviews, thought leadership

## What You Need to Provide

### 1. Brave API Key (for web search)
```bash
# Add to ~/.bashrc or environment
export BRAVE_API_KEY="your-api-key-here"
```
Get key at: https://brave.com/search/api/

### 2. LinkedIn API (optional, for deeper monitoring)
- Requires LinkedIn Developer account
- Or use LinkedIn Sales Navigator API
- Current system uses web search as fallback

## Deduplication Logic

### Article Age Check
- Articles >7 days old = automatically skipped
- Prevents stale content from being sent

### Seen Tracking
- Each article ID tracked with:
  - `found_at`: When first discovered
  - `sent`: Whether sent in email
  - `sent_count`: How many times sent (max 2)
  - `last_sent`: Timestamp of last send

### Max Send Limit
- Articles can be sent maximum 2 times
- After 2 sends, permanently skipped
- Prevents spam

## Schedule

**Twice Daily:**
- 7:00 AM PT — Morning report
- 2:00 PM PT — Afternoon update

## Next Steps

1. **Add Brave API key** for web search functionality
2. **Review first few reports** to ensure quality
3. **Add more LinkedIn sources** if needed (company pages, specific executives)
4. **Tune priority thresholds** based on feedback

## Files Changed/Created

### New Files
- `scripts/competitor_intelligence_v2.py`
- `scripts/linkedin_monitor.py`
- `scripts/competitor_email_v2.py`
- `scripts/daily-competitor-report-v2.sh`
- `config/competitive-intelligence-config.json`
- `config/competitor-seen-v2.json`

### Updated
- Cron jobs (now use v2 scripts)

---

**Status:** ✅ System v2 deployed and running
**Last Updated:** March 22, 2026
