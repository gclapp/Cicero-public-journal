#!/usr/bin/env python3
"""
LinkedIn Executive Monitor - Alternative approach
Uses company page RSS and web alerts to track executive activity
"""

import json
import subprocess
from pathlib import Path
from datetime import datetime, timedelta

CONFIG_PATH = Path.home() / ".openclaw" / "workspace" / "config" / "competitive-intelligence-config.json"
OUTPUT_PATH = Path.home() / ".openclaw" / "workspace" / "config" / "linkedin-executive-posts.json"

def load_config():
    """Load competitor configuration"""
    if CONFIG_PATH.exists():
        with open(CONFIG_PATH) as f:
            return json.load(f)
    return {}

def load_existing():
    """Load existing posts"""
    if OUTPUT_PATH.exists():
        with open(OUTPUT_PATH) as f:
            return json.load(f)
    return {"posts": [], "last_updated": None}

def save_data(data):
    """Save posts"""
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    data["last_updated"] = datetime.now().isoformat()
    with open(OUTPUT_PATH, 'w') as f:
        json.dump(data, f, indent=2)

def search_exec_posts_brave(name, company):
    """Search for executive posts using Brave API"""
    try:
        result = subprocess.run(
            ['python3', '-c', f'''
import os
import requests
import json
from datetime import datetime

api_key = os.getenv("BRAVE_API_KEY")
if not api_key:
    print(json.dumps({{"error": "No API key"}}))
    exit(1)

# Search for posts by this executive
queries = [
    f"{name} {company} LinkedIn post",
    f"{name} {company} LinkedIn update",
    f"{name} CEO {company} LinkedIn"
]

all_results = []
for query in queries[:1]:  # Just first query to save API calls
    url = "https://api.search.brave.com/res/v1/news/search"
    headers = {{"X-Subscription-Token": api_key}}
    params = {{"q": query, "count": 3, "freshness": "week"}}
    
    try:
        resp = requests.get(url, headers=headers, params=params, timeout=15)
        data = resp.json()
        
        for item in data.get("results", []):
            # Only include LinkedIn URLs
            url = item.get("url", "")
            if "linkedin.com" in url or "linkedin" in item.get("title", "").lower():
                all_results.append({{
                    "title": item.get("title", ""),
                    "url": url,
                    "description": item.get("description", "")[:400],
                    "published": item.get("published", datetime.now().isoformat())
                }})
    except Exception as e:
        continue

print(json.dumps({{"success": True, "posts": all_results}}))
            '''],
            capture_output=True, text=True, timeout=30
        )
        
        if result.returncode == 0 and result.stdout:
            try:
                lines = result.stdout.strip().split('\n')
                for line in reversed(lines):
                    if line.strip().startswith('{'):
                        return json.loads(line)
            except:
                pass
        
        return {"success": False, "posts": []}
        
    except Exception as e:
        return {"success": False, "error": str(e), "posts": []}

def fetch_all_posts():
    """Fetch posts for all executives"""
    config = load_config()
    existing = load_existing()
    
    companies = config.get('linkedin_companies', {})
    all_posts = []
    
    print("🔍 Scanning for LinkedIn executive activity...")
    print(f"   Companies: {len(companies)}")
    
    # Priority executives (CEOs and key leaders)
    priority_execs = [
        ("Maven", "Kate Ryder"),
        ("Carrot", "Tammy Sun"),
        ("KindBody", "Gina Bartasi"),
        ("Pomelo Health", "Marta Bralic Kerns"),
        ("Midi Health", "Joanna Strober"),
        ("Evernow", "Alicia Jackson"),
    ]
    
    for company, exec_name in priority_execs:
        print(f"   Checking {exec_name} ({company})...")
        
        result = search_exec_posts_brave(exec_name, company)
        
        if result.get('success') and result.get('posts'):
            for post in result['posts']:
                post_data = {
                    "executive": exec_name,
                    "company": company,
                    "title": post.get('title', ''),
                    "url": post.get('url', ''),
                    "description": post.get('description', ''),
                    "found_at": datetime.now().isoformat(),
                    "source": "linkedin_search"
                }
                all_posts.append(post_data)
                print(f"      ✓ Found: {post.get('title', '')[:60]}...")
        else:
            print(f"      - No recent posts")
    
    # Merge with existing
    existing_urls = {p.get('url') for p in existing.get('posts', [])}
    new_posts = [p for p in all_posts if p.get('url') not in existing_urls]
    
    # Keep only last 14 days
    cutoff = datetime.now() - timedelta(days=14)
    combined = existing.get('posts', []) + new_posts
    
    recent = []
    for post in combined:
        try:
            post_date = datetime.fromisoformat(post.get('found_at', '2000-01-01'))
            if post_date > cutoff:
                recent.append(post)
        except:
            recent.append(post)
    
    save_data({"posts": recent})
    
    print(f"\n✅ LinkedIn scan complete:")
    print(f"   Total posts tracked: {len(recent)}")
    print(f"   New posts found: {len(new_posts)}")
    
    return len(new_posts)

if __name__ == "__main__":
    import sys
    count = fetch_all_posts()
    sys.exit(0 if count >= 0 else 1)
