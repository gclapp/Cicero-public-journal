#!/usr/bin/env python3
"""
Competitive Intelligence Web Search Backup
Uses Brave Search API to find recent news when RSS feeds fail
"""

import json
import os
from datetime import datetime, timedelta
from pathlib import Path

# Paths
CONFIG_DIR = Path.home() / ".openclaw" / "workspace" / "config"
SEEN_FILE = CONFIG_DIR / "web-search-seen.json"
SENT_COUNT_FILE = CONFIG_DIR / "web-search-sent-count.json"
OUTPUT_FILE = CONFIG_DIR / "web-search-new-articles.json"
LOG_FILE = Path.home() / ".openclaw" / "workspace" / "logs" / "web-search-monitor.log"

# Search queries for each competitor
SEARCH_QUERIES = {
    "Progyny": "Progyny PGNY fertility benefits news",
    "Maven": "Maven Clinic fertility benefits news",
    "Carrot": "Carrot Fertility benefits news",
    "KindBody": "KindBody fertility benefits news",
    "WIN Fertility": "WIN Fertility benefits news",
    "Pomelo": "Pomelo Health fertility benefits news",
    "Sesame": "Sesame fertility benefits news"
}

def log(msg):
    """Log message with timestamp"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_msg = f"[{timestamp}] {msg}"
    print(log_msg)
    os.makedirs(LOG_FILE.parent, exist_ok=True)
    with open(LOG_FILE, 'a') as f:
        f.write(log_msg + '\n')

def load_seen():
    """Load previously seen article URLs"""
    if SEEN_FILE.exists():
        with open(SEEN_FILE, 'r') as f:
            return set(json.load(f))
    return set()

def save_seen(seen):
    """Save seen article URLs"""
    SEEN_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(SEEN_FILE, 'w') as f:
        json.dump(list(seen), f)

def load_sent_counts():
    """Load article send counts (tracks how many times each article was sent)"""
    if SENT_COUNT_FILE.exists():
        with open(SENT_COUNT_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_sent_counts(counts):
    """Save article send counts"""
    SENT_COUNT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(SENT_COUNT_FILE, 'w') as f:
        json.dump(counts, f)

def can_send_article(url, sent_counts):
    """
    Check if article can be sent (max 2 times).
    Returns True if article hasn't been sent 2+ times yet.
    """
    count = sent_counts.get(url, 0)
    return count < 2

def increment_sent_count(url, sent_counts):
    """Increment the send count for an article"""
    sent_counts[url] = sent_counts.get(url, 0) + 1
    return sent_counts

def search_news(company, query):
    """Search for news using web_search tool via OpenClaw CLI"""
    try:
        import subprocess
        # Use openclaw web-search command with freshness filter for recent news
        result = subprocess.run(
            ['openclaw', 'web-search', query, '--count', '5', '--freshness', 'pw'],
            capture_output=True,
            text=True,
            timeout=60
        )
        
        if result.returncode == 0:
            # Parse the output - it's JSON after the tool header
            output = result.stdout
            # Find the JSON part (after the tool execution output)
            try:
                # Look for the results array in the output
                lines = output.split('\n')
                for line in lines:
                    line = line.strip()
                    if line.startswith('[') and line.endswith(']'):
                        return json.loads(line)
                    if line.startswith('{') and '"results"' in line:
                        data = json.loads(line)
                        return data.get('results', [])
                # Try parsing the whole output as JSON
                return json.loads(output)
            except json.JSONDecodeError:
                log(f"Could not parse search results for {company}")
                return []
        return []
    except Exception as e:
        log(f"Search error for {company}: {e}")
        return []

def scan_all_competitors():
    """Scan all competitors via web search"""
    seen = load_seen()
    sent_counts = load_sent_counts()
    new_articles = []
    skipped_duplicates = 0
    
    for company, query in SEARCH_QUERIES.items():
        log(f"Searching: {company}")
        
        # Search for news from last 7 days
        results = search_news(company, query)
        
        for result in results:
            url = result.get('url', '')
            if url and url not in seen:
                # Check if we've already sent this article 2+ times
                if not can_send_article(url, sent_counts):
                    log(f"  ⚠️ Skipping (already sent 2x): {result.get('title', 'No title')[:50]}...")
                    skipped_duplicates += 1
                    seen.add(url)  # Mark as seen so we don't check again
                    continue
                
                article = {
                    'title': result.get('title', 'No title'),
                    'link': url,
                    'published': result.get('published', 'Recent'),
                    'summary': result.get('description', '')[:300],
                    'source': company,
                    'found_via': 'web_search'
                }
                new_articles.append(article)
                seen.add(url)
                # Increment send count for this article
                sent_counts = increment_sent_count(url, sent_counts)
                log(f"  New article: {article['title'][:60]}...")
    
    # Save seen URLs and sent counts
    save_seen(seen)
    save_sent_counts(sent_counts)
    
    # Save new articles for email
    if new_articles:
        with open(OUTPUT_FILE, 'w') as f:
            json.dump(new_articles, f, indent=2)
        log(f"✅ Found {len(new_articles)} new articles via web search")
        if skipped_duplicates > 0:
            log(f"⚠️ Skipped {skipped_duplicates} articles (already sent 2x max)")
    else:
        if skipped_duplicates > 0:
            log(f"⚠️ No new articles found (skipped {skipped_duplicates} duplicates - max 2 sends reached)")
        else:
            log("No new articles found via web search")
    
    return new_articles

if __name__ == "__main__":
    log("=== Starting Web Search Competitive Intelligence ===")
    articles = scan_all_competitors()
    log(f"=== Scan complete: {len(articles)} new articles ===")
