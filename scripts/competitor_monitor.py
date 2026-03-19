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
SENT_COUNT_FILE = os.path.expanduser("~/.openclaw/workspace/config/competitor-sent-count.json")
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
        "Progyny - Google Alerts": "https://www.google.com/alerts/feeds/13519883000496020413/8201260240037632356",
        "Carrot - Google Alerts": "https://www.google.com/alerts/feeds/13519883000496020413/8201260240037632357",
        "KindBody - Google Alerts": "https://www.google.com/alerts/feeds/13519883000496020413/8201260240037632358",
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

def load_sent_counts():
    """Load article send counts (tracks how many times each article was sent)"""
    if os.path.exists(SENT_COUNT_FILE):
        with open(SENT_COUNT_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_sent_counts(counts):
    """Save article send counts"""
    os.makedirs(os.path.dirname(SENT_COUNT_FILE), exist_ok=True)
    with open(SENT_COUNT_FILE, 'w') as f:
        json.dump(counts, f)

def can_send_article(article_id, sent_counts):
    """
    Check if article can be sent (max 2 times).
    Returns True if article hasn't been sent 2+ times yet.
    """
    count = sent_counts.get(article_id, 0)
    return count < 2

def increment_sent_count(article_id, sent_counts):
    """Increment the send count for an article"""
    sent_counts[article_id] = sent_counts.get(article_id, 0) + 1
    return sent_counts

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
    sent_counts = load_sent_counts()
    all_new = []
    skipped_duplicates = 0
    
    for name, url in feeds.items():
        log(f"Scanning: {name}")
        articles = scan_feed(name, url)
        new_articles = [a for a in articles if a['id'] not in seen]
        
        if new_articles:
            log(f"  Found {len(new_articles)} new articles")
            for article in new_articles:
                # Check if we've already sent this article 2+ times
                if not can_send_article(article['id'], sent_counts):
                    log(f"  ⚠️ Skipping (already sent 2x): {article['title'][:50]}...")
                    skipped_duplicates += 1
                    seen.add(article['id'])  # Mark as seen so we don't check again
                    continue
                
                priority, category = categorize_article(article['title'], article['summary'])
                article['priority'] = priority
                article['category'] = category
                all_new.append(article)
                seen.add(article['id'])
                # Increment send count for this article
                sent_counts = increment_sent_count(article['id'], sent_counts)
        else:
            log(f"  No new articles")
    
    # Save updated seen list and sent counts
    save_seen(seen)
    save_sent_counts(sent_counts)
    
    # Sort by priority
    priority_order = {'high': 0, 'medium': 1, 'low': 2}
    all_new.sort(key=lambda x: priority_order.get(x['priority'], 3))
    
    # Save to output file
    if all_new:
        os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
        with open(OUTPUT_FILE, 'w') as f:
            json.dump(all_new, f, indent=2)
        log(f"✅ Saved {len(all_new)} new articles to {OUTPUT_FILE}")
        if skipped_duplicates > 0:
            log(f"⚠️ Skipped {skipped_duplicates} articles (already sent 2x max)")
        
        # Print summary for cron/email
        print(f"\n{'='*60}")
        print(f"COMPETITIVE INTELLIGENCE ALERT: {len(all_new)} new articles")
        if skipped_duplicates > 0:
            print(f"(Skipped {skipped_duplicates} duplicate articles - max 2 sends reached)")
        print(f"{'='*60}")
        for article in all_new:
            badge = "🔴" if article['priority'] == 'high' else "🟡" if article['priority'] == 'medium' else "⚪"
            send_count = sent_counts.get(article['id'], 1)
            count_indicator = f" [send {send_count}/2]" if send_count > 1 else ""
            print(f"\n{badge} [{article['source']}] {article['title']}{count_indicator}")
            print(f"   Priority: {article['priority'].upper()} | Category: {article['category']}")
            print(f"   {article['link'][:80]}...")
        print(f"\n{'='*60}")
    else:
        if skipped_duplicates > 0:
            log(f"⚠️ No new articles to send (skipped {skipped_duplicates} duplicates - max 2 sends reached)")
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
