#!/usr/bin/env python3
"""
Competitive Intelligence Feed Monitor
Scans Maven and other competitor feeds, outputs new articles for email reports
"""

import feedparser
import json
import os
import sys
from datetime import datetime, timezone
import hashlib
import subprocess

# Paths
FEEDS_FILE = os.path.expanduser("~/.openclaw/workspace/config/competitor-feeds.json")
SEEN_FILE = os.path.expanduser("~/.openclaw/workspace/config/competitor-seen.json")
OUTPUT_FILE = os.path.expanduser("~/.openclaw/workspace/config/competitor-new-articles.json")
LOG_FILE = os.path.expanduser("~/.openclaw/workspace/logs/competitor-monitor.log")

def log(msg):
    """Log message with timestamp"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_msg = f"[{timestamp}] {msg}"
    print(log_msg)
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    with open(LOG_FILE, 'a') as f:
        f.write(log_msg + '\n')

def load_feeds():
    """Load competitor feeds configuration"""
    default_feeds = {
        "Maven - Google Alerts": "https://www.google.com/alerts/feeds/13519883000496020413/8201260240037632355",
        # Add more feeds here as needed
    }
    
    if os.path.exists(FEEDS_FILE):
        with open(FEEDS_FILE, 'r') as f:
            return json.load(f)
    return default_feeds

def load_seen():
    """Load previously seen article IDs"""
    if os.path.exists(SEEN_FILE):
        with open(SEEN_FILE, 'r') as f:
            return set(json.load(f))
    return set()

def save_seen(seen):
    """Save seen article IDs"""
    os.makedirs(os.path.dirname(SEEN_FILE), exist_ok=True)
    with open(SEEN_FILE, 'w') as f:
        json.dump(list(seen), f)

def article_id(entry):
    """Generate unique ID for an article"""
    content = f"{entry.get('link', '')}:{entry.get('title', '')}"
    return hashlib.md5(content.encode()).hexdigest()

def scan_feed(name, url):
    """Scan a single feed for new articles"""
    try:
        feed = feedparser.parse(url)
        articles = []
        
        for entry in feed.entries:
            aid = article_id(entry)
            published = entry.get('published', entry.get('updated', ''))
            
            articles.append({
                'id': aid,
                'title': entry.get('title', 'No title'),
                'link': entry.get('link', ''),
                'published': published,
                'summary': entry.get('summary', '')[:500],
                'source': name
            })
        
        return articles
    except Exception as e:
        log(f"Error scanning {name}: {e}")
        return []

def scan_with_blogwatcher():
    """Use blogwatcher as alternative scanner"""
    try:
        result = subprocess.run(
            ['blogwatcher', 'scan'],
            capture_output=True,
            text=True,
            timeout=60
        )
        return result.stdout
    except Exception as e:
        log(f"Blogwatcher scan failed: {e}")
        return ""

def categorize_article(title, summary):
    """Categorize article by priority/signal type"""
    title_lower = title.lower()
    summary_lower = summary.lower()
    combined = title_lower + " " + summary_lower
    
    # High priority signals
    high_priority = ['funding', 'acquisition', 'acquires', 'merger', 'ipo', 'series ', 'raised', 'investment', '$']
    for signal in high_priority:
        if signal in combined:
            return 'high', 'funding/acquisition'
    
    # Medium priority
    medium_priority = ['partnership', 'partners', 'collaboration', 'launch', 'expansion', 'new product', 'ceo', 'executive']
    for signal in medium_priority:
        if signal in combined:
            return 'medium', 'partnership/launch'
    
    return 'low', 'general'

def main():
    log("=== Starting Competitive Intelligence Scan ===")
    
    feeds = load_feeds()
    seen = load_seen()
    all_new = []
    
    for name, url in feeds.items():
        log(f"Scanning: {name}")
        articles = scan_feed(name, url)
        new_articles = [a for a in articles if a['id'] not in seen]
        
        if new_articles:
            log(f"  Found {len(new_articles)} new articles")
            for article in new_articles:
                priority, category = categorize_article(article['title'], article['summary'])
                article['priority'] = priority
                article['category'] = category
                all_new.append(article)
                seen.add(article['id'])
        else:
            log(f"  No new articles")
    
    # Save updated seen list
    save_seen(seen)
    
    # Sort by priority
    priority_order = {'high': 0, 'medium': 1, 'low': 2}
    all_new.sort(key=lambda x: priority_order.get(x['priority'], 3))
    
    # Save to output file
    if all_new:
        os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
        with open(OUTPUT_FILE, 'w') as f:
            json.dump(all_new, f, indent=2)
        log(f"✅ Saved {len(all_new)} new articles to {OUTPUT_FILE}")
        
        # Print summary for cron/email
        print(f"\n{'='*60}")
        print(f"COMPETITIVE INTELLIGENCE ALERT: {len(all_new)} new articles")
        print(f"{'='*60}")
        for article in all_new:
            badge = "🔴" if article['priority'] == 'high' else "🟡" if article['priority'] == 'medium' else "⚪"
            print(f"\n{badge} [{article['source']}] {article['title']}")
            print(f"   Priority: {article['priority'].upper()} | Category: {article['category']}")
            print(f"   {article['link'][:80]}...")
        print(f"\n{'='*60}")
    else:
        log("✅ No new articles found")
    
    # Also try blogwatcher for any other configured blogs
    log("\nChecking blogwatcher feeds...")
    bw_output = scan_with_blogwatcher()
    if bw_output and "new article" in bw_output.lower():
        log("Blogwatcher found additional articles")
        print(bw_output)
    else:
        log("No additional articles from blogwatcher")

if __name__ == "__main__":
    main()
