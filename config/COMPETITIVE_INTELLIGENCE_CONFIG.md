# Competitive Intelligence System v3.1
## Documentation & Configuration

**Last Updated:** March 28, 2026  
**Status:** PRODUCTION READY  
**Critical:** This file contains the canonical configuration for competitive intelligence reports

---

## System Architecture

### Components

| Component | File | Purpose |
|-----------|------|---------|
| **Data Collector** | `scripts/competitor_intelligence_v2.py` | Fetches news, RSS, LinkedIn, job boards |
| **Email Generator** | `scripts/competitor_email_v3.py` | Creates HTML email with all sections |
| **Reddit Collector** | `scripts/reddit_intel_collector.py` | Gathers Reddit intelligence |
| **Glassdoor Fetcher** | `scripts/glassdoor_fetcher.py` | Company satisfaction ratings |
| **Progyny Monitor** | `scripts/progyny_sentiment_monitor.py` | Brand mention tracking |
| **Cron Script** | `scripts/daily-competitor-report-v2.sh` | Orchestrates daily execution |

### Data Sources

1. **RSS Feeds** — Google Alerts for Maven, Carrot, Kindbody, FemTech
2. **Web Search** — Brave Search API (real-time news)
3. **LinkedIn** — Executive posts and company updates
4. **Reddit** — Patient communities (via reddit-search-but-free skill)
5. **Glassdoor** — Employee satisfaction metrics
6. **Job Boards** — Hiring signals and growth indicators

---

## Email Format (LOCKED)

### Section Order (DO NOT CHANGE)

1. **Executive Summary** — Key trends, stats, alerts
2. **🔴 Critical Signals** — Immediate action required
3. **🟠 High Priority** — Important developments
4. **🟡 Medium Priority** — Context and monitoring
5. **💬 Reddit Intelligence** — Patient/community sentiment
6. **💼 LinkedIn Executive Activity** — Leadership updates
7. **📊 Glassdoor Comparison** — Employee satisfaction
8. **Footer** — Sources and timestamp

### Visual Design (LOCKED)

- **Background:** #0f0f0f (near black)
- **Text:** #e0e0e0 (light gray)
- **Accent:** #3b82f6 (blue)
- **Critical:** #dc2626 (red)
- **High:** #ea580c (orange)
- **Medium:** #f59e0b (yellow)
- **Success:** #16a34a (green)
- **Font:** system-ui, -apple-system, sans-serif
- **Max-width:** 800px

### Required Elements

Every email MUST include:
- [ ] Date and time generated
- [ ] Total signal count
- [ ] Breakdown by priority
- [ ] Each section (even if empty — show "No new signals")
- [ ] Glassdoor table (always include Progyny as baseline)
- [ ] Source attribution

---

## Content Rules

### Article Filtering

- **Max age:** 30 days (skip older articles)
- **Max sends:** 2 per article (deduplication)
- **FemTech relevance:** Must score >25 to be included
- **Priority scoring:**
  - Critical: Funding, acquisitions, major partnerships, executive departures
  - High: Product launches, significant hires, policy changes
  - Medium: General news, minor updates, industry context

### Reddit Monitoring

**Subreddits watched:**
- r/infertility — Patient experiences
- r/IVF — Treatment discussions
- r/TTC — Trying to conceive
- r/Menopause — Menopause care

**Search terms:**
- Progyny, Maven, Carrot, Kindbody, WIN
- "fertility benefits", "IVF insurance", "fertility coverage"

**Provider:** PullPush (no auth required)

### Glassdoor Metrics

| Company | Rating | Reviews | Recommend | CEO |
|---------|--------|---------|-----------|-----|
| Progyny | 4.2 | 156 | 78% | 82% |
| Maven | 4.0 | 89 | 72% | 75% |
| Carrot | 3.8 | 67 | 68% | 70% |
| Kindbody | 3.5 | 45 | 62% | 65% |
| WIN | 3.2 | 34 | 55% | 58% |

**Note:** Progyny always shown first as baseline comparison

---

## API Keys & Credentials

### Brave Search API
- **Key:** `BSAQvzsdCTmv48KVZCYZxO2Uc2-Wgbf`
- **Status:** Active
- **Limit:** 2,000 queries/month (free tier)
- **Used in:** `competitor_intelligence_v2.py`

### Environment Variable
```bash
export BRAVE_API_KEY="BSAQvzsdCTmv48KVZCYZxO2Uc2-Wgbf"
```

---

## Cron Schedule

```
# Competitive Intelligence - twice daily
0 14,21 * * * /home/ubuntu/.openclaw/workspace/scripts/daily-competitor-report-v2.sh
```

**Times (PT):**
- 7:00 AM — Morning report
- 2:00 PM — Afternoon update

---

## File Locations

### Config Files
- `config/competitive-intelligence-config.json` — RSS feeds, search queries
- `config/competitor-seen-v2.json` — Deduplication tracking
- `config/competitor-sent-count-v2.json` — Article send counts
- `config/competitor-articles-v2.json` — Latest articles
- `config/reddit-intelligence.json` — Reddit data
- `config/glassdoor-data.json` — Glassdoor ratings
- `config/progyny-sentiment.json` — Brand mentions

### Output
- `config/competitor-email-v3.html` — Generated email
- `logs/competitor-v2.log` — Execution log

### Scripts
- `scripts/competitor_intelligence_v2.py`
- `scripts/competitor_email_v3.py`
- `scripts/reddit_intel_collector.py`
- `scripts/glassdoor_fetcher.py`
- `scripts/progyny_sentiment_monitor.py`
- `scripts/daily-competitor-report-v2.sh`

---

## Troubleshooting

### No articles found
1. Check Brave API key: `echo $BRAVE_API_KEY`
2. Verify RSS feeds are active
3. Check logs: `tail -f ~/.openclaw/workspace/logs/competitor-v2.log`

### Reddit not working
- Reddit provider blocks scraping (expected)
- PullPush provider should be used (automatic)
- No auth required

### Glassdoor data stale
- Run: `python3 scripts/glassdoor_fetcher.py`
- Data refreshes automatically with each report

---

## Change Log

### March 28, 2026 — v3.1
- ✅ Added Reddit intelligence (reddit-search-but-free skill)
- ✅ Added Glassdoor satisfaction table
- ✅ Added Progyny sentiment monitoring
- ✅ Locked email format and visual design
- ✅ Documented all configuration
- ✅ Set 30-day article age limit
- ✅ Set 2-send limit per article

### March 27, 2026 — v3.0
- ✅ Consolidated v1 and v2 systems
- ✅ Added Brave Search API integration
- ✅ Added LinkedIn executive monitoring
- ✅ Added job board tracking

---

## DO NOT MODIFY WITHOUT APPROVAL

This configuration is LOCKED. Any changes must be:
1. Discussed with Geoff
2. Tested in isolation
3. Documented in this file
4. Approved before deployment

**The reports matter. Get it right.**
