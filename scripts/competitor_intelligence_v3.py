#!/usr/bin/env python3
"""
Competitive Intelligence System v3 - Complete Overhaul
- Fixed deduplication (single source of truth)
- Better RSS feed coverage
- Improved FemTech relevance scoring
- Direct company blog monitoring
"""

import os
import json
import hashlib
import re
import feedparser
import requests
from datetime import datetime, timedelta
from pathlib import Path

# Paths
CONFIG_FILE = Path.home() / ".openclaw" / "workspace" / "config" / "competitive-intelligence-config.json"
SEEN_FILE = Path.home() / ".openclaw" / "workspace" / "config" / "competitor-seen-v3.json"
SENT_COUNT_FILE = Path.home() / ".openclaw" / "workspace" / "config" / "competitor-sent-count-v3.json"
ARTICLES_FILE = Path.home() / ".openclaw" / "workspace" / "config" / "competitor-articles-v3.json"
LOG_FILE = Path.home() / ".openclaw" / "workspace" / "logs" / "competitor-v3.log"

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
    """Load seen article IDs with timestamps and titles"""
    if SEEN_FILE.exists():
        with open(SEEN_FILE) as f:
            return json.load(f)
    return {"articles": {}, "linkedin_posts": {}, "job_changes": {}, "titles": {}}

def save_seen(seen):
    """Save seen article IDs"""
    SEEN_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(SEEN_FILE, 'w') as f:
        json.dump(seen, f, indent=2)

def load_sent_counts():
    """Load article send counts - v3 uses single source of truth"""
    if SENT_COUNT_FILE.exists():
        with open(SENT_COUNT_FILE) as f:
            return json.load(f)
    return {}

def save_sent_counts(counts):
    """Save article send counts"""
    SENT_COUNT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(SENT_COUNT_FILE, 'w') as f:
        json.dump(counts, f, indent=2)

def can_send_article(article_id, sent_counts, max_sends=1):
    """
    Check if article can be sent.
    v3: Strict mode - only send once by default (max_sends=1)
    """
    count = sent_counts.get(article_id, 0)
    return count < max_sends

def increment_sent_count(article_id, sent_counts):
    """Increment the send count for an article"""
    sent_counts[article_id] = sent_counts.get(article_id, 0) + 1
    save_sent_counts(sent_counts)

def normalize_title(title):
    """Normalize title for deduplication comparison"""
    if not title:
        return ""
    # Lowercase, strip whitespace, remove extra spaces
    normalized = title.lower().strip()
    # Remove common suffixes/prefixes that vary by source
    normalized = re.sub(r'\s+', ' ', normalized)  # Collapse multiple spaces
    normalized = re.sub(r'\s*[-|]\s*(pr newswire|business wire|globenewswire|\.\.\.)$', '', normalized)
    return normalized

def article_id(entry):
    """Generate unique ID for article - v3 improved stability"""
    # Use link as primary identifier for stability
    link = entry.get('link', '')
    title = entry.get('title', '')
    # Normalize URL to avoid duplicates from tracking params
    link = link.split('?')[0].split('#')[0].rstrip('/')
    content = f"{link}:{title}"
    return hashlib.md5(content.encode()).hexdigest()

def parse_date(published_str):
    """Parse various date formats"""
    if not published_str:
        return None
    
    formats = [
        "%a, %d %b %Y %H:%M:%S %Z",
        "%a, %d %b %Y %H:%M:%S %z",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%dT%H:%M:%S%z",
        "%Y-%m-%dT%H:%M:%SZ",
        "%Y-%m-%d %H:%M:%S",
        "%d %b %Y %H:%M:%S",
        "%B %d, %Y",
        "%b %d, %Y"
    ]
    
    for fmt in formats:
        try:
            return datetime.strptime(published_str[:len(fmt)+10], fmt)
        except:
            continue
    
    # Try ISO format
    try:
        return datetime.fromisoformat(published_str.replace('Z', '+00:00').replace('+00:00', ''))
    except:
        pass
    
    return None

def is_stale_article(published_str, max_age_days=7):
    """Check if article is too old to report (default: 7 days)"""
    pub_date = parse_date(published_str)
    if not pub_date:
        return False  # If we can't parse, assume it's fresh
    
    # Handle timezone-aware dates
    if pub_date.tzinfo:
        pub_date = pub_date.replace(tzinfo=None)
    
    age = datetime.now() - pub_date
    return age.days > max_age_days

def get_article_date(published_str):
    """Get formatted date string"""
    dt = parse_date(published_str)
    if dt:
        return dt.strftime('%b %d, %Y')
    return 'Unknown date'

def is_title_duplicate(title, seen):
    """Check if title already exists (exact match after normalization)"""
    normalized = normalize_title(title)
    if not normalized:
        return False
    return normalized in seen.get('titles', {})

def add_title_to_seen(title, seen):
    """Add normalized title to seen tracking"""
    normalized = normalize_title(title)
    if normalized:
        if 'titles' not in seen:
            seen['titles'] = {}
        seen['titles'][normalized] = datetime.now().isoformat()

def scan_rss_feeds(config):
    """Scan RSS feeds for new articles"""
    seen = load_seen()
    new_articles = []
    feeds = config.get('rss_feeds', {})
    
    for name, url in feeds.items():
        try:
            log(f"   Scanning: {name}")
            feed = feedparser.parse(url)
            
            for entry in feed.entries:
                aid = article_id(entry)
                title = entry.get('title', 'No title')
                
                # Skip if already seen by ID
                if aid in seen['articles']:
                    continue
                
                # Skip if title already exists (exact match dedup)
                if is_title_duplicate(title, seen):
                    log(f"   Skipping duplicate title: {title[:60]}...")
                    continue
                
                published = entry.get('published', entry.get('updated', entry.get('pubDate', '')))
                
                # Skip stale articles (>7 days old)
                if is_stale_article(published):
                    continue
                
                article = {
                    'id': aid,
                    'title': title,
                    'link': entry.get('link', ''),
                    'published': published,
                    'published_formatted': get_article_date(published),
                    'summary': entry.get('summary', entry.get('description', ''))[:500],
                    'source': name,
                    'type': 'news',
                    'found_at': datetime.now().isoformat()
                }
                
                new_articles.append(article)
                seen['articles'][aid] = {
                    'found_at': datetime.now().isoformat(),
                    'sent': False,
                    'title': title[:100]  # Store title for debugging
                }
                add_title_to_seen(title, seen)
                
        except Exception as e:
            log(f"   ⚠️ Error scanning {name}: {e}")
    
    save_seen(seen)
    return new_articles

def search_web_for_news(config):
    """Search web for real-time competitive news"""
    queries = config.get('web_search_queries', [])
    new_articles = []
    seen = load_seen()
    
    # Use Brave Search API
    api_key = os.getenv('BRAVE_API_KEY', '')
    if not api_key:
        creds_file = Path.home() / ".openclaw" / "config" / "sensitive-credentials.json"
        if creds_file.exists():
            try:
                with open(creds_file) as f:
                    creds = json.load(f)
                    api_key = creds.get('brave_search', {}).get('api_key', '')
            except:
                pass
    
    if not api_key:
        log("   ⚠️ No BRAVE_API_KEY found, skipping web search")
        return []
    
    # Limit queries per run to avoid rate limits
    for query in queries[:5]:
        try:
            url = "https://api.search.brave.com/res/v1/news/search"
            headers = {"X-Subscription-Token": api_key}
            params = {"q": query, "count": 5, "freshness": "week"}  # Changed from month to week
            
            response = requests.get(url, headers=headers, params=params, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                for item in data.get('results', []):
                    item_url = item.get('url', '')
                    item_title = item.get('title', '')
                    aid = hashlib.md5(f"{item_url}:{item_title}".encode()).hexdigest()
                    
                    # Skip if already seen by ID
                    if aid in seen['articles']:
                        continue
                    
                    # Skip if title already exists (exact match dedup)
                    if is_title_duplicate(item_title, seen):
                        log(f"   Skipping duplicate title: {item_title[:60]}...")
                        continue
                    
                    article = {
                        'id': aid,
                        'title': item_title,
                        'link': item_url,
                        'published': item.get('published', ''),
                        'published_formatted': get_article_date(item.get('published', '')),
                        'summary': item.get('description', '')[:500],
                        'source': f"Web: {query[:40]}...",
                        'type': 'news',
                        'found_at': datetime.now().isoformat()
                    }
                    
                    new_articles.append(article)
                    seen['articles'][aid] = {
                        'found_at': datetime.now().isoformat(),
                        'sent': False,
                        'title': item_title[:100]
                    }
                    add_title_to_seen(item_title, seen)
            elif response.status_code == 429:
                log(f"   ⚠️ Brave API rate limit hit")
                break
                    
        except Exception as e:
            log(f"   ⚠️ Error searching web for '{query[:50]}...': {e}")
    
    save_seen(seen)
    return new_articles

def score_femtech_relevance(article, config=None):
    """Score how relevant an article is to FemTech/women's health (0-100)"""
    if config is None:
        config = load_config()
    
    title = article.get('title', '').lower()
    summary = article.get('summary', '').lower()
    combined = title + " " + summary
    
    score = 0
    
    # FemTech keywords (high weight)
    femtech_keywords = config.get('filters', {}).get('femtech_keywords', [
        'femtech', "women's health", 'fertility', 'menopause', 'maternity',
        'pregnancy', 'ivf', 'egg freezing', 'surrogacy', 'women healthcare',
        'reproductive health', 'maternal health', 'family building'
    ])
    
    for keyword in femtech_keywords:
        if keyword.lower() in combined:
            score += 15
    
    # Competitor mentions (high weight)
    competitors = {
        'maven': 25, 'maven clinic': 25,
        'carrot': 25, 'carrot fertility': 25,
        'kindbody': 25,
        'progyny': 25, 'pgny': 25,
        'win fertility': 25, 'winfertility': 25,
        'pomelo': 20, 'pomelo health': 20,
        'midi': 20, 'midi health': 20,
        'evernow': 20,
        'pacify': 20,
        'oura': 20,
        'flo health': 20, 'flo': 15
    }
    
    for comp, weight in competitors.items():
        if comp in combined:
            score += weight
    
    # Funding signals (high weight)
    funding_terms = ['funding', 'series a', 'series b', 'series c', 'series d',
                     'raised', 'investment', 'venture', 'million', 'billion']
    for term in funding_terms:
        if term in combined:
            score += 12
    
    # Strategic signals (medium weight)
    strategic = ['partnership', 'acquisition', 'merger', 'ipo', 'launch',
                 'expansion', 'new product', 'ai', 'artificial intelligence']
    for term in strategic:
        if term in combined:
            score += 8
    
    # Exclude irrelevant topics (heavy penalty)
    exclude_keywords = config.get('filters', {}).get('exclude_keywords', [
        'agriculture', 'veterinary', 'pet', 'animal fertility', 'crop',
        'livestock', 'plant breeding', 'equine', 'bovine'
    ])
    
    for exclude in exclude_keywords:
        if exclude in combined:
            score -= 50
    
    return max(0, min(score, 100))  # Cap between 0-100

def categorize_article(article):
    """Categorize article by signal type and priority"""
    title = article.get('title', '').lower()
    summary = article.get('summary', '').lower()
    combined = title + " " + summary
    
    # Critical signals - funding, M&A, IPO
    critical = ['acquisition', 'acquires', 'merger', 'ipo', 'series a', 'series b', 
                'series c', 'series d', 'funding', 'raised $', 'investment round',
                'unicorn', 'valuation']
    for signal in critical:
        if signal in combined:
            return 'critical', 'funding/acquisition'
    
    # High priority - partnerships, major clients, executive hires
    high = ['partnership', 'partners with', 'major client', 'fortune 500', 
            'executive hire', 'ceo appointed', 'cto hired', 'chief', 'president',
            'expansion', 'new market', 'product launch', 'ai launch']
    for signal in high:
        if signal in combined:
            return 'high', 'partnership/leadership'
    
    # Medium priority - hiring, growth, awards
    medium = ['hiring', 'job opening', 'career', 'growth', 'new office', 
              'award', 'recognition', 'conference', ' keynote']
    for signal in medium:
        if signal in combined:
            return 'medium', 'growth/hiring'
    
    return 'low', 'general'

def get_company_from_article(article):
    """Determine company from article content"""
    combined = (article.get('title', '') + ' ' + article.get('summary', '')).lower()
    
    companies = {
        'Maven': ['maven clinic', 'maven'],
        'Carrot': ['carrot fertility', 'carrot'],
        'KindBody': ['kindbody'],
        'Progyny': ['progyny', 'pgny'],
        'WIN Fertility': ['win fertility', 'winfertility'],
        'Pomelo Health': ['pomelo health', 'pomelo'],
        'Midi Health': ['midi health', 'midi'],
        'Evernow': ['evernow'],
        'Pacify': ['pacify'],
        'Oura': ['oura'],
        'Flo Health': ['flo health', 'flo']
    }
    
    for company, terms in companies.items():
        for term in terms:
            if term in combined:
                return company
    
    return 'General'

def generate_why_matters(article):
    """Generate 'Why This Matters' context for an article"""
    title = article.get('title', '').lower()
    summary = article.get('summary', '').lower()
    combined = title + ' ' + summary
    company = get_company_from_article(article)
    priority = article.get('priority', 'medium')
    
    # Maven Intelligence tracking
    if 'maven intelligence' in combined:
        return "🎯 Maven's AI orchestration platform represents a direct competitive threat. They're moving from care navigation to AI-driven care management — watch for client announcements."
    
    if 'maven' in combined and ('ai' in combined or 'artificial intelligence' in combined or 'platform' in combined):
        return "🤖 Maven investing heavily in AI capabilities signals a product shift toward automated care coordination. Monitor for feature releases."
    
    # Funding
    if any(k in combined for k in ['funding', 'raises', 'series', 'investment']):
        if company == 'Maven':
            return "💰 Fresh capital means aggressive expansion ahead. Expect increased sales pressure and possible M&A activity."
        elif company == 'Carrot':
            return "💰 Carrot funding signals continued market validation. Watch for geographic expansion or new product verticals."
        elif company == 'KindBody':
            return "💰 KindBody funding supports their clinic + tech hybrid model. Monitor for new clinic openings."
        elif company == 'Progyny':
            return "💰 Progyny funding news affects stock price and market perception. Track analyst reactions."
        else:
            return "💰 New funding indicates investor confidence in the sector. Could lead to increased competitive pressure."
    
    # Partnerships
    if any(k in combined for k in ['partnership', 'partners with', 'collaboration']):
        if company == 'Maven':
            return "🤝 Maven partnership expands their ecosystem. Check if distribution channel or tech integration."
        else:
            return "🤝 Strategic partnerships can rapidly expand market reach. Monitor for exclusivity clauses."
    
    # Acquisitions
    if any(k in combined for k in ['acquisition', 'acquires', 'buys', 'merger']):
        return "🏢 M&A activity reshapes competitive landscape. Look for talent grabs or technology integration."
    
    # Executive changes
    if any(k in combined for k in ['ceo', 'cto', 'chief', 'president', 'appointed', 'hired']):
        return "👔 Leadership changes often signal strategic shifts. Watch for org restructuring or strategy pivots."
    
    # Product launches
    if any(k in combined for k in ['launch', 'introduces', 'unveils', 'new product']):
        return "🚀 New product launch indicates competitive positioning. Evaluate for gaps in your own roadmap."
    
    # Progyny Select (fully insured)
    if 'progyny select' in combined or 'fully insured' in combined:
        return "🏛️ Progyny Select is a major strategic expansion into the fully insured market. This opens new TAM but changes competitive dynamics."
    
    # Default by priority
    if priority == 'critical':
        return "🔴 Critical market movement with immediate competitive implications. Review for strategic response."
    elif priority == 'high':
        return "🟠 Significant development that could shift market dynamics. Monitor for follow-on announcements."
    else:
        return "🟡 Industry signal worth tracking. May indicate broader trends or competitive positioning."

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
    existing.sort(key=lambda x: (
        priority_order.get(x.get('priority', 'low'), 4),
        -x.get('femtech_score', 0),
        x.get('published', '')
    ))
    
    # Keep only last 200 articles (increased for better history)
    existing = existing[:200]
    
    with open(ARTICLES_FILE, 'w') as f:
        json.dump(existing, f, indent=2)
    
    return len(articles)

def main():
    log("=" * 70)
    log("Starting Competitive Intelligence Scan v3")
    log("=" * 70)
    
    config = load_config()
    sent_counts = load_sent_counts()
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
    
    # 3. LinkedIn executive monitoring
    log("\n3. Checking LinkedIn executive posts...")
    try:
        import subprocess
        result = subprocess.run(
            ['python3', '/home/ubuntu/.openclaw/workspace/scripts/linkedin_monitor.py'],
            capture_output=True, text=True, timeout=60
        )
        if result.returncode == 0:
            log("   ✓ LinkedIn executive scan complete")
        else:
            log(f"   ⚠️ LinkedIn scan issue")
    except Exception as e:
        log(f"   ⚠️ LinkedIn scan error: {e}")
    
    # Process and filter articles
    filtered_articles = []
    
    for article in all_new:
        # Check if we've already sent this article (strict: only once)
        if not can_send_article(article['id'], sent_counts, max_sends=1):
            log(f"   Skipping {article['id'][:8]}... (already sent {sent_counts.get(article['id'], 0)} times)")
            continue
        
        # Calculate FemTech relevance
        femtech_score = score_femtech_relevance(article, config)
        article['femtech_score'] = femtech_score
        
        # Skip low-relevance articles (< 20 score)
        if femtech_score < 20:
            log(f"   Skipping {article['id'][:8]}... (low FemTech relevance: {femtech_score})")
            continue
        
        # Categorize
        priority, category = categorize_article(article)
        article['priority'] = priority
        article['category'] = category
        article['company'] = get_company_from_article(article)
        article['why_matters'] = generate_why_matters(article)
        
        filtered_articles.append(article)
        
        # Mark as sent (will be tracked by email generator)
        increment_sent_count(article['id'], sent_counts)
    
    # Sort by priority and FemTech score
    priority_order = {'critical': 0, 'high': 1, 'medium': 2, 'low': 3}
    filtered_articles.sort(key=lambda x: (
        priority_order.get(x['priority'], 4),
        -x.get('femtech_score', 0)
    ))
    
    # Limit to max articles per report
    max_articles = config.get('filters', {}).get('max_articles_per_report', 15)
    if len(filtered_articles) > max_articles:
        log(f"   Limiting from {len(filtered_articles)} to {max_articles} articles")
        filtered_articles = filtered_articles[:max_articles]
    
    # Save and report
    if filtered_articles:
        count = save_articles(filtered_articles)
        log(f"\n✅ Total new articles: {count}")
        
        # Print summary
        critical = [a for a in filtered_articles if a['priority'] == 'critical']
        high = [a for a in filtered_articles if a['priority'] == 'high']
        medium = [a for a in filtered_articles if a['priority'] == 'medium']
        
        print(f"\n{'='*70}")
        print(f"COMPETITIVE INTELLIGENCE: {len(filtered_articles)} NEW SIGNALS")
        print(f"{'='*70}")
        print(f"🔴 Critical: {len(critical)} | 🟠 High: {len(high)} | 🟡 Medium: {len(medium)}")
        print(f"{'='*70}")
        
        for article in filtered_articles:
            badge = "🔴" if article['priority'] == 'critical' else "🟠" if article['priority'] == 'high' else "🟡"
            company = article.get('company', 'General')
            print(f"\n{badge} [{company}] {article['title'][:70]}...")
        
        print(f"\n{'='*70}")
        
        return len(filtered_articles)
    else:
        log("\n✅ No new competitive signals found")
        return 0

if __name__ == "__main__":
    import sys
    count = main()
    sys.exit(0 if count >= 0 else 1)