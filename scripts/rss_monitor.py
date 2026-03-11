#!/usr/bin/env python3
"""
Lightweight RSS feed monitor for competitive intelligence
Monitors Maven Google Alerts feed and sends notifications on new items
"""

import feedparser
import json
import os
import sys
from datetime import datetime
from urllib.parse import urlparse
import hashlib

# Configuration
FEEDS_FILE = os.path.expanduser("~/.openclaw/workspace/config/rss-feeds.json")
SEEN_FILE = os.path.expanduser("~/.openclaw/workspace/config/rss-seen.json")

def load_feeds():
    """Load configured RSS feeds"""
    if os.path.exists(FEEDS_FILE):
        with open(FEEDS_FILE, 'r') as f:
            return json.load(f)
    return {}

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
    # Use link + title hash as ID
    content = f"{entry.get('link', '')}:{entry.get('title', '')}"
    return hashlib.md5(content.encode()).hexdigest()

def scan_feed(name, url):
    """Scan a single feed for new articles"""
    try:
        feed = feedparser.parse(url)
        new_articles = []
        
        for entry in feed.entries:
            aid = article_id(entry)
            new_articles.append({
                'id': aid,
                'title': entry.get('title', 'No title'),
                'link': entry.get('link', ''),
                'published': entry.get('published', ''),
                'summary': entry.get('summary', '')[:500]  # Truncate summary
            })
        
        return new_articles
    except Exception as e:
        print(f"Error scanning {name}: {e}")
        return []

def main():
    feeds = load_feeds()
    seen = load_seen()
    
    if not feeds:
        print("No feeds configured. Add feeds to:", FEEDS_FILE)
        return
    
    all_new = []
    
    for name, url in feeds.items():
        articles = scan_feed(name, url)
        new_articles = [a for a in articles if a['id'] not in seen]
        
        if new_articles:
            print(f"\n📰 {name}: {len(new_articles)} new article(s)")
            for article in new_articles:
                print(f"  • {article['title'][:80]}...")
                print(f"    {article['link'][:100]}...")
                all_new.append({
                    'feed': name,
                    **article
                })
                seen.add(article['id'])
        else:
            print(f"📰 {name}: No new articles")
    
    # Save updated seen list
    save_seen(seen)
    
    # Output summary for potential email integration
    if all_new:
        print(f"\n✅ Total new articles: {len(all_new)}")
        # Save to file for email script to pick up
        summary_file = os.path.expanduser("~/.openclaw/workspace/config/rss-new-articles.json")
        with open(summary_file, 'w') as f:
            json.dump(all_new, f, indent=2)
    else:
        print("\n✅ No new articles found")

if __name__ == "__main__":
    main()
