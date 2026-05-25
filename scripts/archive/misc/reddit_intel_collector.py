#!/usr/bin/env python3
"""
Reddit Intelligence Collector for Competitive Analysis
Monitors 10 subreddits for Progyny, competitor, and industry discussions
"""

import subprocess
import json
from datetime import datetime
from pathlib import Path

OUTPUT_FILE = Path.home() / ".openclaw" / "workspace" / "config" / "reddit-intelligence.json"
SKILL_PATH = Path.home() / ".openclaw" / "workspace" / "skills" / "reddit-search-but-free" / "scripts"

# Expanded search strategy
SEARCHES = {
    # Primary: Progyny (exact match)
    "Progyny": {
        "queries": ["Progyny"],
        "priority": "CRITICAL",
        "note": "Exact brand mentions"
    },
    
    # Competitors: Full names to avoid generic matches
    "Maven Clinic": {
        "queries": ["Maven Clinic", "Maven fertility"],
        "priority": "HIGH",
        "note": "Maven Clinic specifically"
    },
    
    "Carrot Fertility": {
        "queries": ["Carrot Fertility", "Carrot benefit"],
        "priority": "HIGH", 
        "note": "Carrot Fertility specifically"
    },
    
    "Kindbody": {
        "queries": ["Kindbody"],
        "priority": "HIGH",
        "note": "Exact brand mentions"
    },
    
    "WIN Fertility": {
        "queries": ["WIN Fertility"],
        "priority": "MEDIUM",
        "note": "Exact brand mentions"
    },
    
    # Industry: Broader discussions
    "IVF Insurance": {
        "queries": ["IVF insurance", "IVF coverage"],
        "priority": "HIGH",
        "note": "Insurance coverage discussions"
    },
    
    "Fertility Benefits": {
        "queries": ["fertility benefits", "fertility coverage"],
        "priority": "HIGH",
        "note": "Benefit discussions"
    },
    
    "Employer Benefits": {
        "queries": ["employer fertility", "company fertility benefit"],
        "priority": "MEDIUM",
        "note": "Employer-sponsored discussions"
    },
    
    "Egg Freezing": {
        "queries": ["egg freezing insurance", "egg freezing cost"],
        "priority": "MEDIUM",
        "note": "Egg freezing discussions"
    },
    
    "Menopause Benefits": {
        "queries": ["menopause benefits", "menopause coverage"],
        "priority": "HIGH",
        "note": "Menopause care discussions - CRITICAL"
    }
}

def run_reddit_search(query, limit=15):
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
            timeout=90
        )
        if result.returncode == 0:
            data = json.loads(result.stdout)
            return data.get("posts", [])
        return []
    except Exception as e:
        print(f"Error searching '{query}': {e}")
        return []

def collect_intelligence():
    """Collect comprehensive Reddit intelligence"""
    
    all_results = {}
    total_posts = 0
    
    print("=" * 60)
    print("REDDIT INTELLIGENCE COLLECTION")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    for category, config in SEARCHES.items():
        print(f"\n🔍 {category} ({config['priority']})")
        print(f"   Note: {config['note']}")
        
        category_posts = []
        for query in config['queries']:
            print(f"   Query: '{query}'")
            results = run_reddit_search(query, limit=10)
            
            # Add metadata to each post
            for post in results:
                post['_intel_category'] = category
                post['_intel_priority'] = config['priority']
                post['_search_query'] = query
            
            category_posts.extend(results)
        
        # Deduplicate by URL
        seen_urls = set()
        unique_posts = []
        for post in category_posts:
            url = post.get('url', '')
            if url and url not in seen_urls:
                seen_urls.add(url)
                unique_posts.append(post)
        
        all_results[category] = unique_posts
        total_posts += len(unique_posts)
        print(f"   ✓ Found {len(unique_posts)} unique posts")
    
    # Save results
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, 'w') as f:
        json.dump({
            "collected_at": datetime.now().isoformat(),
            "total_posts": total_posts,
            "categories_searched": len(SEARCHES),
            "results": all_results
        }, f, indent=2)
    
    print("\n" + "=" * 60)
    print(f"✅ Collection complete: {total_posts} total posts")
    print(f"💾 Saved to: {OUTPUT_FILE}")
    print("=" * 60)
    
    return all_results

def format_for_email():
    """Format Reddit data for competitive intelligence email"""
    if not OUTPUT_FILE.exists():
        collect_intelligence()
    
    with open(OUTPUT_FILE) as f:
        data = json.load(f)
    
    html = '<div class="section-title">💬 Reddit Intelligence</div>'
    html += '<p style="color: #9ca3af; font-size: 13px; margin-bottom: 20px;">Patient and community discussions from 10 subreddits</p>'
    
    # Progyny mentions (CRITICAL)
    progyny_posts = data.get("results", {}).get("Progyny", [])
    if progyny_posts:
        html += '<div style="margin-bottom: 25px; padding: 15px; background: #064e3b; border-radius: 8px; border-left: 4px solid #16a34a;">'
        html += '<div style="font-weight: 600; color: #16a34a; margin-bottom: 12px; font-size: 16px;">📢 PROGYNY MENTIONS</div>'
        for post in progyny_posts[:5]:
            title = post.get('title', 'No title')[:100]
            subreddit = post.get('subreddit', 'unknown')
            url = post.get('url', '#')
            score = post.get('score', 0)
            comments = post.get('num_comments', 0)
            html += f'''
            <div style="padding: 12px; background: #065f46; border-radius: 6px; margin-bottom: 10px;">
                <div style="font-size: 14px; font-weight: 500; margin-bottom: 6px;"><a href="{url}" style="color: #6ee7b7; text-decoration: none;">{title}...</a></div>
                <div style="font-size: 12px; color: #9ca3af;">r/{subreddit} • ⬆️ {score} • 💬 {comments} comments</div>
            </div>
            '''
        html += '</div>'
    
    # Competitor mentions
    competitors = ["Maven Clinic", "Carrot Fertility", "Kindbody", "WIN Fertility"]
    comp_posts = []
    for comp in competitors:
        posts = data.get("results", {}).get(comp, [])
        if posts:
            comp_posts.append((comp, posts))
    
    if comp_posts:
        html += '<div style="margin-bottom: 25px;">'
        html += '<div style="font-weight: 600; color: #ea580c; margin-bottom: 12px; font-size: 16px;">🔍 COMPETITOR MENTIONS</div>'
        
        for comp_name, posts in comp_posts:
            html += f'<div style="margin-bottom: 15px; padding: 12px; background: #1f1f1f; border-radius: 6px;">'
            html += f'<div style="font-weight: 600; color: #fb923c; margin-bottom: 8px;">{comp_name}</div>'
            for post in posts[:2]:
                title = post.get('title', 'No title')[:90]
                subreddit = post.get('subreddit', 'unknown')
                url = post.get('url', '#')
                score = post.get('score', 0)
                html += f'''
                <div style="padding: 8px; background: #262626; border-radius: 4px; margin-bottom: 6px;">
                    <div style="font-size: 13px;"><a href="{url}" style="color: #e5e5e5; text-decoration: none;">{title}...</a></div>
                    <div style="font-size: 11px; color: #737373;">r/{subreddit} • ⬆️ {score}</div>
                </div>
                '''
            html += '</div>'
        html += '</div>'
    
    # Industry trends / sentiment
    industry_categories = ["IVF Insurance", "Fertility Benefits", "Menopause Benefits", "Employer Benefits"]
    industry_posts = []
    for cat in industry_categories:
        posts = data.get("results", {}).get(cat, [])
        if posts:
            industry_posts.extend(posts[:2])  # Top 2 from each
    
    if industry_posts:
        html += '<div style="margin-bottom: 20px;">'
        html += '<div style="font-weight: 600; color: #3b82f6; margin-bottom: 12px; font-size: 16px;">📊 MARKET SENTIMENT & TRENDS</div>'
        html += '<div style="padding: 15px; background: #172554; border-radius: 8px;">'
        
        # Extract key themes
        themes = {
            "insurance_coverage": 0,
            "employer_sponsored": 0,
            "cost_concerns": 0,
            "menopause_interest": 0
        }
        
        for post in industry_posts:
            title = post.get('title', '').lower()
            if any(word in title for word in ['insurance', 'coverage', 'covered']):
                themes["insurance_coverage"] += 1
            if any(word in title for word in ['employer', 'company', 'work', 'job']):
                themes["employer_sponsored"] += 1
            if any(word in title for word in ['cost', 'expensive', 'price', 'pay']):
                themes["cost_concerns"] += 1
            if any(word in title for word in ['menopause', 'perimenopause']):
                themes["menopause_interest"] += 1
        
        # Show themes as insights
        html += '<ul style="font-size: 13px; line-height: 1.8; color: #bfdbfe; margin: 0; padding-left: 20px;">'
        if themes["insurance_coverage"] > 0:
            html += f'<li><strong>Insurance questions prevalent:</strong> {themes["insurance_coverage"]} discussions about coverage</li>'
        if themes["employer_sponsored"] > 0:
            html += f'<li><strong>Employer benefits active:</strong> {themes["employer_sponsored"]} posts about workplace benefits</li>'
        if themes["cost_concerns"] > 0:
            html += f'<li><strong>Cost concerns ongoing:</strong> {themes["cost_concerns"]} discussions about pricing</li>'
        if themes["menopause_interest"] > 0:
            html += f'<li><strong>Menopause interest rising:</strong> {themes["menopause_interest"]} discussions</li>'
        html += '</ul>'
        html += '</div>'
        html += '</div>'
    
    # Summary stats
    total_posts = data.get("total_posts", 0)
    html += f'<div style="font-size: 12px; color: #737373; text-align: center; padding-top: 10px; border-top: 1px solid #262626;">'
    html += f'Monitored: r/infertility, r/IVF, r/TTC, r/Menopause, r/tryingtoconceive, r/pregnant, r/BabyBumps, r/Parenting, r/womenshealth, r/HealthInsurance<br>'
    html += f'Total posts analyzed: {total_posts} • Last updated: {datetime.now().strftime("%Y-%m-%d %H:%M")}'
    html += '</div>'
    
    return html

if __name__ == "__main__":
    collect_intelligence()
    print("\n" + "=" * 60)
    print("EMAIL FORMAT PREVIEW:")
    print("=" * 60)
    print(format_for_email()[:2000] + "...")
