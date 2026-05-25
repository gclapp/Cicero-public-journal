#!/usr/bin/env python3
"""
Progyny Market Sentiment Monitor
Tracks what the market is saying about Progyny
Sources: News, Reddit, Twitter/X (if available), Glassdoor
"""

import os
import json
import requests
import subprocess
from datetime import datetime, timedelta
from pathlib import Path

OUTPUT_FILE = Path.home() / ".openclaw" / "workspace" / "config" / "progyny-sentiment.json"
LOG_FILE = Path.home() / ".openclaw" / "workspace" / "logs" / "progyny-sentiment.log"

def log(msg):
    """Log with timestamp"""
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{ts}] {msg}")
    with open(LOG_FILE, 'a') as f:
        f.write(f"[{ts}] {msg}\n")

def load_existing():
    """Load existing sentiment data"""
    if OUTPUT_FILE.exists():
        with open(OUTPUT_FILE) as f:
            return json.load(f)
    return {"mentions": [], "executive_news": [], "last_updated": None}

def save_data(data):
    """Save sentiment data"""
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    data["last_updated"] = datetime.now().isoformat()
    with open(OUTPUT_FILE, 'w') as f:
        json.dump(data, f, indent=2)

def search_brave(query, count=10):
    """Search using Brave API"""
    api_key = os.getenv('BRAVE_API_KEY', '')
    if not api_key:
        return []
    
    try:
        url = "https://api.search.brave.com/res/v1/news/search"
        headers = {"X-Subscription-Token": api_key}
        params = {"q": query, "count": count, "freshness": "week"}
        
        response = requests.get(url, headers=headers, params=params, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            return data.get('results', [])
        else:
            log(f"  ⚠️ Brave API error: {response.status_code}")
            return []
    except Exception as e:
        log(f"  ⚠️ Search error: {e}")
        return []

def fetch_progyny_news():
    """Fetch news about Progyny"""
    log("🔍 Searching for Progyny news...")
    
    queries = [
        "Progyny PGNY news",
        "Progyny fertility benefits",
        "Progyny stock analysis",
        "Progyny employer reviews"
    ]
    
    all_results = []
    for query in queries[:2]:  # Limit to save API calls
        results = search_brave(query, count=5)
        for r in results:
            all_results.append({
                'title': r.get('title', ''),
                'url': r.get('url', ''),
                'description': r.get('description', '')[:300],
                'published': r.get('published', ''),
                'source': r.get('siteName', 'News'),
                'type': 'news'
            })
    
    log(f"   Found {len(all_results)} news items")
    return all_results

def fetch_progyny_reddit():
    """Fetch Reddit discussions about Progyny"""
    log("🔍 Searching Reddit for Progyny mentions...")
    
    subreddits = ['infertility', 'IVF', 'TTC', 'fertility', 'tryingforababy']
    all_posts = []
    
    for subreddit in subreddits:
        try:
            url = f"https://www.reddit.com/r/{subreddit}/search.json"
            headers = {'User-Agent': 'CompetitiveIntelligence/1.0'}
            params = {
                'q': 'progyny',
                'restrict_sr': '1',
                'sort': 'new',
                'limit': 10
            }
            
            response = requests.get(url, headers=headers, params=params, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                posts = data.get('data', {}).get('children', [])
                
                for post_data in posts:
                    post = post_data.get('data', {})
                    all_posts.append({
                        'title': post.get('title', ''),
                        'url': f"https://reddit.com{post.get('permalink', '')}",
                        'subreddit': subreddit,
                        'score': post.get('score', 0),
                        'num_comments': post.get('num_comments', 0),
                        'created_utc': post.get('created_utc', 0),
                        'type': 'reddit'
                    })
                    
        except Exception as e:
            log(f"  ⚠️ r/{subreddit}: {e}")
    
    log(f"   Found {len(all_posts)} Reddit posts")
    return all_posts

def fetch_executive_news():
    """Fetch news about Progyny executives"""
    log("🔍 Searching for Progyny executive news...")
    
    executives = [
        ("Pete Anevski", "CEO"),
        ("Geoffrey Clapp", "Chief Product Officer"),
        ("Janet Choi", "Chief Medical Officer"),
        ("Steven Leist", "Chief Technology Officer"),
        ("Melissa Cummings", "Chief Operating Officer"),
        ("Risa Fisher", "Chief Marketing Officer")
    ]
    
    all_results = []
    for name, title in executives:
        query = f'"{name}" Progyny'
        results = search_brave(query, count=3)
        
        for r in results:
            all_results.append({
                'executive': name,
                'title': title,
                'headline': r.get('title', ''),
                'url': r.get('url', ''),
                'description': r.get('description', '')[:300],
                'published': r.get('published', ''),
                'type': 'executive_news'
            })
    
    log(f"   Found {len(all_results)} executive news items")
    return all_results

def fetch_all_progyny_intel():
    """Fetch all Progyny market sentiment data"""
    existing = load_existing()
    
    log("="*60)
    log("PROGYNY MARKET SENTIMENT SCAN")
    log("="*60)
    
    # Fetch from all sources
    news = fetch_progyny_news()
    reddit = fetch_progyny_reddit()
    exec_news = fetch_executive_news()
    
    # Deduplicate by URL
    existing_urls = {m.get('url') for m in existing.get('mentions', [])}
    
    new_mentions = []
    for item in news + reddit:
        if item.get('url') not in existing_urls:
            item['found_at'] = datetime.now().isoformat()
            new_mentions.append(item)
    
    # Executive news is always tracked separately
    new_exec_news = []
    existing_exec_urls = {e.get('url') for e in existing.get('executive_news', [])}
    for item in exec_news:
        if item.get('url') not in existing_exec_urls:
            item['found_at'] = datetime.now().isoformat()
            new_exec_news.append(item)
    
    # Merge and keep recent (14 days)
    cutoff = datetime.now() - timedelta(days=14)
    
    all_mentions = existing.get('mentions', []) + new_mentions
    recent_mentions = []
    for m in all_mentions:
        try:
            if m.get('created_utc'):
                post_date = datetime.fromtimestamp(m['created_utc'])
            else:
                post_date = datetime.fromisoformat(m.get('found_at', '2000-01-01'))
            if post_date > cutoff:
                recent_mentions.append(m)
        except:
            recent_mentions.append(m)
    
    all_exec = existing.get('executive_news', []) + new_exec_news
    
    save_data({
        "mentions": recent_mentions,
        "executive_news": all_exec,
        "stats": {
            "total_mentions": len(recent_mentions),
            "new_mentions": len(new_mentions),
            "total_exec_news": len(all_exec),
            "new_exec_news": len(new_exec_news)
        }
    })
    
    log(f"\n✅ Progyny sentiment scan complete:")
    log(f"   Total mentions tracked: {len(recent_mentions)}")
    log(f"   New mentions: {len(new_mentions)}")
    log(f"   Executive news items: {len(all_exec)}")
    log(f"   New exec news: {len(new_exec_news)}")
    
    return {
        "mentions": recent_mentions,
        "executive_news": all_exec,
        "new_mentions": new_mentions,
        "new_exec_news": new_exec_news
    }

if __name__ == "__main__":
    import sys
    result = fetch_all_progyny_intel()
    sys.exit(0)
