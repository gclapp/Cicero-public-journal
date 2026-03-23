#!/bin/bash
# Daily Competitive Intelligence Report Generator
# Runs at 6 AM PT (14:00 UTC) daily
# Sends email only if there are new articles
# Includes PGNY alongside competitors as primary entity

WORKSPACE="/home/ubuntu/.openclaw/workspace"
cd "$WORKSPACE"

# Set PATH for Go
export PATH=$PATH:/usr/local/go/bin

echo "[$(date)] Starting competitive intelligence scan..." >> logs/competitor-reports.log

# Run RSS feed monitor (primary source)
python3 scripts/competitor_monitor.py > /tmp/competitor_scan.log 2>&1
RSS_COUNT=0
if [ -f config/competitor-new-articles.json ]; then
    RSS_COUNT=$(jq length config/competitor-new-articles.json 2>/dev/null || echo 0)
fi
echo "[$(date)] RSS scan found: $RSS_COUNT articles" >> logs/competitor-reports.log

# Run web search backup (catches what RSS misses)
python3 scripts/competitor_web_search.py > /tmp/web_search_scan.log 2>&1
WEB_COUNT=0
if [ -f config/web-search-new-articles.json ]; then
    WEB_COUNT=$(jq length config/web-search-new-articles.json 2>/dev/null || echo 0)
fi
echo "[$(date)] Web search found: $WEB_COUNT articles" >> logs/competitor-reports.log

# Combine articles from both sources
python3 << 'PYEOF'
import json
from pathlib import Path

rss_file = Path("config/competitor-new-articles.json")
web_file = Path("config/web-search-new-articles.json")
combined_file = Path("config/competitor-new-articles.json")

all_articles = []

# Load RSS articles
if rss_file.exists():
    try:
        with open(rss_file) as f:
            all_articles.extend(json.load(f))
    except:
        pass

# Load web search articles
if web_file.exists():
    try:
        with open(web_file) as f:
            all_articles.extend(json.load(f))
    except:
        pass

# Remove duplicates by URL
seen_urls = set()
unique_articles = []
for article in all_articles:
    url = article.get('link', '')
    if url and url not in seen_urls:
        seen_urls.add(url)
        unique_articles.append(article)

# Save combined
with open(combined_file, 'w') as f:
    json.dump(unique_articles, f, indent=2)

print(f"Combined: {len(unique_articles)} unique articles")
PYEOF

# Check if there are new articles
if [ -f config/competitor-new-articles.json ] && [ -s config/competitor-new-articles.json ]; then
    TOTAL_COUNT=$(jq length config/competitor-new-articles.json 2>/dev/null || echo 0)
    echo "[$(date)] Total unique articles: $TOTAL_COUNT" >> logs/competitor-reports.log
    
    # Generate HTML email (includes PGNY + competitors)
    python3 scripts/competitor_email.py
    
    # Check if email HTML was generated
    if [ -f config/competitor-email.html ]; then
        # Send the email to Geoff and Steven
        python3 scripts/send_email.py \
            --to "geoffrey.clapp@progyny.com" \
            --cc "steven.leist@progyny.com" \
            --subject "Competitive Intelligence Report - $(date '+%B %d, %Y')" \
            --body-file config/competitor-email.html \
            --html
        
        echo "[$(date)] Competitive report sent to Geoff + Steven ($TOTAL_COUNT articles)" >> logs/competitor-reports.log
    fi
else
    echo "[$(date)] No new competitive intelligence to report" >> logs/competitor-reports.log
fi
