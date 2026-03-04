# Competitive Intelligence Monitoring Setup

## ✅ What's Installed

### 1. Blogwatcher (Go-based RSS monitor)
- **Location:** `~/go/bin/blogwatcher`
- **Usage:** `blogwatcher [add|remove|blogs|scan|articles|read]`
- **Status:** Installed and working

### 2. Python Competitor Monitor
- **Script:** `scripts/competitor_monitor.py`
- **Purpose:** Scans RSS feeds, categorizes articles by priority, tracks seen articles
- **Feeds config:** `config/competitor-feeds.json`
- **Seen tracking:** `config/competitor-seen.json`
- **Output:** `config/competitor-new-articles.json`

### 3. Email Generator
- **Script:** `scripts/competitor_email.py`
- **Purpose:** Generates HTML email content from new articles
- **Output:** `config/competitor-email.html`

## 📡 Current Feeds (6 Total)

| Priority | Entity | Type | Feed URL |
|----------|--------|------|----------|
| 🔷 **Primary** | **Progyny (PGNY)** | Self | Google Alerts RSS |
| 🔴 High | Maven | Competitor | Google Alerts RSS |
| 🔴 High | Carrot | Competitor | Google Alerts RSS |
| 🔴 High | KindBody | Competitor | Google Alerts RSS |
| 🔴 High | WIN Fertility | Competitor | Google Alerts RSS |
| 🔴 High | Pomelo Health | Competitor | Google Alerts RSS |

**Note:** PGNY is treated as a primary entity alongside competitors. All PGNY news (good and bad) appears in the competitive report.

## 🔧 How to Add More Feeds

### Option 1: Edit the feeds JSON file
```bash
nano ~/.openclaw/workspace/config/competitor-feeds.json
```

Add entries like:
```json
{
  "Progyny (PGNY) - Google Alerts": "https://www.google.com/alerts/feeds/...",
  "Maven - Google Alerts": "https://www.google.com/alerts/feeds/...",
  "Carrot - News": "https://www.google.com/alerts/feeds/...",
  "KindBody - Blog": "https://kindbody.com/feed"
}
```

### Option 2: Use blogwatcher CLI
```bash
export PATH=$PATH:/usr/local/go/bin
blogwatcher add "Competitor Name" "https://competitor.com/feed.xml"
```

## 🏃 Manual Run

```bash
# Scan for new articles
cd ~/.openclaw/workspace
python3 scripts/competitor_monitor.py

# Generate email HTML (includes PGNY + competitors)
python3 scripts/competitor_email.py

# View results
cat config/competitor-new-articles.json
```

## 📅 Cron Setup (Recommended)

Add to crontab for daily monitoring:
```bash
crontab -e
```

Add this line for daily 6 AM PT scan:
```
0 14 * * * cd /home/ubuntu/.openclaw/workspace && python3 scripts/competitor_monitor.py >> logs/competitor-cron.log 2>&1
```

## 📧 Email Report Structure

Reports include:

### 🔷 Progyny (PGNY) Section
- Featured prominently at the top
- All PGNY news (positive, negative, neutral)
- Priority badges (🔴🟡⚪)
- Category tags (funding, partnership, general)

### 🔴🟡⚪ Competitor Sections
- Grouped by priority
- Maven, Carrot, KindBody, WIN, Pomelo
- Same formatting as PGNY

## 🎯 Article Categorization

Articles are auto-categorized by priority:

| Priority | Triggers | Badge |
|----------|----------|-------|
| **High** | funding, acquisition, IPO, raised, $ | 🔴 |
| **Medium** | partnership, launch, expansion, CEO | 🟡 |
| **Low** | general news, mentions | ⚪ |

## 📊 Next Steps

1. **Set up Google Alert feeds for real monitoring:**
   - The current URLs are placeholders
   - Go to Google Alerts → Create alerts for each entity
   - Set delivery to RSS
   - Replace the placeholder URLs in `config/competitor-feeds.json`

2. **Integrate with daily email report:**
   - PGNY news now appears alongside competitors
   - Run: `python3 scripts/competitor_email.py`
   - Include the generated HTML in your competitive intel email

3. **Test the flow:**
   ```bash
   python3 scripts/competitor_monitor.py
   python3 scripts/competitor_email.py
   cat config/competitor-email.html
   ```

## 📝 Logs

- Monitor log: `logs/competitor-monitor.log`
- Cron log: `logs/competitor-cron.log`
- Blogwatcher log: `logs/blogwatcher-cron.log`
