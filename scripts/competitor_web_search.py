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
OUTPUT_FILE = CONFIG_DIR / "web-search-new-articles.json"
LOG_FILE = Path.home() / ".openclaw" / "workspace" / "logs" / "web-search-monitor.log"

# Search queries for each competitor
SEARCH_QUERIES = {
    "Progyny": "Progyny PGNY news",
    "Maven": "Maven Clinic fertility news",
    "Carrot": "Carrot Fertility news",
    "KindBody": "KindBody fertility news",
    "WIN Fertility": "WIN Fertility news",
    "Pomelo": "Pomelo Health news"
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

def search_news(company, query):
    """Search for news using web_search tool"""
    try:
        # Import here to avoid issues if tool not available
        import sys
        sys.path.insert(0, str(Path.home() / ".openclaw" / "workspace" / "scripts"))
        
        # Use web_search via exec
        import subprocess
        result = subprocess.run(
            ['python3', '-c', f'''
import sys
sys.path.insert(0, "/home/ubuntu/.openclaw/workspace/scripts")
from web_search import web_search
results = web_search("{query}", count=5)
print(json.dumps(results))
'''],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0:
            return json.loads(result.stdout)
        return []
    except Exception as e:
        log(f"Search error for {company}: {e}")
        return []

def scan_all_competitors():
    """Scan all competitors via web search"""
    seen = load_seen()
    new_articles = []
    
    for company, query in SEARCH_QUERIES.items():
        log(f"Searching: {company}")
        
        # Search for news from last 7 days
        results = search_news(company, query)
        
        for result in results:
            url = result.get('url', '')
            if url and url not in seen:
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
                log(f"  New article: {article['title'][:60]}...")
    
    # Save seen URLs
    save_seen(seen)
    
    # Save new articles for email
    if new_articles:
        with open(OUTPUT_FILE, 'w') as f:
            json.dump(new_articles, f, indent=2)
        log(f"✅ Found {len(new_articles)} new articles via web search")
    else:
        log("No new articles found via web search")
    
    return new_articles

if __name__ == "__main__":
    log("=== Starting Web Search Competitive Intelligence ===")
    articles = scan_all_competitors()
    log(f"=== Scan complete: {len(articles)} new articles ===")
