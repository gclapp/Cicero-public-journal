#!/usr/bin/env python3
"""
Reddit scraper for competitive intelligence
Monitors IVF, fertility, and family building subreddits
"""

import os
import json
import requests
from datetime import datetime, timedelta
from pathlib import Path

OUTPUT_FILE = Path.home() / ".openclaw" / "workspace" / "config" / "reddit-competitive-intel.json"
LOG_FILE = Path.home() / ".openclaw" / "workspace" / "logs" / "reddit-scraper.log"

# Subreddits to monitor
SUBREDDITS = [
    'infertility',
    'IVF',
    'TTC',
    'pregnant',
    'babybumps',
    'fertility',
    'infertilitybabies',
    'whattoexpect',
    'tryingforababy',
    'Parenting',
    'NewParents'
]

# Keywords to track
KEYWORDS = {
    'Progyny': ['progyny', 'pgny'],
    'Maven': ['maven', 'maven clinic'],
    'Carrot': ['carrot', 'carrot fertility'],
    'KindBody': ['kindbody', 'kind body'],
    'WIN Fertility': ['win fertility', 'winfertility'],
    'Employer Benefits': ['employer benefit', 'fertility benefit', 'fertility coverage'],
    'Insurance': ['insurance coverage', 'covered by insurance']
}

def log(msg):
    """Log with timestamp"""
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{ts}] {msg}")
    with open(LOG_FILE, 'a') as f:
        f.write(f"[{ts}] {msg}\n")

def load_existing():
    """Load existing Reddit data"""
    if OUTPUT_FILE.exists():
        with open(OUTPUT_FILE) as f:
            return json.load(f)
    return {"posts": [], "last_updated": None}

def save_data(data):
    """Save Reddit data"""
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    data["last_updated"] = datetime.now().isoformat()
    with open(OUTPUT_FILE, 'w') as f:
        json.dump(data, f, indent=2)

def fetch_subreddit_posts(subreddit, limit=25):
    """Fetch recent posts from a subreddit"""
    try:
        url = f"https://www.reddit.com/r/{subreddit}/new.json"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json',
            'Accept-Language': 'en-US,en;q=0.9',
        }
        params = {'limit': limit}
        
        response = requests.get(url, headers=headers, params=params, timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            return data.get('data', {}).get('children', [])
        else:
            log(f"  ⚠️ r/{subreddit}: HTTP {response.status_code}")
            return []
            
    except Exception as e:
        log(f"  ⚠️ r/{subreddit}: {e}")
        return []

def analyze_post(post_data):
    """Analyze a post for competitive keywords"""
    post = post_data.get('data', {})
    
    title = post.get('title', '').lower()
    selftext = post.get('selftext', '').lower()
    combined = title + ' ' + selftext
    
    findings = []
    
    for category, keywords in KEYWORDS.items():
        for keyword in keywords:
            if keyword in combined:
                findings.append({
                    'category': category,
                    'keyword': keyword,
                    'context': title[:200]
                })
                break  # Only count once per category
    
    return findings

def fetch_all_reddit_intel():
    """Fetch competitive intelligence from Reddit"""
    existing = load_existing()
    existing_urls = {p.get('url') for p in existing.get('posts', [])}
    
    all_posts = []
    new_findings = []
    
    log(f"🔍 Scanning Reddit for competitive intel...")
    log(f"   Subreddits: {len(SUBREDDITS)}")
    
    for subreddit in SUBREDDITS:
        posts = fetch_subreddit_posts(subreddit, limit=25)
        log(f"   r/{subreddit}: {len(posts)} posts fetched")
        
        for post_data in posts:
            post = post_data.get('data', {})
            url = f"https://reddit.com{post.get('permalink', '')}"
            
            # Skip if already seen
            if url in existing_urls:
                continue
            
            # Analyze for keywords
            findings = analyze_post(post_data)
            
            if findings:
                post_info = {
                    'title': post.get('title', ''),
                    'url': url,
                    'subreddit': subreddit,
                    'author': post.get('author', ''),
                    'created_utc': post.get('created_utc', 0),
                    'score': post.get('score', 0),
                    'num_comments': post.get('num_comments', 0),
                    'findings': findings,
                    'found_at': datetime.now().isoformat()
                }
                all_posts.append(post_info)
                new_findings.append(post_info)
                log(f"      ✓ Found: {post.get('title', '')[:60]}... [{findings[0]['category']}]")
    
    # Merge with existing (keep last 14 days)
    cutoff = datetime.now() - timedelta(days=14)
    combined = existing.get('posts', []) + new_findings
    
    recent = []
    for post in combined:
        try:
            post_date = datetime.fromtimestamp(post.get('created_utc', 0))
            if post_date > cutoff:
                recent.append(post)
        except:
            recent.append(post)
    
    # Sort by date
    recent.sort(key=lambda x: x.get('created_utc', 0), reverse=True)
    
    save_data({"posts": recent})
    
    log(f"\n✅ Reddit scan complete:")
    log(f"   Total posts tracked: {len(recent)}")
    log(f"   New findings: {len(new_findings)}")
    
    return new_findings

if __name__ == "__main__":
    import sys
    findings = fetch_all_reddit_intel()
    sys.exit(0 if len(findings) >= 0 else 1)
