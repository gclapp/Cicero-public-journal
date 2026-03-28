#!/usr/bin/env python3
"""
Reddit Intelligence Collector for Competitive Analysis
Uses reddit-search-but-free skill with PullPush provider
"""

import subprocess
import json
from datetime import datetime
from pathlib import Path

OUTPUT_FILE = Path.home() / ".openclaw" / "workspace" / "config" / "reddit-intelligence.json"
SKILL_PATH = Path.home() / ".openclaw" / "workspace" / "skills" / "reddit-search-but-free" / "scripts"

def run_reddit_search(query, limit=10):
    """Run reddit search using the skill"""
    cmd = [
        "npx", "tsx", "reddit.ts", "search", query,
        "--provider", "pullpush",
        "--time", "month",
        "--limit", str(limit),
        "--json"
    ]
    
    try:
        result = subprocess.run(
            cmd,
            cwd=SKILL_PATH,
            capture_output=True,
            text=True,
            timeout=60
        )
        if result.returncode == 0:
            data = json.loads(result.stdout)
            return data.get("posts", [])
        return []
    except Exception as e:
        print(f"Error searching '{query}': {e}")
        return []

def collect_intelligence():
    """Collect Reddit intelligence on fertility benefits and competitors"""
    
    searches = {
        "Progyny": "Progyny fertility benefit",
        "Maven": "Maven Clinic fertility",
        "Carrot": "Carrot Fertility benefit",
        "Kindbody": "Kindbody fertility",
        "WIN": "WIN Fertility",
        "IVF insurance": "IVF insurance coverage",
        "fertility benefits": "fertility benefits employer"
    }
    
    all_results = {}
    
    for name, query in searches.items():
        print(f"🔍 Searching: {name}")
        results = run_reddit_search(query, limit=8)
        all_results[name] = results
        print(f"   Found {len(results)} posts")
    
    # Save results
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, 'w') as f:
        json.dump({
            "collected_at": datetime.now().isoformat(),
            "results": all_results
        }, f, indent=2)
    
    return all_results

def format_reddit_for_email():
    """Format Reddit data for competitive intelligence email"""
    if not OUTPUT_FILE.exists():
        collect_intelligence()
    
    with open(OUTPUT_FILE) as f:
        data = json.load(f)
    
    html = '<div class="section-title">💬 Reddit Intelligence</div>'
    html += '<p style="color: #666; font-size: 13px; margin-bottom: 20px;">Recent discussions from fertility communities (via PullPush)</p>'
    
    # Progyny mentions
    progyny_posts = data.get("results", {}).get("Progyny", [])
    if isinstance(progyny_posts, list) and progyny_posts:
        html += '<div style="margin-bottom: 20px;">'
        html += '<div style="font-weight: 600; color: #16a34a; margin-bottom: 10px;">📢 Progyny Mentions</div>'
        for post in progyny_posts[:3]:
            title = post.get('title', 'No title')[:80]
            subreddit = post.get('subreddit', 'unknown')
            url = post.get('url', '#')
            score = post.get('score', 0)
            html += f'''
            <div style="padding: 10px; background: #f0fdf4; border-radius: 6px; margin-bottom: 8px;">
                <div style="font-size: 13px; font-weight: 500;"><a href="{url}">{title}...</a></div>
                <div style="font-size: 11px; color: #666;">r/{subreddit} • ⬆️ {score}</div>
            </div>
            '''
        html += '</div>'
    
    # Competitor mentions
    competitors = ["Maven", "Carrot", "Kindbody"]
    for comp in competitors:
        posts = data.get("results", {}).get(comp, [])
        if isinstance(posts, list) and posts:
            html += f'<div style="margin-bottom: 20px;">'
            html += f'<div style="font-weight: 600; color: #ea580c; margin-bottom: 10px;">🔍 {comp} Mentions</div>'
            for post in posts[:2]:
                title = post.get('title', 'No title')[:80]
                subreddit = post.get('subreddit', 'unknown')
                url = post.get('url', '#')
                score = post.get('score', 0)
                html += f'''
                <div style="padding: 10px; background: #fff7ed; border-radius: 6px; margin-bottom: 8px;">
                    <div style="font-size: 13px; font-weight: 500;"><a href="{url}">{title}...</a></div>
                    <div style="font-size: 11px; color: #666;">r/{subreddit} • ⬆️ {score}</div>
                </div>
                '''
            html += '</div>'
    
    # General sentiment
    ivf_posts = data.get("results", {}).get("IVF insurance", [])
    benefit_posts = data.get("results", {}).get("fertility benefits", [])
    general_posts = []
    if isinstance(ivf_posts, list):
        general_posts.extend(ivf_posts)
    if isinstance(benefit_posts, list):
        general_posts.extend(benefit_posts)
    
    if general_posts:
        html += '<div style="margin-bottom: 20px;">'
        html += '<div style="font-weight: 600; color: #1e40af; margin-bottom: 10px;">📊 Market Sentiment</div>'
        html += '<ul style="font-size: 13px; line-height: 1.6;">'
        
        # Extract key themes
        themes = []
        for post in general_posts[:5]:
            title = post.get('title', '')
            if 'insurance' in title.lower():
                themes.append("Insurance coverage questions prevalent")
            if 'coverage' in title.lower():
                themes.append("Patients actively researching benefit options")
            if 'employer' in title.lower():
                themes.append("Employer-sponsored benefits being discussed")
        
        if themes:
            for theme in set(themes[:3]):
                html += f'<li>{theme}</li>'
        else:
            html += '<li>Active discussions around IVF coverage and benefits</li>'
        
        html += '</ul></div>'
    
    return html

if __name__ == "__main__":
    collect_intelligence()
    print(format_reddit_for_email())
