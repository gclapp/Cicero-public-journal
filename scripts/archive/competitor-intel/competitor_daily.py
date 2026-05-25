#!/usr/bin/env python3
"""
Daily Competitive Intelligence - Combined RSS + Web Search
Run via cron daily at 7 AM PT
"""

import subprocess
import json
from datetime import datetime
from pathlib import Path

def run_rss_monitor():
    """Run RSS feed monitor"""
    result = subprocess.run(
        ['python3', '/home/ubuntu/.openclaw/workspace/scripts/competitor_monitor.py'],
        capture_output=True,
        text=True
    )
    return result.returncode == 0

def run_web_search():
    """Run web search for competitors"""
    result = subprocess.run(
        ['python3', '/home/ubuntu/.openclaw/workspace/scripts/competitor_web_search.py'],
        capture_output=True,
        text=True
    )
    return result.returncode == 0

def merge_results():
    """Merge RSS and web search results"""
    rss_file = Path('/home/ubuntu/.openclaw/workspace/config/competitor-new-articles.json')
    web_file = Path('/home/ubuntu/.openclaw/workspace/config/web-search-articles.json')
    output_file = Path('/home/ubuntu/.openclaw/workspace/config/competitor-daily-articles.json')
    
    all_articles = []
    seen_ids = set()
    
    # Load RSS results
    if rss_file.exists():
        with open(rss_file) as f:
            rss_articles = json.load(f)
        for article in rss_articles:
            if article['id'] not in seen_ids:
                all_articles.append(article)
                seen_ids.add(article['id'])
    
    # Load web search results
    if web_file.exists():
        with open(web_file) as f:
            web_articles = json.load(f)
        for article in web_articles:
            if article['id'] not in seen_ids:
                all_articles.append(article)
                seen_ids.add(article['id'])
    
    # Sort by date (newest first)
    all_articles.sort(key=lambda x: x.get('published', ''), reverse=True)
    
    # Save merged results
    with open(output_file, 'w') as f:
        json.dump(all_articles, f, indent=2)
    
    return len(all_articles)

def main():
    """Run daily competitive intelligence"""
    print(f"[{datetime.now().isoformat()}] Starting daily competitive intel...")
    
    # Run both monitors
    rss_ok = run_rss_monitor()
    web_ok = run_web_search()
    
    # Merge results
    count = merge_results()
    
    print(f"[{datetime.now().isoformat()}] Found {count} new articles")
    
    # Send email if articles found
    if count > 0:
        subprocess.run([
            'python3', 
            '/home/ubuntu/.openclaw/workspace/scripts/competitor_email.py'
        ])
    
    return 0

if __name__ == "__main__":
    exit(main())
