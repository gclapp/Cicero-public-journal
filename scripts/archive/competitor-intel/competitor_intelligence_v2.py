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

def can_send_article(article_id, sent_counts, config=None):
    """Check if article can be sent (strict: only once if strict_deduplication enabled)"""
    if config is None:
        config = load_config()
    
    # Strict mode: article only sent once ever
    if config.get('filters', {}).get('strict_deduplication', True):
        return sent_counts.get(article_id, 0) == 0
    
    # Legacy mode: max 2 times
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

def normalize_title(title):
    """Normalize title for duplicate detection"""
    import re
    # Remove HTML tags
    title = re.sub(r'<[^>]+>', '', title)
    # Remove extra whitespace
    title = ' '.join(title.split())
    # Remove common suffixes/prefixes
    title = re.sub(r'\s*-\s*(PR Newswire|Business Wire|GlobeNewswire|TipRanks\.com)$', '', title, flags=re.IGNORECASE)
    title = re.sub(r'\s*\|\s*(The Verge|AlphaMaven|Fierce Healthcare)$', '', title, flags=re.IGNORECASE)
    # Convert to lowercase
    return title.lower().strip()

def is_duplicate_title(title, existing_articles=None):
    """Check if similar title already exists in current batch OR previously saved articles"""
    normalized = normalize_title(title)
    
    # Check against current batch
    if existing_articles:
        for article in existing_articles:
            existing_normalized = normalize_title(article.get('title', ''))
            if normalized == existing_normalized:
                return True
            if len(normalized) > 20 and len(existing_normalized) > 20:
                if normalized in existing_normalized or existing_normalized in normalized:
                    return True
    
    # Check against ALL previously saved articles
    if ARTICLES_FILE.exists():
        try:
            with open(ARTICLES_FILE) as f:
                saved_articles = json.load(f)
            for article in saved_articles:
                existing_normalized = normalize_title(article.get('title', ''))
                if normalized == existing_normalized:
                    return True
                if len(normalized) > 20 and len(existing_normalized) > 20:
                    if normalized in existing_normalized or existing_normalized in normalized:
                        return True
        except:
            pass
    
    return False

def is_stale_article(published_str, max_age_days=None):
    """Check if article is too old to report (default: 3 days for strict freshness)"""
    if max_age_days is None:
        config = load_config()
        max_age_days = config.get('filters', {}).get('max_article_age_days', 3)
    
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
                title = entry.get('title', 'No title')
                
                # Skip if already seen by ID
                if aid in seen['articles']:
                    continue
                
                # Skip if duplicate title (from another source)
                if is_duplicate_title(title, new_articles):
                    log(f"   Skipping duplicate: {title[:50]}...")
                    continue
                
                published = entry.get('published', entry.get('updated', ''))
                
                # Skip stale articles (>7 days old)
                if is_stale_article(published):
                    continue
                
                article = {
                    'id': aid,
                    'title': title,
                    'link': entry.get('link', ''),
                    'published': published,
                    'summary': entry.get('summary', '')[:500],
                    'source': name,
                    'type': 'news',
                    'found_at': datetime.now().isoformat()
                }
                
                new_articles.append(article)
                # NOTE: Don't add to seen cache here - add AFTER filtering passes
                
        except Exception as e:
            log(f"Error scanning {name}: {e}")
    
    # NOTE: Don't save seen cache here - save AFTER filtering passes
    return new_articles

def search_web_for_news(config):
    """Search web for real-time competitive news"""
    queries = config.get('web_search_queries', [])
    new_articles = []
    seen = load_seen()
    
    # Use Brave Search API for each query
    # Try environment variable first, then consolidated credentials
    api_key = os.getenv('BRAVE_API_KEY', '')
    if not api_key:
        # Try consolidated credentials file
        creds_file = Path.home() / ".openclaw" / "config" / "sensitive-credentials.json"
        if creds_file.exists():
            try:
                with open(creds_file) as f:
                    creds = json.load(f)
                    api_key = creds.get('brave_search', {}).get('api_key', '')
            except:
                pass
    
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
                    # NOTE: Don't add to seen cache here - add AFTER filtering passes
            
        except Exception as e:
            log(f"Error searching web for '{query}': {e}")
    
    # NOTE: Don't save seen cache here - save AFTER filtering passes
    return new_articles

def is_stock_investor_news(article):
    """Check if article is stock price/investor news (not real competitive intel)
    
    Allows PGNY news if it's about competition, partnerships, or strategy (not just stock price)
    """
    title = article.get('title', '').lower()
    summary = article.get('summary', '').lower()
    combined = title + " " + summary
    
    # Check if it's about competition/partnerships (keep these)
    competitive_context = [
        'competition', 'competitor', 'competitive', 'market share',
        'partnership', 'partners', 'client', 'employer', 'expansion',
        'strategic', 'strategy', 'launch', 'new product', 'innovation'
    ]
    is_competitive = any(kw in combined for kw in competitive_context)
    
    # Stock/investor keywords that indicate low-value content
    stock_keywords = [
        'stock price', 'stock analysis', 'investor should', 'investors should',
        'buying now', 'selling now', 'price target', 'analyst rating',
        'earnings preview', 'earnings review', 'q4 earnings', 'q1 earnings',
        'q2 earnings', 'q3 earnings', 'quarterly earnings', 'financial results',
        'stock up', 'stock down', 'shares up', 'shares down',
        'reflecting on', 'q4 roundup', 'earnings roundup', 'stock volatility',
        'amid recent volatility', 'what investors', 'investor know',
        'smart investor', 'wall street', 'trading at', 'market cap',
        'stock valuation', 'fair value', 'overvalued', 'undervalued',
        'bullish', 'bearish', 'outperform', 'underperform', 'hold rating',
        'buy rating', 'sell rating', 'analyst consensus', 'consensus estimate'
    ]
    
    # PGNY ticker alone is not enough to filter - check if it's just stock news
    has_stock_keyword = any(kw in combined for kw in stock_keywords)
    
    # If it has stock keywords AND no competitive context, filter it out
    if has_stock_keyword and not is_competitive:
        return True
    
    return False

def is_irrelevant_maven_article(article):
    """Filter out non-Maven Clinic articles that mention 'Maven' (e.g., Pentagon, EQT)"""
    title = article.get('title', '').lower()
    summary = article.get('summary', '').lower()
    combined = title + " " + summary
    
    # Must mention Maven
    if 'maven' not in combined:
        return False
    
    # Keywords that indicate it's NOT Maven Clinic (the health company)
    non_healthcare_indicators = [
        'pentagon', 'battlefield', 'military', 'defense', 'weapon', 'warfare',
        'eqt', 'private equity', 'infrastructure', 'investment firm',
        'project maven', 'ai weapons', 'defense department', 'dod',
        'space force', 'navy', 'army', 'air force'
    ]
    
    for indicator in non_healthcare_indicators:
        if indicator in combined:
            return True
    
    # Must have health/fertility context to be relevant
    health_indicators = [
        'clinic', 'health', 'fertility', 'family', 'pregnancy', 'women',
        'care', 'benefits', 'employer', 'patient', 'medical', 'healthcare',
        'ivf', 'egg freezing', 'surrogacy', 'menopause', 'maternity'
    ]
    
    has_health_context = any(h in combined for h in health_indicators)
    
    # If it mentions Maven but has no health context, it's probably not Maven Clinic
    if not has_health_context:
        return True
    
    return False

def score_femtech_relevance(article, config=None):
    """Score how relevant an article is to FemTech/women's health (0-100)"""
    if config is None:
        config = load_config()
    
    title = article.get('title', '').lower()
    summary = article.get('summary', '').lower()
    combined = title + " " + summary
    
    # REJECT stock/investor news immediately
    if is_stock_investor_news(article):
        return -100  # Negative score ensures exclusion
    
    # REJECT non-healthcare Maven articles (Pentagon, EQT, etc.)
    if is_irrelevant_maven_article(article):
        return -100  # Negative score ensures exclusion
    
    score = 0
    
    # FemTech keywords (high weight)
    femtech_keywords = config.get('filters', {}).get('femtech_keywords', [
        'femtech', "women's health", 'fertility', 'menopause', 'maternity',
        'pregnancy', 'ivf', 'egg freezing', 'surrogacy'
    ])
    
    for keyword in femtech_keywords:
        if keyword in combined:
            score += 15
    
    # Competitor mentions (high weight)
    competitors = ['maven', 'carrot', 'kindbody', 'pomelo', 'midi', 'evernow', 
                   'pacify', 'progyny', 'win fertility']
    for comp in competitors:
        if comp in combined:
            score += 20
    
    # Funding signals (medium weight)
    funding = ['funding', 'series', 'raised', 'investment', 'venture']
    for term in funding:
        if term in combined:
            score += 10
    
    # Exclude irrelevant topics
    exclude_keywords = config.get('filters', {}).get('exclude_keywords', [])
    for exclude in exclude_keywords:
        if exclude in combined:
            score -= 50  # Heavy penalty
    
    return min(score, 100)  # Cap at 100

def categorize_article(article):
    """Categorize article by signal type and priority"""
    title = article.get('title', '').lower()
    summary = article.get('summary', '').lower()
    combined = title + " " + summary
    
    # Calculate FemTech relevance
    femtech_score = score_femtech_relevance(article)
    article['femtech_score'] = femtech_score
    
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
    
    # 3. LinkedIn executive post monitoring
    log("\n3. Checking LinkedIn executive posts...")
    try:
        import subprocess
        result = subprocess.run(
            ['python3', '/home/ubuntu/.openclaw/workspace/scripts/linkedin_exec_monitor.py'],
            capture_output=True, text=True, timeout=60
        )
        if result.returncode == 0:
            log("   ✓ LinkedIn executive scan complete")
        else:
            log(f"   ⚠ LinkedIn scan issue (may need Brave API key)")
    except Exception as e:
        log(f"   ⚠ LinkedIn scan error: {e}")
    
    # 4. Reddit intelligence monitoring
    log("\n4. Checking Reddit for competitive intelligence...")
    try:
        import subprocess
        result = subprocess.run(
            ['python3', '/home/ubuntu/.openclaw/workspace/scripts/reddit_intel_collector.py'],
            capture_output=True, text=True, timeout=120
        )
        if result.returncode == 0:
            # Load Reddit results
            reddit_file = Path.home() / ".openclaw" / "workspace" / "config" / "reddit-intelligence.json"
            if reddit_file.exists():
                with open(reddit_file) as f:
                    reddit_data = json.load(f)
                # Handle both old format (posts key) and new format (results key)
                reddit_posts = reddit_data.get('posts', [])
                if not reddit_posts and 'results' in reddit_data:
                    # New format - flatten results from all categories
                    reddit_posts = []
                    for category, posts in reddit_data['results'].items():
                        if isinstance(posts, list):
                            for post in posts:
                                post['_intel_category'] = category
                            reddit_posts.extend(posts)
                log(f"   Found {len(reddit_posts)} Reddit posts")
                
                # Convert Reddit posts to article format
                for post in reddit_posts:
                    title = post.get('title', 'Reddit Discussion')[:200]
                    
                    # Skip if duplicate title (from previous runs or current batch)
                    if is_duplicate_title(title, all_new):
                        log(f"   Skipping duplicate Reddit: {title[:50]}...")
                        continue
                    
                    article = {
                        'id': f"reddit_{post.get('id', hashlib.md5(post.get('url', '').encode()).hexdigest())}",
                        'title': title,
                        'link': post.get('url', ''),
                        'published': post.get('created', datetime.now().isoformat()),
                        'summary': post.get('content', '')[:500] if post.get('content') else f"r/{post.get('subreddit', 'unknown')} - {post.get('author', 'unknown')}",
                        'source': f"Reddit: r/{post.get('subreddit', 'unknown')}",
                        'type': 'reddit',
                        'found_at': datetime.now().isoformat(),
                        'reddit_data': {
                            'subreddit': post.get('subreddit'),
                            'author': post.get('author'),
                            'score': post.get('score'),
                            'comments': post.get('comments'),
                            'priority': post.get('priority')
                        }
                    }
                    all_new.append(article)
        else:
            log(f"   ⚠ Reddit scan issue: {result.stderr[:100]}")
    except Exception as e:
        log(f"   ⚠ Reddit scan error: {e}")
    
    # 5. Job board monitoring
    log("\n5. Checking job boards...")
    job_updates = check_job_boards(config)
    log(f"   Found {len(job_updates)} job postings")
    all_new.extend(job_updates)
    
    # DEDUPLICATION: Remove articles with duplicate titles across all sources
    log("\n6. Deduplicating articles by title...")
    unique_articles = []
    seen_titles = set()
    for article in all_new:
        normalized = normalize_title(article.get('title', ''))
        if normalized and normalized not in seen_titles:
            seen_titles.add(normalized)
            unique_articles.append(article)
        else:
            log(f"   Removing duplicate title: {article.get('title', '')[:50]}...")
    log(f"   {len(all_new)} articles -> {len(unique_articles)} unique after deduplication")
    all_new = unique_articles
    
    # Categorize all articles and apply strict filtering
    sent_counts = load_sent_counts()
    config = load_config()
    seen = load_seen()  # Load seen cache to add filtered articles
    filtered_articles = []
    
    for article in all_new:
        # Check if we've already sent this article (strict: only once)
        if not can_send_article(article['id'], sent_counts, config):
            log(f"   Skipping {article['id'][:8]}... (already sent)")
            continue
        
        # Calculate FemTech relevance
        femtech_score = score_femtech_relevance(article, config)
        article['femtech_score'] = femtech_score
        
        # Skip low-relevance articles (< 15 score) - was 20, lowered to catch more relevant content
        if femtech_score < 15:
            log(f"   Skipping {article['id'][:8]}... (low FemTech relevance: {femtech_score})")
            continue
        
        priority, category = categorize_article(article)
        article['priority'] = priority
        article['category'] = category
        filtered_articles.append(article)
        
        # Add to seen cache now that article passed filtering
        seen['articles'][article['id']] = {'found_at': datetime.now().isoformat(), 'sent': False}
        
        # NOTE: Send count is incremented in competitor_email_v2.py when email is actually sent
        # NOT here during scanning
    
    # Save seen cache with filtered articles
    save_seen(seen)
    
    # Sort by priority and FemTech score, then limit to max articles
    max_articles = config.get('filters', {}).get('max_articles_per_report', 10)
    
    def sort_key(article):
        priority_order = {'critical': 0, 'high': 1, 'medium': 2, 'low': 3}
        return (priority_order.get(article['priority'], 4), -article.get('femtech_score', 0))
    
    filtered_articles.sort(key=sort_key)
    
    # Limit to top articles
    if len(filtered_articles) > max_articles:
        log(f"   Limiting from {len(filtered_articles)} to {max_articles} articles (top priority)")
        filtered_articles = filtered_articles[:max_articles]
    
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
        
        for article in all_new:
            badge = "🔴" if article['priority'] == 'critical' else "🟠" if article['priority'] == 'high' else "🟡"
            femtech_badge = f" (FemTech: {article.get('femtech_score', 0)})"
            print(f"\n{badge} [{article['source']}] {article['title']}{femtech_badge}")
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
