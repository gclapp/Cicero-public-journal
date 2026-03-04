# Blogwatcher Setup for Competitive Intelligence
## Maven, Carrot, KindBody, WIN, Pomelo Monitoring

**Status:** In Progress | **Created:** March 3, 2026

---

## RSS Feeds Found

### ✅ Carrot Fertility
**Feed:** https://www.carrotfertility.com/blog/feed/
**Status:** Active RSS feed available
**Content:** Company blog posts, updates

### 🔍 Others to Check
- Maven Clinic: Check https://www.mavenclinic.com/blog
- KindBody: Check https://www.kindbody.com/blog
- WIN Fertility: Check https://www.winfertility.com/news
- Pomelo Health: Check https://www.pomelohealth.com/blog

### 📰 Industry News (Backup)
- Fierce Healthcare: https://www.fiercehealthcare.com/rss.xml
- Healthcare Dive: https://www.healthcaredive.com/feeds/news/
- MedCity News: https://medcitynews.com/feed/

---

## Manual Setup Steps

### Option 1: Blogwatcher CLI (Current)
```bash
# Check status
openclaw blogwatcher list

# Add feeds
openclaw blogwatcher subscribe https://www.carrotfertility.com/blog/feed/
openclaw blogwatcher subscribe [maven-feed-url]
openclaw blogwatcher subscribe [kindbody-feed-url]

# Watch for updates
openclaw blogwatcher watch
```

### Option 2: Google Alerts → RSS
1. Go to https://www.google.com/alerts
2. Create alerts for:
   - "Maven Clinic" funding OR acquisition
   - "Carrot Fertility" news
   - "KindBody" fertility
   - "WIN Fertility" 
   - "Pomelo Health"
   - Kate Ryder (Maven CEO)
3. Set delivery to "RSS feed"
4. Copy RSS URLs
5. Add to blogwatcher

### Option 3: Web Monitoring (Alternative)
If RSS not available, use web scraper to check:
- Company blog pages daily
- News sites for mentions
- LinkedIn for executive posts

---

## What to Monitor

### Company News
- Funding rounds
- Acquisitions
- Product launches
- Partnership announcements
- Leadership changes

### CEO Activity (Kate Ryder priority)
- LinkedIn posts
- Speaking engagements
- Interviews/articles
- Board appointments

### Industry Signals
- New competitors entering market
- Regulatory changes
- Market trends
- Customer sentiment (Reddit)

---

## Delivery

**Frequency:** Daily check (morning)
**Format:** Brief summary via Telegram/email
**Urgency:** Real-time alerts for major news
**Storage:** Log to memory/competitive-intel.md

---

## Current Status

- ✅ Skill installed
- ⏳ RSS feeds being identified
- ⏳ Configuration in progress
- ⏳ Testing delivery

**Next Action:** Complete RSS feed setup and test first scan
