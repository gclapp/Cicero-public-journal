#!/usr/bin/env python3
"""
Enhanced Competitive Intelligence System
- RSS feeds (Google Alerts + industry news)
- Web search (real-time news)
- LinkedIn company monitoring (exec posts, job changes)
- Job board scraping (hiring signals)
- Deduplication and stale content detection
"""

import os
import json
import hashlib
import feedparser
import requests
from datetime import datetime, timedelta
from pathlib import Path

# Paths
CONFIG_FILE = Path.home() / ".openclaw" / "workspace" / "config" / "competitive-intelligence-config.json"
SEEN_FILE = Path.home() / ".openclaw" / "workspace" / "config" / "competitor-seen-v2.json"
SENT_COUNT_FILE = Path.home() / ".openclaw" / "workspace" / "config" / "competitor-sent-count-v2.json"
ARTICLES_FILE = Path.home() / ".openclaw" / "workspace" / "config" / "competitor-articles-v2.json"
LOG_FILE = Path.home() / ".openclaw" / "workspace" / "logs" / "competitor-v2.log"

def log(msg):
    """Log with timestamp"""
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{ts}] {msg}")
    with open(LOG_FILE, 'a') as f:
        f.write(f"[{ts}] {msg}\n")

def load_config():
    """Load competitive intelligence configuration"""
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE) as f:
            return json.load(f)
    return {}

def load_seen():
    """Load seen article IDs with timestamps"""
    if SEEN_FILE.exists():
        with open(SEEN_FILE) as f:
            return json.load(f)
    return {"articles": {}, "linkedin_posts": {}, "job_changes": {}}

def save_seen(seen):
    """Save seen article IDs"""
    SEEN_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(SEEN_FILE, 'w') as f:
        json.dump(seen, f, indent=2)

def load_sent_counts():
    """Load article send counts (tracks how many times each article was sent) - ported from v1"""
    if SENT_COUNT_FILE.exists():
        with open(SENT_COUNT_FILE) as f:
            return json.load(f)
    return {}

def save_sent_counts(counts):
    """Save article send counts"""
    SENT_COUNT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(SENT_COUNT_FILE, 'w') as f:
        json.dump(counts, f, indent=2)

def can_send_article(article_id, sent_counts):
    """Check if article can be sent (max 2 times) - ported from v1"""
    count = sent_counts.get(article_id, 0)
    return count < 2

def increment_sent_count(article_id, sent_counts):
    """Increment the send count for an article"""
    sent_counts[article_id] = sent_counts.get(article_id, 0) + 1
    save_sent_counts(sent_counts)

def article_id(entry):
    """Generate unique ID for article"""
    content = f"{entry.get('link', '')}:{entry.get('title', '')}"
    return hashlib.md5(content.encode()).hexdigest()

def is_stale_article(published_str, max_age_days=30):
    """Check if article is too old to report (default: 30 days)"""
    try:
        # Try various date formats
        for fmt in ["%a, %d %b %Y %H:%M:%S %Z", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d"]:
            try:
                pub_date = datetime.strptime(published_str[:len(fmt)+10], fmt)
                age = datetime.now() - pub_date
                return age.days > max_age_days
            except:
                continue
    except:
        pass
    return False  # If we can't parse, assume it's fresh

def scan_rss_feeds(config):
    """Scan RSS feeds for new articles"""
    seen = load_seen()
    new_articles = []
    feeds = config.get('rss_feeds', {})
    
    for name, url in feeds.items():
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries:
                aid = article_id(entry)
                
                # Skip if already seen
                if aid in seen['articles']:
                    continue
                
                published = entry.get('published', entry.get('updated', ''))
                
                # Skip stale articles (>7 days old)
                if is_stale_article(published):
                    continue
                
                article = {
                    'id': aid,
                    'title': entry.get('title', 'No title'),
                    'link': entry.get('link', ''),
                    'published': published,
                    'summary': entry.get('summary', '')[:500],
                    'source': name,
                    'type': 'news',
                    'found_at': datetime.now().isoformat()
                }
                
                new_articles.append(article)
                seen['articles'][aid] = {'found_at': datetime.now().isoformat(), 'sent': False}
                
        except Exception as e:
            log(f"Error scanning {name}: {e}")
    
    save_seen(seen)
    return new_articles

def search_web_for_news(config):
    """Search web for real-time competitive news"""
    queries = config.get('web_search_queries', [])
    new_articles = []
    seen = load_seen()
    
    # Use Brave Search API for each query
    api_key = os.getenv('BRAVE_API_KEY', '')
    if not api_key:
        log("⚠️ No BRAVE_API_KEY found, skipping web search")
        return []
    
    for query in queries[:3]:  # Limit to top 3 queries per run
        try:
            url = "https://api.search.brave.com/res/v1/news/search"
            headers = {"X-Subscription-Token": api_key}
            params = {"q": query, "count": 5, "freshness": "month"}
            
            response = requests.get(url, headers=headers, params=params, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                for item in data.get('results', []):
                    aid = hashlib.md5(f"{item.get('url')}:{item.get('title')}".encode()).hexdigest()
                    
                    if aid in seen['articles']:
                        continue
                    
                    article = {
                        'id': aid,
                        'title': item.get('title', 'No title'),
                        'link': item.get('url', ''),
                        'published': item.get('published', ''),
                        'summary': item.get('description', '')[:500],
                        'source': f"Web Search: {query[:30]}...",
                        'type': 'news',
                        'found_at': datetime.now().isoformat()
                    }
                    
                    new_articles.append(article)
                    seen['articles'][aid] = {'found_at': datetime.now().isoformat(), 'sent': False}
            
        except Exception as e:
            log(f"Error searching web for '{query}': {e}")
    
    save_seen(seen)
    return new_articles

def categorize_article(article):
    """Categorize article by signal type and priority"""
    title = article.get('title', '').lower()
    summary = article.get('summary', '').lower()
    combined = title + " " + summary
    
    # Critical signals
    critical = ['acquisition', 'acquires', 'merger', 'ipo', 'series a', 'series b', 'series c', 
                'funding', 'raised', 'investment', '$100m', '$50m', '$1b', 'unicorn']
    for signal in critical:
        if signal in combined:
            return 'critical', 'funding/acquisition'
    
    # High priority
    high = ['partnership', 'partners', 'major client', 'fortune 500', 'executive hire', 
            'ceo', 'cto', 'chief', 'president', 'expansion', 'new market', 'product launch']
    for signal in high:
        if signal in combined:
            return 'high', 'partnership/leadership'
    
    # Medium priority
    medium = ['hiring', 'job', 'career', 'growth', 'new office', 'award', 'recognition']
    for signal in medium:
        if signal in combined:
            return 'medium', 'growth/hiring'
    
    return 'low', 'general'

def check_linkedin_for_updates(config):
    """Check LinkedIn for company updates and executive posts"""
    # This would require LinkedIn API or scraping
    # For now, placeholder for structure
    companies = config.get('linkedin_companies', {})
    updates = []
    
    log(f"LinkedIn monitoring: {len(companies)} companies configured")
    log("Note: LinkedIn API integration required for full functionality")
    
    return updates

def check_job_boards(config):
    """Check job boards for hiring signals"""
    job_boards = config.get('job_boards', {})
    jobs = []
    
    log(f"Job board monitoring: {len(job_boards)} companies")
    
    # Placeholder - would need scraping or API access
    # Greenhouse, Lever, etc. have different structures
    
    return jobs

def save_articles(articles):
    """Save articles to file for email generation"""
    ARTICLES_FILE.parent.mkdir(parents=True, exist_ok=True)
    
    # Load existing
    existing = []
    if ARTICLES_FILE.exists():
        with open(ARTICLES_FILE) as f:
            existing = json.load(f)
    
    # Add new, avoiding duplicates
    existing_ids = {a['id'] for a in existing}
    for article in articles:
        if article['id'] not in existing_ids:
            existing.append(article)
            existing_ids.add(article['id'])
    
    # Sort by priority and date
    priority_order = {'critical': 0, 'high': 1, 'medium': 2, 'low': 3}
    existing.sort(key=lambda x: (priority_order.get(x.get('priority', 'low'), 4), 
                                  x.get('published', '')), reverse=True)
    
    # Keep only last 100 articles
    existing = existing[:100]
    
    with open(ARTICLES_FILE, 'w') as f:
        json.dump(existing, f, indent=2)
    
    return len(articles)

def main():
    log("=" * 70)
    log("Starting Enhanced Competitive Intelligence Scan")
    log("=" * 70)
    
    config = load_config()
    all_new = []
    
    # 1. Scan RSS feeds
    log("\n1. Scanning RSS feeds...")
    rss_articles = scan_rss_feeds(config)
    log(f"   Found {len(rss_articles)} new articles from RSS")
    all_new.extend(rss_articles)
    
    # 2. Web search
    log("\n2. Searching web for competitive news...")
    web_articles = search_web_for_news(config)
    log(f"   Found {len(web_articles)} new articles from web search")
    all_new.extend(web_articles)
    
    # 3. LinkedIn monitoring (placeholder)
    log("\n3. Checking LinkedIn updates...")
    linkedin_updates = check_linkedin_for_updates(config)
    log(f"   Found {len(linkedin_updates)} LinkedIn updates")
    all_new.extend(linkedin_updates)
    
    # 4. Job board monitoring (placeholder)
    log("\n4. Checking job boards...")
    job_updates = check_job_boards(config)
    log(f"   Found {len(job_updates)} job postings")
    all_new.extend(job_updates)
    
    # Categorize all articles and apply send limit (max 2 sends per article)
    sent_counts = load_sent_counts()
    filtered_articles = []
    
    for article in all_new:
        # Check if we've already sent this article 2+ times
        if not can_send_article(article['id'], sent_counts):
            log(f"   Skipping {article['id'][:8]}... (already sent 2 times)")
            continue
        
        priority, category = categorize_article(article)
        article['priority'] = priority
        article['category'] = category
        filtered_articles.append(article)
        
        # Increment send count
        increment_sent_count(article['id'], sent_counts)
    
    all_new = filtered_articles
    
    # Save and report
    if all_new:
        count = save_articles(all_new)
        log(f"\n✅ Total new articles: {count}")
        
        # Print summary
        critical = [a for a in all_new if a['priority'] == 'critical']
        high = [a for a in all_new if a['priority'] == 'high']
        medium = [a for a in all_new if a['priority'] == 'medium']
        
        print(f"\n{'='*70}")
        print(f"COMPETITIVE INTELLIGENCE: {len(all_new)} NEW SIGNALS")
        print(f"{'='*70}")
        print(f"🔴 Critical: {len(critical)} | 🟠 High: {len(high)} | 🟡 Medium: {len(medium)}")
        print(f"{'='*70}")
        
        for article in sorted(all_new, 
                              key=lambda x: {'critical': 0, 'high': 1, 'medium': 2, 'low': 3}.get(x['priority'], 4)):
            badge = "🔴" if article['priority'] == 'critical' else "🟠" if article['priority'] == 'high' else "🟡"
            print(f"\n{badge} [{article['source']}] {article['title']}")
            print(f"   {article['link'][:70]}...")
        
        print(f"\n{'='*70}")
        
        return len(all_new)
    else:
        log("\n✅ No new competitive signals found")
        return 0

if __name__ == "__main__":
    import sys
    count = main()
    sys.exit(0 if count >= 0 else 1)
