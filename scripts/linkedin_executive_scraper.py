#!/usr/bin/env python3
"""
LinkedIn Executive Post Scraper
Uses Scrapling to bypass anti-bot protection and fetch executive posts
"""

import json
import sys
import subprocess
from pathlib import Path
from datetime import datetime, timedelta

# Add workspace to path
sys.path.insert(0, '/home/ubuntu/.openclaw/workspace')

CONFIG_PATH = Path.home() / ".openclaw" / "workspace" / "config" / "competitive-intelligence-config.json"
OUTPUT_PATH = Path.home() / ".openclaw" / "workspace" / "config" / "linkedin-executive-posts.json"

def load_config():
    """Load competitor configuration"""
    if CONFIG_PATH.exists():
        with open(CONFIG_PATH) as f:
            return json.load(f)
    return {}

def load_existing_posts():
    """Load existing posts to avoid duplicates"""
    if OUTPUT_PATH.exists():
        with open(OUTPUT_PATH) as f:
            return json.load(f)
    return {"posts": [], "last_updated": None}

def save_posts(data):
    """Save posts to JSON"""
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    data["last_updated"] = datetime.now().isoformat()
    with open(OUTPUT_PATH, 'w') as f:
        json.dump(data, f, indent=2)

def get_executive_profile_url(name, company):
    """Generate likely LinkedIn profile URL from name"""
    # Convert name to LinkedIn slug format
    name_slug = name.lower().replace(' ', '-')
    return f"https://www.linkedin.com/in/{name_slug}"

def scrape_linkedin_profile(name, company):
    """
    Scrape LinkedIn profile for recent posts using Scrapling
    """
    profile_url = get_executive_profile_url(name, company)
    
    scrapling_script = f'''
import asyncio
import json
from scrapling import StealthFetcher

async def scrape_profile():
    fetcher = StealthFetcher()
    try:
        # Fetch the profile page
        page = await fetcher.async_fetch("{profile_url}", headless=True)
        
        # Wait for content to load
        await page.wait_for_selector("main", timeout=10000)
        
        posts = []
        
        # Try to find posts section
        post_elements = await page.query_selector_all("[data-test-id='feed-component'] .update-components-text")
        
        for elem in post_elements[:5]:  # Get last 5 posts
            try:
                text = await elem.inner_text()
                if text and len(text) > 20:
                    posts.append({{
                        "text": text[:500],
                        "timestamp": "recent"
                    }})
            except:
                continue
        
        print(json.dumps({{"success": True, "posts": posts, "profile": "{profile_url}"}}))
        
    except Exception as e:
        print(json.dumps({{"success": False, "error": str(e)}}))
    finally:
        await page.close()

asyncio.run(scrape_profile())
'''
    
    try:
        # Run scrapling in the scrapling venv
        result = subprocess.run(
            ['bash', '-c', f'source ~/.openclaw/venvs/scrapling/bin/activate && python3 -c "{scrapling_script}"'],
            capture_output=True, text=True, timeout=60
        )
        
        if result.returncode == 0 and result.stdout:
            try:
                return json.loads(result.stdout.strip().split('\n')[-1])
            except:
                return {"success": False, "error": "JSON parse failed"}
        
        return {"success": False, "error": result.stderr or "No output"}
        
    except Exception as e:
        return {"success": False, "error": str(e)}

def search_linkedin_posts(name, company):
    """
    Alternative: Search for executive posts via web search
    More reliable than scraping LinkedIn directly
    """
    search_query = f"{name} {company} LinkedIn post site:linkedin.com"
    
    try:
        result = subprocess.run(
            ['python3', '-c', f'''
import os
import requests
import json

api_key = os.getenv("BRAVE_API_KEY")
if not api_key:
    print(json.dumps({{"success": False, "error": "No API key"}}))
    exit(1)

url = "https://api.search.brave.com/res/v1/web/search"
headers = {{"X-Subscription-Token": api_key}}
params = {{"q": "{search_query}", "count": 5, "freshness": "week"}}

resp = requests.get(url, headers=headers, params=params, timeout=15)
results = []

for item in resp.json().get("results", []):
    results.append({{
        "title": item.get("title", ""),
        "url": item.get("url", ""),
        "description": item.get("description", "")[:300]
    }})

print(json.dumps({{"success": True, "posts": results}}))
            '''],
            capture_output=True, text=True, timeout=20
        )
        
        if result.returncode == 0 and result.stdout:
            return json.loads(result.stdout.strip().split('\n')[-1])
        
        return {"success": False, "error": "Search failed"}
        
    except Exception as e:
        return {"success": False, "error": str(e)}

def fetch_all_executive_posts():
    """Fetch posts for all tracked executives"""
    config = load_config()
    existing = load_existing_posts()
    
    companies = config.get('linkedin_companies', {})
    all_posts = []
    
    print("🔍 Fetching LinkedIn executive posts...")
    print(f"   Companies to check: {len(companies)}")
    
    for company_name, company_data in companies.items():
        exec_team = company_data.get('exec_team', [])
        
        for exec_name in exec_team[:3]:  # Top 3 execs per company
            print(f"   Checking {exec_name} ({company_name})...")
            
            # Try web search first (more reliable)
            result = search_linkedin_posts(exec_name, company_name)
            
            if result.get('success') and result.get('posts'):
                for post in result['posts']:
                    post_data = {
                        "executive": exec_name,
                        "company": company_name,
                        "title": post.get('title', ''),
                        "url": post.get('url', ''),
                        "description": post.get('description', ''),
                        "found_at": datetime.now().isoformat(),
                        "source": "linkedin_search"
                    }
                    all_posts.append(post_data)
                    print(f"      ✓ Found: {post.get('title', 'No title')[:50]}...")
            else:
                print(f"      ⚠ No posts found")
    
    # Merge with existing, deduplicate by URL
    existing_urls = {p.get('url') for p in existing.get('posts', [])}
    new_posts = [p for p in all_posts if p.get('url') not in existing_urls]
    
    # Keep only last 30 days of posts
    cutoff = datetime.now() - timedelta(days=30)
    all_posts_combined = existing.get('posts', []) + new_posts
    
    recent_posts = []
    for post in all_posts_combined:
        try:
            post_date = datetime.fromisoformat(post.get('found_at', '2000-01-01'))
            if post_date > cutoff:
                recent_posts.append(post)
        except:
            recent_posts.append(post)  # Keep if date parsing fails
    
    # Save updated data
    save_posts({"posts": recent_posts})
    
    print(f"\n✅ LinkedIn fetch complete:")
    print(f"   Total posts: {len(recent_posts)}")
    print(f"   New posts: {len(new_posts)}")
    
    return len(new_posts)

if __name__ == "__main__":
    count = fetch_all_executive_posts()
    sys.exit(0 if count >= 0 else 1)
