#!/usr/bin/env python3
"""
LinkedIn Executive Monitoring
Tracks executive team changes, job moves, and company posts
Uses web search and public LinkedIn data
"""

import json
import hashlib
from datetime import datetime
from pathlib import Path
import requests
import os

SEEN_FILE = Path.home() / ".openclaw" / "workspace" / "config" / "competitor-seen-v2.json"
OUTPUT_FILE = Path.home() / ".openclaw" / "workspace" / "config" / "linkedin-updates.json"

def load_config():
    """Load competitive intelligence config"""
    config_file = Path.home() / ".openclaw" / "workspace" / "config" / "competitive-intelligence-config.json"
    with open(config_file) as f:
        return json.load(f)

def load_seen():
    """Load seen updates"""
    if SEEN_FILE.exists():
        with open(SEEN_FILE) as f:
            return json.load(f)
    return {"linkedin_posts": {}, "job_changes": {}, "exec_moves": {}}

def save_seen(seen):
    """Save seen updates"""
    with open(SEEN_FILE, 'w') as f:
        json.dump(seen, f, indent=2)

def search_exec_news(company, exec_team):
    """Search for news about executive team"""
    updates = []
    api_key = os.getenv('BRAVE_API_KEY', '')
    
    if not api_key:
        return updates
    
    for exec_name in exec_team:
        try:
            query = f'"{exec_name}" "{company}" LinkedIn OR hired OR appointed OR joined OR left'
            url = "https://api.search.brave.com/res/v1/web/search"
            headers = {"X-Subscription-Token": api_key}
            params = {"q": query, "count": 3, "freshness": "week"}
            
            response = requests.get(url, headers=headers, params=params, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                for item in data.get('web', {}).get('results', []):
                    # Check if it's about this exec
                    if exec_name.lower() in item.get('title', '').lower() or \
                       exec_name.lower() in item.get('description', '').lower():
                        
                        update_id = hashlib.md5(f"{exec_name}:{item.get('url')}".encode()).hexdigest()
                        
                        updates.append({
                            'id': update_id,
                            'type': 'exec_news',
                            'company': company,
                            'executive': exec_name,
                            'title': item.get('title'),
                            'link': item.get('url'),
                            'description': item.get('description', '')[:300],
                            'found_at': datetime.now().isoformat()
                        })
                        
        except Exception as e:
            print(f"Error searching for {exec_name}: {e}")
    
    return updates

def search_job_changes():
    """Search for executive job changes in fertility industry"""
    updates = []
    api_key = os.getenv('BRAVE_API_KEY', '')
    
    if not api_key:
        return updates
    
    queries = [
        "Maven Clinic executive hired OR appointed OR joined",
        "Carrot Fertility executive hired OR appointed OR joined", 
        "KindBody executive hired OR appointed OR joined",
        "WIN Fertility executive hired OR appointed OR joined",
        "fertility benefits executive job change 2026"
    ]
    
    for query in queries:
        try:
            url = "https://api.search.brave.com/res/v1/news/search"
            headers = {"X-Subscription-Token": api_key}
            params = {"q": query, "count": 5, "freshness": "week"}
            
            response = requests.get(url, headers=headers, params=params, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                for item in data.get('results', []):
                    update_id = hashlib.md5(item.get('url', '').encode()).hexdigest()
                    
                    # Determine company from content
                    title_lower = item.get('title', '').lower()
                    company = 'industry'
                    if 'maven' in title_lower:
                        company = 'Maven'
                    elif 'carrot' in title_lower:
                        company = 'Carrot'
                    elif 'kindbody' in title_lower:
                        company = 'KindBody'
                    elif 'win fertility' in title_lower or 'winfertility' in title_lower:
                        company = 'WIN Fertility'
                    
                    updates.append({
                        'id': update_id,
                        'type': 'job_change',
                        'company': company,
                        'title': item.get('title'),
                        'link': item.get('url'),
                        'description': item.get('description', '')[:300],
                        'published': item.get('published', ''),
                        'found_at': datetime.now().isoformat()
                    })
                    
        except Exception as e:
            print(f"Error searching job changes: {e}")
    
    return updates

def search_company_posts():
    """Search for company announcements/posts"""
    updates = []
    api_key = os.getenv('BRAVE_API_KEY', '')
    
    if not api_key:
        return updates
    
    companies = ['Maven Clinic', 'Carrot Fertility', 'KindBody', 'WIN Fertility']
    
    for company in companies:
        try:
            query = f'"{company}" announcement OR launch OR partnership OR milestone site:linkedin.com OR site:twitter.com OR site:x.com'
            url = "https://api.search.brave.com/res/v1/news/search"
            headers = {"X-Subscription-Token": api_key}
            params = {"q": query, "count": 3, "freshness": "day"}
            
            response = requests.get(url, headers=headers, params=params, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                for item in data.get('results', []):
                    update_id = hashlib.md5(item.get('url', '').encode()).hexdigest()
                    
                    updates.append({
                        'id': update_id,
                        'type': 'company_post',
                        'company': company,
                        'title': item.get('title'),
                        'link': item.get('url'),
                        'description': item.get('description', '')[:300],
                        'published': item.get('published', ''),
                        'found_at': datetime.now().isoformat()
                    })
                    
        except Exception as e:
            print(f"Error searching company posts for {company}: {e}")
    
    return updates

def main():
    """Run LinkedIn/exec monitoring"""
    print("=" * 70)
    print("LinkedIn Executive & Job Change Monitoring")
    print("=" * 70)
    
    config = load_config()
    seen = load_seen()
    all_updates = []
    
    # 1. Search for executive news
    print("\n1. Searching for executive team updates...")
    linkedin_companies = config.get('linkedin_companies', {})
    for company, data in linkedin_companies.items():
        if company == 'Progyny':  # Skip our own company
            continue
        exec_team = data.get('exec_team', [])
        updates = search_exec_news(company, exec_team)
        for update in updates:
            if update['id'] not in seen.get('linkedin_posts', {}):
                all_updates.append(update)
                seen['linkedin_posts'][update['id']] = {'found_at': datetime.now().isoformat()}
        print(f"   {company}: {len(updates)} updates")
    
    # 2. Search for job changes
    print("\n2. Searching for executive job changes...")
    job_changes = search_job_changes()
    for change in job_changes:
        if change['id'] not in seen.get('job_changes', {}):
            all_updates.append(change)
            seen['job_changes'][change['id']] = {'found_at': datetime.now().isoformat()}
    print(f"   Found {len(job_changes)} job changes")
    
    # 3. Search for company posts/announcements
    print("\n3. Searching for company announcements...")
    company_posts = search_company_posts()
    for post in company_posts:
        if post['id'] not in seen.get('linkedin_posts', {}):
            all_updates.append(post)
            seen['linkedin_posts'][post['id']] = {'found_at': datetime.now().isoformat()}
    print(f"   Found {len(company_posts)} company posts")
    
    # Save updates
    save_seen(seen)
    
    if all_updates:
        OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(OUTPUT_FILE, 'w') as f:
            json.dump(all_updates, f, indent=2)
        
        print(f"\n✅ Found {len(all_updates)} new LinkedIn/exec updates")
        print(f"   Saved to: {OUTPUT_FILE}")
        
        # Print summary
        job_changes_count = len([u for u in all_updates if u['type'] == 'job_change'])
        exec_news_count = len([u for u in all_updates if u['type'] == 'exec_news'])
        posts_count = len([u for u in all_updates if u['type'] == 'company_post'])
        
        print(f"\n   Job Changes: {job_changes_count}")
        print(f"   Executive News: {exec_news_count}")
        print(f"   Company Posts: {posts_count}")
        
        return len(all_updates)
    else:
        print("\n✅ No new LinkedIn/exec updates found")
        return 0

if __name__ == "__main__":
    import sys
    count = main()
    sys.exit(0 if count >= 0 else 1)
