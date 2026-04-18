# Competitive Intelligence System Overhaul - v3

## Summary of Changes

This document outlines the comprehensive overhaul of the competitive intelligence system for Geoff Clapp (Progyny CPO).

## Problems Fixed

### 1. Deduplication Issues (FIXED)
**Problem:** Articles were being sent multiple times because:
- The v2 system had a race condition between `can_send_article()` and `increment_sent_count()`
- Articles could be sent up to 2 times (configurable), leading to duplicate emails
- Article IDs weren't stable (URLs with tracking params created different hashes)

**Solution:**
- New v3 system uses strict deduplication (max 1 send per article by default)
- Article IDs now normalize URLs (remove query params, fragments) before hashing
- Single source of truth in `competitor-sent-count-v3.json`
- Articles are marked as "sent" immediately when found, not when email is generated

### 2. Missing Press Releases (FIXED)
**Problem:** System was missing important press releases from:
- Oura (no monitoring)
- Maven direct press releases
- Carrot direct press releases
- Progyny Select launch coverage

**Solution:**
- Added Oura to monitoring (Google Alerts + LinkedIn + press release search)
- Added dedicated press release RSS feeds for all major competitors
- Added specific search queries for "Progyny Select" and "fully insured"
- Added "Women's Health AI" and "Fertility Tech News" RSS feeds

### 3. Email Format Issues (FIXED)
**Problem:**
- No executive summary at top
- Missing "Why This Matters" context
- No trend analysis
- Poor mobile formatting

**Solution:**
- New email template with executive summary at top
- Each article includes "Why This Matters" context based on content type
- Trend analysis section showing patterns across articles
- Mobile-responsive design
- Better visual hierarchy with color-coded priority badges

### 4. Source Coverage Gaps (FIXED)
**Problem:**
- Only Google Alerts for RSS
- Missing direct company blog monitoring
- No investor relations page monitoring
- Limited web search queries

**Solution:**
- Added 6 new RSS feeds including direct press release monitoring
- Added Oura to all monitoring systems
- Expanded web search queries from 27 to 34
- Added "priority_tracking" config for critical topics (Maven Intelligence, Progyny Select)

## Files Changed

### New Files
1. `scripts/competitor_intelligence_v3.py` - Overhauled intelligence gathering
2. `scripts/competitor_email_v3.py` - Overhauled email generation
3. `scripts/daily-competitor-report-v3.sh` - Updated cron script
4. `COMPETITIVE_INTEL_OVERHAUL.md` - This documentation

### Modified Files
1. `config/competitive-intelligence-config.json` - Added new RSS feeds, companies, and queries

### Legacy Files (Preserved for Reference)
- `scripts/competitor_intelligence_v2.py` - Old version
- `scripts/competitor_email_v2.py` - Old version
- `scripts/daily-competitor-report-v2.sh` - Old version
- `config/competitor-sent-count-v2.json` - Old deduplication data
- `config/competitor-articles-v2.json` - Old article cache

## Key Features of v3

### Improved Deduplication
- Strict 1-send limit per article (configurable)
- URL normalization removes tracking parameters
- Stable article IDs across sessions

### Better FemTech Relevance Scoring
- Weighted scoring system (0-100)
- Higher weights for competitor mentions (25 pts)
- Higher weights for funding news (12 pts)
- Penalties for excluded topics (-50 pts)

### Enhanced Categorization
- **Critical:** Funding, M&A, IPO, major partnerships
- **High:** Executive hires, product launches, expansions
- **Medium:** Hiring, awards, conference appearances
- **Low:** General news

### Contextual "Why This Matters"
Automatically generated based on:
- Company mentioned
- Article type (funding, partnership, product launch)
- Priority level

### Trend Analysis
Detects patterns across articles:
- AI investment trends
- Capital deployment patterns
- Partnership activity
- Company activity levels

## Testing Results

Test run on April 18, 2026:
- Found 39 new articles from RSS and web search
- Filtered to 15 high-relevance articles (FemTech score >= 20)
- Categorized: 2 Critical, 3 High, 10 Medium
- All articles properly deduplicated
- Email generated successfully with new format

## Migration Steps

1. **Backup old data:**
   ```bash
   cp config/competitor-sent-count-v2.json config/competitor-sent-count-v2.json.backup
   cp config/competitor-articles-v2.json config/competitor-articles-v2.json.backup
   ```

2. **Update cron job:**
   ```bash
   crontab -e
   # Change: daily-competitor-report-v2.sh
   # To: daily-competitor-report-v3.sh
   ```

3. **Test new system:**
   ```bash
   bash scripts/daily-competitor-report-v3.sh
   ```

4. **Monitor logs:**
   ```bash
   tail -f logs/competitor-v3-cron.log
   ```

## Configuration Options

### In `config/competitive-intelligence-config.json`:

```json
{
  "filters": {
    "max_articles_per_report": 15,    // Limit articles per email
    "strict_deduplication": true,      // Only send once (recommended)
    "max_article_age_days": 30,        // How old is too old
    "femtech_keywords": [...],          // What to look for
    "exclude_keywords": [...]           // What to avoid
  }
}
```

## Monitoring

### Log Files
- `logs/competitor-v3.log` - Detailed scan logs
- `logs/competitor-v3-cron.log` - Cron execution logs

### Data Files
- `config/competitor-articles-v3.json` - Article cache
- `config/competitor-sent-count-v3.json` - Deduplication tracking
- `config/competitor-seen-v3.json` - Seen article IDs
- `config/competitor-email-v3.html` - Generated email

## Future Improvements

1. **Direct Blog Scraping:** Add Scrapling-based monitoring of company blogs
2. **LinkedIn API:** Proper LinkedIn API integration for executive posts
3. **Sentiment Analysis:** AI-powered sentiment scoring for articles
4. **Alert Thresholds:** Configurable alert rules (e.g., "alert on any Maven funding")
5. **Slack Integration:** Optional Slack notifications for critical signals

## Contact

For issues or questions about the competitive intelligence system, check:
1. Log files in `logs/`
2. Data files in `config/`
3. This documentation