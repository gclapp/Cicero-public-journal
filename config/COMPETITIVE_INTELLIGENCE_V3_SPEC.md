# Competitive Intelligence System v3 — Documentation
## Established: March 28, 2026

This document captures the locked format, rules, and structure for the competitive intelligence system. **Do not modify without explicit approval.**

---

## Email Report Structure (LOCKED)

### Section Order (Mandatory)
1. **Executive Summary** — 2-3 sentence thematic analysis of all signals
2. **Stats Bar** — Critical / High / Medium / Progyny mention counts
3. **🔴 Critical Signals** — Max 3, highest priority competitive moves
4. **🟠 High Priority** — Max 3, significant announcements
5. **🟡 Medium Priority** — Max 5, industry trends
6. **🏢 Glassdoor** — Employee satisfaction table (6 companies)
7. **💼 Executive Web Mentions** — Web search results about executives (NOT LinkedIn posts)
8. **📊 Progyny Market Mentions** — Progyny visibility tracking with dates
9. **Footer** — System info, 30-day filter notice

### Content Rules (Hard-Coded)

| Rule | Implementation |
|------|----------------|
| **30-Day Filter** | All articles MUST have date scraped from URL. Articles >30 days auto-excluded. |
| **Max 2 Sends** | Each article tracked by URL hash. Max 2 sends, then permanently excluded. |
| **Dates Required** | Every article displays actual publication date (scraped from meta tags). "Date unknown" not acceptable. |
| **Summaries** | 2-3 sentence "Why it matters" on every article. Auto-generated based on content type. |
| **Source Links** | Every mention must have clickable URL for validation. |
| **Deduplication** | URL-based hashing prevents duplicate articles across sources. |

### Date Scraping Rules
- Try meta tags first: `article:published_time`, `pubdate`, `date`
- Fallback to `<time>` tags
- Fallback to text patterns (e.g., "March 27, 2026")
- If no date found → exclude article
- If date >30 days old → exclude with console logging

### Priority Classification

**🔴 Critical:**
- Funding rounds >$10M
- M&A announcements
- Major product launches
- Executive departures/hires (C-level)
- Partnerships with Fortune 500

**🟠 High:**
- Funding <$10M
- Product updates
- Mid-level hires
- Geographic expansion
- Awards/recognition

**🟡 Medium:**
- Industry trend pieces
- General news mentions
- Blog posts
- Event appearances

---

## Progyny Executive Brief (Separate Report)

### Format
- **Icon:** Progyny favicon (Google s2 favicon service)
- **Title:** "Progyny Executive Brief"
- **Subtitle:** Date | "Strict 30-day filter" | mention count

### Sections
1. **Executive Summary** — Thematic analysis of Progyny mentions
2. **Stats Bar** — Financial / Executive / Partnerships / Other counts
3. **Notable Mentions** — Top 5 with full summaries and source links
4. **Category Breakdown** — Grouped by: Financial, Executive, Product, Partnership, Competitive, Sentiment, Regulatory
5. **Source Index** — Complete list of all sources with validation links

### Data Storage
```
config/progyny-intelligence/
├── mentions/              # Individual JSON files per mention
├── weekly-summaries/      # Weekly summary JSON files
├── sources-index.json     # Master source validation index
└── README.md             # System documentation
```

---

## LinkedIn Section (Current State)

**IMPORTANT:** Current data is from web search results, NOT actual LinkedIn posts.

### Label
"Executive Web Mentions" (not "LinkedIn Activity")

### Data Source
- Web search results mentioning executives + "LinkedIn"
- Google Alerts for exec names
- No actual post dates available

### Future Enhancement (Todoist #6gGF7g38HCpPFwgx)
Build browser-based scraper:
- Playwright/Selenium automation
- Login session management
- Extract actual post content and dates
- Rate limiting to avoid blocking

---

## Technical Implementation

### Key Scripts
| Script | Purpose |
|--------|---------|
| `competitor_email_v3.py` | Main email generator with all rules |
| `competitor_intelligence_v2.py` | Data collection (RSS + web search) |
| `progyny_exec_report_strict.py` | Progyny-only report with strict filtering |
| `progyny_intelligence.py` | Progyny data collector |
| `glassdoor_fetcher.py` | Employee satisfaction data |
| `reddit_intel_collector.py` | Reddit mentions by company |

### Cron Schedule
| Job | Time | Script |
|-----|------|--------|
| Competitive Intel | 7:00 AM, 2:00 PM PT | `daily-competitor-report-v2.sh` |
| Progyny Intel | 8:00 AM PT daily | `progyny-intel-cron.sh` |
| Progyny Weekly | Sundays 8:00 AM PT | `progyny_intel_cron.py` |

### Environment Variables Required
```bash
BRAVE_API_KEY=         # For web search (optional but recommended)
```

---

## Validation Checklist

Before marking any report as "complete":
- [ ] Executive summary present (2-3 sentences)
- [ ] All articles have dates (scraped, not "found_at")
- [ ] No articles >30 days old
- [ ] Max 2 sends per article enforced
- [ ] Source links clickable
- [ ] "Why it matters" summary on every article
- [ ] Glassdoor table included
- [ ] Progyny section has dates + summaries
- [ ] LinkedIn section labeled correctly ("Web Mentions")

---

## Change Log

**March 28, 2026:**
- Locked email format and section order
- Implemented strict 30-day date filtering with URL scraping
- Added 2-send maximum deduplication
- Fixed LinkedIn section to show "Web Mentions" (accurate label)
- Added Progyny favicon to executive brief
- Documented all rules in this file

---

**DO NOT MODIFY WITHOUT EXPLICIT APPROVAL FROM GEOFF.**
