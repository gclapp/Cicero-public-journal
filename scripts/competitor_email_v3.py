#!/usr/bin/env python3
"""
Competitive Intelligence Email Generator v3.2
Executive summary at top, proper date filtering, no duplicates
"""

import json
import re
import requests
from datetime import datetime, timedelta
from pathlib import Path
from email.utils import parsedate_to_datetime
from bs4 import BeautifulSoup

ARTICLES_FILE = Path.home() / ".openclaw" / "workspace" / "config" / "competitor-articles-v2.json"
PROGYNY_FILE = Path.home() / ".openclaw" / "workspace" / "config" / "progyny-sentiment.json"
REDDIT_FILE = Path.home() / ".openclaw" / "workspace" / "config" / "reddit-competitive-intel.json"
SENT_COUNT_FILE = Path.home() / ".openclaw" / "workspace" / "config" / "competitor-sent-count-v3.json"
EMAIL_OUTPUT = Path.home() / ".openclaw" / "workspace" / "config" / "competitor-email-v3.html"

def load_json(filepath):
    if filepath.exists():
        with open(filepath) as f:
            return json.load(f)
    return {}

def scrape_date_from_url(url):
    """Scrape actual publication date from article"""
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        response = requests.get(url, headers=headers, timeout=8)
        if response.status_code != 200:
            return None
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Try meta tags first
        for meta in soup.find_all('meta'):
            prop = meta.get('property', '').lower()
            name = meta.get('name', '').lower()
            if any(x in prop or x in name for x in ['published_time', 'date', 'pubdate']):
                content = meta.get('content', '')
                if content:
                    try:
                        dt = parsedate_to_datetime(content)
                        return dt.strftime('%b %d, %Y')
                    except:
                        pass
        
        # Try time tags
        for time in soup.find_all('time'):
            datetime_attr = time.get('datetime', '')
            if datetime_attr:
                try:
                    dt = parsedate_to_datetime(datetime_attr)
                    return dt.strftime('%b %d, %Y')
                except:
                    pass
        
        # Look for date patterns in text
        text = soup.get_text()
        patterns = [
            r'((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+\d{1,2},?\s+202[0-6])',
            r'(\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+202[0-6])',
        ]
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1)
        
        return None
    except:
        return None

def parse_article_date(article):
    """Get best date for article, scraping if necessary"""
    # Try published field
    pub = article.get('published', '')
    if pub:
        try:
            dt = parsedate_to_datetime(pub)
            return dt
        except:
            try:
                return datetime.fromisoformat(pub.replace('Z', '+00:00').replace('+00:00', ''))
            except:
                pass
    
    # Try scraping from URL
    url = article.get('link', '')
    if url:
        scraped = scrape_date_from_url(url)
        if scraped:
            try:
                return datetime.strptime(scraped, '%b %d, %Y')
            except:
                pass
    
    # Fallback to found_at
    found = article.get('found_at', '')
    if found:
        try:
            return datetime.fromisoformat(found.replace('Z', '+00:00').replace('+00:00', ''))
        except:
            pass
    
    return None

def is_within_30_days(article):
    """Check if article is within 30 days"""
    article_date = parse_article_date(article)
    if not article_date:
        return False
    cutoff = datetime.now() - timedelta(days=30)
    if article_date.tzinfo:
        article_date = article_date.replace(tzinfo=None)
    return article_date >= cutoff

def format_article_date(article):
    """Format date for display"""
    dt = parse_article_date(article)
    if dt:
        return dt.strftime('%b %d, %Y')
    return 'Date unknown'

def can_send_article(article_id):
    """Check if article can be sent (max 2 times)"""
    counts = load_json(SENT_COUNT_FILE)
    return counts.get(article_id, 0) < 2

def increment_sent_count(article_id):
    """Track sends"""
    counts = load_json(SENT_COUNT_FILE)
    counts[article_id] = counts.get(article_id, 0) + 1
    SENT_COUNT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(SENT_COUNT_FILE, 'w') as f:
        json.dump(counts, f, indent=2)

def generate_reddit_html():
    """Generate Reddit intelligence section"""
    try:
        # Try both possible Reddit data files
        REDDIT_FILES = [
            Path.home() / ".openclaw" / "workspace" / "config" / "reddit-competitive-intel.json",
            Path.home() / ".openclaw" / "workspace" / "config" / "reddit-intelligence.json"
        ]
        
        data = None
        for reddit_file in REDDIT_FILES:
            if reddit_file.exists():
                with open(reddit_file) as f:
                    data = json.load(f)
                break
        
        if not data:
            return '<!-- No Reddit data -->'
        
        # Handle different data structures
        all_mentions = []
        cutoff = datetime.now() - timedelta(days=30)
        
        def is_recent(entry):
            """Check if entry is within 30 days"""
            date_field = entry.get('created', entry.get('created_utc', entry.get('date', entry.get('found_at', ''))))
            if not date_field:
                return True  # Include if no date
            try:
                if isinstance(date_field, (int, float)):
                    dt = datetime.fromtimestamp(date_field)
                else:
                    dt = datetime.fromisoformat(str(date_field).replace('Z', '+00:00').replace('+00:00', ''))
                return dt >= cutoff
            except:
                return True  # Include if can't parse
        
        # Structure 1: {company: {mentions: [...]}}
        if isinstance(data, dict) and any(isinstance(v, dict) for v in data.values()):
            companies = ['Progyny', 'Maven', 'Carrot', 'Kindbody']
            for company in companies:
                company_data = data.get(company, {})
                if isinstance(company_data, dict):
                    mentions = company_data.get('mentions', [])
                    for m in mentions[:3]:
                        if is_recent(m):
                            m['company'] = company
                            all_mentions.append(m)
        
        # Structure 2: {posts: [...]}
        elif isinstance(data, dict) and 'posts' in data:
            posts = data.get('posts', [])
            for post in posts[:10]:
                if is_recent(post):
                    post['company'] = post.get('company', 'General')
                    all_mentions.append(post)
        
        # Structure 3: Direct list
        elif isinstance(data, list):
            for post in data[:10]:
                if isinstance(post, dict) and is_recent(post):
                    post['company'] = post.get('company', 'General')
                    all_mentions.append(post)
        
        if not all_mentions:
            # Return empty section with message instead of comment
            return '''
        <div class="section">
            <h2>🔍 Reddit Intelligence</h2>
            <p style="font-size: 13px; color: #666;">No Reddit discussions found in the last 30 days.</p>
        </div>
'''
        
        html = '''
        <div class="section">
            <h2>🔍 Reddit Intelligence</h2>
            <p style="font-size: 13px; color: #666; margin-bottom: 15px;">Community discussions and sentiment</p>
'''
        
        for mention in all_mentions[:10]:  # Top 10 total
            title = mention.get('title', 'No title')
            subreddit = mention.get('subreddit', mention.get('source', 'Unknown'))
            score = mention.get('score', mention.get('upvotes', 0))
            url = mention.get('url', mention.get('permalink', '#'))
            company = mention.get('company', '')
            
            html += f'''
            <div class="mention" style="margin-bottom: 12px; padding: 10px; background: #f8fafc; border-radius: 6px;">
                <div style="font-size: 13px; font-weight: 500; margin-bottom: 4px;">
                    <span style="background: #e5e7eb; padding: 2px 6px; border-radius: 4px; font-size: 11px; margin-right: 8px;">{company}</span>
                    <a href="{url}" style="color: #1a1a1a; text-decoration: none;">{title[:80]}...</a>
                </div>
                <div style="font-size: 12px; color: #666;">r/{subreddit} • ⬆️ {score}</div>
            </div>
'''
        
        html += '</div>'
        return html
    except Exception as e:
        return f'<!-- Reddit error: {e} -->'

def generate_linkedin_html():
    """Generate executive web mentions section (placeholder for proper LinkedIn scraping)"""
    try:
        LINKEDIN_FILE = Path.home() / ".openclaw" / "workspace" / "config" / "linkedin-updates.json"
        if not LINKEDIN_FILE.exists():
            return '<!-- No executive data -->'
        
        with open(LINKEDIN_FILE) as f:
            data = json.load(f)
        
        # Handle both list format and dict with posts key
        if isinstance(data, list):
            updates = data
        else:
            updates = data.get('posts', []) or data.get('updates', [])
        
        if not updates:
            return '''
        <div class="section">
            <h2>💼 Executive Web Mentions</h2>
            <p style="font-size: 13px; color: #666;">No recent executive mentions found.</p>
            <p style="font-size: 11px; color: #999; margin-top: 10px;"><em>Note: Proper LinkedIn post scraping with dates requires browser automation — on todo list.</em></p>
        </div>
'''
        
        html = '''
        <div class="section">
            <h2>💼 Executive Web Mentions</h2>
            <p style="font-size: 13px; color: #666; margin-bottom: 15px;">Recent web mentions of monitored executives</p>
'''
        
        for update in updates[:5]:  # Top 5 updates
            if not isinstance(update, dict):
                continue
            author = update.get('executive', update.get('author', 'Unknown'))
            company = update.get('company', '')
            content = update.get('description', update.get('content', ''))[:200]
            url = update.get('link', update.get('url', '#'))
            source = 'LinkedIn' if 'linkedin.com' in url else 'Web'
            
            html += f'''
            <div class="mention" style="margin-bottom: 15px; padding: 12px; background: #f8fafc; border-radius: 6px;">
                <div style="font-weight: 600; font-size: 14px;">{author}</div>
                <div style="font-size: 12px; color: #666; margin-bottom: 5px;">{company} • Source: {source}</div>
                <div style="font-size: 13px; color: #444; margin-bottom: 8px;">{content}...</div>
                <a href="{url}" style="font-size: 12px; color: #2563eb;">View →</a>
            </div>
'''
        
        html += '''
            <p style="font-size: 11px; color: #999; margin-top: 15px; padding-top: 10px; border-top: 1px solid #e5e7eb;">
                <em>Note: These are web search results mentioning executives. Proper LinkedIn post scraping with dates requires browser automation — on todo list.</em>
            </p>
        </div>'''
        return html
    except Exception as e:
        return f'<!-- Executive mentions error: {e} -->'

def generate_glassdoor_html():
    """Generate Glassdoor satisfaction table"""
    try:
        import sys
        sys.path.insert(0, '/home/ubuntu/.openclaw/workspace/scripts')
        from glassdoor_fetcher import load_existing
        data = load_existing()
        
        if not data:
            return '<!-- No Glassdoor data -->'
        
        html = '''
        <div class="section">
            <h2>🏢 Employee Satisfaction (Glassdoor)</h2>
            <table style="width:100%; border-collapse: collapse; font-size: 13px;">
                <tr style="background: #1e40af; color: white;">
                    <th style="padding: 10px; text-align: left;">Company</th>
                    <th style="padding: 10px; text-align: center;">Rating</th>
                    <th style="padding: 10px; text-align: center;">Reviews</th>
                    <th style="padding: 10px; text-align: center;">Recommend</th>
                    <th style="padding: 10px; text-align: center;">CEO Approval</th>
                </tr>
'''
        
        companies = ['Progyny', 'Maven Clinic', 'Carrot Fertility', 'Kindbody', 'WIN Fertility']
        for i, company in enumerate(companies):
            info = data.get(company, {})
            if not info:
                continue
            
            rating = info.get('overall_rating', 'N/A')
            reviews = info.get('total_reviews', 'N/A')
            recommend = info.get('recommend_to_friend', 'N/A')
            ceo = info.get('approve_of_ceo', 'N/A')
            
            # Color code ratings
            try:
                rating_val = float(rating) if rating != 'N/A' else 0
                rating_color = '#16a34a' if rating_val >= 4.0 else '#ea580c' if rating_val >= 3.0 else '#dc2626'
            except:
                rating_color = '#666'
            
            bg = '#f8fafc' if i % 2 == 0 else 'white'
            html += f'''
                <tr style="background: {bg};">
                    <td style="padding: 10px; border-bottom: 1px solid #e5e7eb; font-weight: 500;">{company}</td>
                    <td style="padding: 10px; text-align: center; border-bottom: 1px solid #e5e7eb; color: {rating_color}; font-weight: 600;">{rating}</td>
                    <td style="padding: 10px; text-align: center; border-bottom: 1px solid #e5e7eb;">{reviews}</td>
                    <td style="padding: 10px; text-align: center; border-bottom: 1px solid #e5e7eb;">{recommend}</td>
                    <td style="padding: 10px; text-align: center; border-bottom: 1px solid #e5e7eb;">{ceo}</td>
                </tr>
'''
        
        html += '</table></div>'
        return html
    except Exception as e:
        return f'<!-- Glassdoor error: {e} -->'

def is_article_relevant(article):
    """Check if article is relevant to FemTech/Women's Health"""
    title = article.get('title', '').lower()
    summary = article.get('summary', '').lower()
    combined = title + ' ' + summary
    
    relevant_terms = [
        'femtech', 'women\'s health', 'womens health', 'female health',
        'fertility', 'infertility', 'ivf', 'egg freezing', 'pregnancy',
        'maternity', 'menopause', 'menstrual', 'pcos', 'endometriosis',
        'maternal', 'family building', 'progyny', 'maven', 'carrot', 'kindbody',
        'surrogacy', 'reproductive', 'gynecology', 'obgyn', 'doula', 'midwife',
    ]
    
    for term in relevant_terms:
        if term in combined:
            return True
    
    # Exclude generic terms unless women-specific
    exclude_generic = ['recruitment', 'staffing', 'hiring', 'job', 'behavioral health']
    for term in exclude_generic:
        if term in combined and not any(w in combined for w in ['women', 'female', 'maternal', 'fertility']):
            return False
    
    return True

def get_company_from_article(article):
    """Determine company from article content"""
    combined = (article.get('title', '') + ' ' + article.get('summary', '')).lower()
    
    companies = {
        'Maven': ['maven', 'maven clinic'],
        'Carrot': ['carrot', 'carrot fertility'],
        'Kindbody': ['kindbody'],
        'Progyny': ['progyny', 'pgny'],
        'Future Family': ['future family'],
        'Sword Health': ['sword health', 'sword'],
        'Oura': ['oura'],
        'Flo Health': ['flo health', 'flo'],
    }
    
    for company, terms in companies.items():
        if any(term in combined for term in terms):
            return company
    
    return 'General'

def generate_detailed_summary(articles):
    """Generate detailed 2-3 sentence summary for a set of articles"""
    if not articles:
        return ""
    
    # Group by company
    by_company = {}
    for a in articles:
        company = get_company_from_article(a)
        by_company[company] = by_company.get(company, [])
        by_company[company].append(a)
    
    # Identify key themes
    all_text = ' '.join([a.get('title','') + ' ' + a.get('summary','') for a in articles]).lower()
    
    themes = []
    
    # AI theme
    ai_keywords = ['ai', 'artificial intelligence', 'machine learning', 'platform', 'algorithm', 'predictive']
    if any(k in all_text for k in ai_keywords):
        ai_companies = [c for c, arts in by_company.items() if any(any(k in (a.get('title','')+a.get('summary','')).lower() for k in ai_keywords) for a in arts)]
        if ai_companies:
            themes.append(f"AI and machine learning innovation from {', '.join(ai_companies[:3])}, signaling a competitive race to automate care coordination and improve patient outcomes through predictive analytics.")
    
    # Funding theme
    if any(k in all_text for k in ['funding', 'raises', 'million', 'investment', 'series']):
        funded = [a for a in articles if any(k in (a.get('title','')+a.get('summary','')).lower() for k in ['funding', 'raises', 'million'])]
        if funded:
            companies_funded = list(set([get_company_from_article(a) for a in funded]))[:3]
            themes.append(f"Significant capital deployment into the sector with fresh funding rounds from {', '.join(companies_funded)}, indicating investor confidence and likely acceleration of market expansion efforts.")
    
    # Partnership theme
    if any(k in all_text for k in ['partnership', 'partners', 'collaboration', 'signs', 'deal']):
        partnered = [a for a in articles if any(k in (a.get('title','')+a.get('summary','')).lower() for k in ['partnership', 'partners', 'collaboration'])]
        if partnered:
            companies_partnered = list(set([get_company_from_article(a) for a in partnered]))[:3]
            themes.append(f"Strategic partnership activity from {', '.join(companies_partnered)}, suggesting market consolidation and expansion into new employer segments or geographic markets.")
    
    # Product launch theme
    if any(k in all_text for k in ['launch', 'introduces', 'unveils', 'new product', 'new service']):
        launched = [a for a in articles if any(k in (a.get('title','')+a.get('summary','')).lower() for k in ['launch', 'introduces', 'unveils'])]
        if launched:
            companies_launched = list(set([get_company_from_article(a) for a in launched]))[:3]
            themes.append(f"New product and service launches from {', '.join(companies_launched)}, representing competitive positioning moves to capture market share and differentiate offerings.")
    
    # Market expansion
    if any(k in all_text for k in ['expands', 'expansion', 'new market', 'international', 'global']):
        expanded = [a for a in articles if any(k in (a.get('title','')+a.get('summary','')).lower() for k in ['expands', 'expansion', 'new market'])]
        if expanded:
            companies_expanded = list(set([get_company_from_article(a) for a in expanded]))[:3]
            themes.append(f"Geographic and market expansion efforts by {', '.join(companies_expanded)}, indicating growth ambitions and potential competitive pressure in new territories.")
    
    # Regulatory/Policy
    if any(k in all_text for k in ['legislation', 'policy', 'regulation', 'mandate', 'coverage', 'benefit']):
        themes.append("Regulatory and policy developments that could impact market dynamics, coverage requirements, and competitive positioning across the sector.")
    
    if themes:
        return ' '.join(themes[:3])  # Max 3 themes
    
    return f"Competitive activity observed across {len(by_company)} companies with {len(articles)} total signals in the reporting period."

def generate_executive_summary(critical, high, medium, progyny_mentions):
    """Generate comprehensive executive summary"""
    all_articles = critical + high + medium
    
    if not all_articles and not progyny_mentions:
        return "No significant competitive activity detected in the last 30 days."
    
    summary_parts = []
    
    # Overall landscape summary
    if all_articles:
        detailed = generate_detailed_summary(all_articles)
        summary_parts.append(detailed)
    
    # Volume context
    companies = {}
    for article in all_articles:
        company = get_company_from_article(article)
        companies[company] = companies.get(company, 0) + 1
    
    top_companies = sorted(companies.items(), key=lambda x: x[1], reverse=True)[:3]
    if top_companies:
        company_str = ', '.join([f"{c} ({n})" for c, n in top_companies])
        summary_parts.append(f"Most active competitors: {company_str}.")
    
    # Progyny context
    if progyny_mentions:
        summary_parts.append(f"Progyny tracked in {len(progyny_mentions)} news/social mentions, indicating sustained market visibility and ongoing competitive interest.")
    
    return ' '.join(summary_parts)

def generate_html_email():
    """Generate competitive intelligence email"""
    
    # Load data
    articles_data = load_json(ARTICLES_FILE)
    progyny_data = load_json(PROGYNY_FILE)
    reddit_data = load_json(REDDIT_FILE)
    
    articles_list = articles_data if isinstance(articles_data, list) else articles_data.get('articles', [])
    
    # Filter articles
    filtered = []
    for article in articles_list:
        if not isinstance(article, dict):
            continue
        if not is_article_relevant(article):
            continue
        if not is_within_30_days(article):
            continue
        if not can_send_article(article.get('id', '')):
            continue
        
        filtered.append(article)
        increment_sent_count(article.get('id', ''))
    
    # Categorize
    critical = [a for a in filtered if a.get('priority') == 'critical'][:5]
    high = [a for a in filtered if a.get('priority') == 'high'][:5]
    medium = [a for a in filtered if a.get('priority') == 'medium'][:10]
    
    # Process Progyny mentions with date filtering
    progyny_mentions_raw = progyny_data.get('mentions', [])
    progyny_mentions = []
    for m in progyny_mentions_raw:
        if is_within_30_days(m):
            progyny_mentions.append(m)
    progyny_mentions = progyny_mentions[:5]
    
    # Generate executive summary
    exec_summary = generate_executive_summary(critical, high, medium, progyny_mentions)
    
    today = datetime.now().strftime('%A, %B %d, %Y')
    
    html = f"""<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; 
               line-height: 1.5; color: #1a1a1a; max-width: 700px; margin: 0 auto; background: #fafafa; }}
        .container {{ background: white; padding: 40px; }}
        
        .header {{ background: linear-gradient(135deg, #1e40af, #3b82f6); color: white; 
                   padding: 30px; margin: -40px -40px 30px -40px; }}
        .header h1 {{ margin: 0; font-size: 24px; font-weight: 600; }}
        .header p {{ margin: 8px 0 0 0; opacity: 0.9; font-size: 14px; }}
        
        .exec-summary {{ background: #f0f7ff; border-left: 4px solid #1e40af; 
                        padding: 20px; margin: 25px 0; }}
        .exec-summary h2 {{ margin: 0 0 12px 0; font-size: 14px; text-transform: uppercase; 
                           letter-spacing: 1px; color: #1e40af; }}
        .exec-summary p {{ margin: 0; font-size: 15px; line-height: 1.6; }}
        
        .stats {{ display: flex; gap: 20px; margin: 20px 0; justify-content: center; }}
        .stat {{ text-align: center; background: #f8fafc; padding: 15px 25px; border-radius: 8px; }}
        .stat-number {{ font-size: 28px; font-weight: 600; color: #1e40af; }}
        .stat-label {{ font-size: 11px; color: #666; text-transform: uppercase; }}
        
        .section {{ margin: 30px 0; }}
        .section h2 {{ font-size: 16px; color: #1a1a1a; border-bottom: 2px solid #e5e7eb; 
                      padding-bottom: 8px; margin-bottom: 15px; }}
        
        .article {{ padding: 15px 0; border-bottom: 1px solid #f0f0f0; }}
        .article:last-child {{ border-bottom: none; }}
        .article-header {{ display: flex; align-items: center; margin-bottom: 8px; }}
        .company {{ font-size: 11px; font-weight: 600; text-transform: uppercase; 
                   color: #666; letter-spacing: 0.5px; }}
        .priority {{ margin-left: auto; font-size: 11px; padding: 2px 8px; border-radius: 4px; }}
        .priority-critical {{ background: #fef2f2; color: #dc2626; }}
        .priority-high {{ background: #fff7ed; color: #ea580c; }}
        .priority-medium {{ background: #fefce8; color: #ca8a04; }}
        
        .title {{ font-weight: 600; font-size: 15px; margin-bottom: 4px; }}
        .title a {{ color: #1a1a1a; text-decoration: none; }}
        .title a:hover {{ text-decoration: underline; }}
        .meta {{ font-size: 12px; color: #999; margin-bottom: 8px; }}
        .summary {{ font-size: 13px; color: #555; }}
        .why-matters {{ font-size: 12px; color: #444; background: #f8f9fa; 
                       padding: 10px 12px; border-radius: 4px; margin-top: 8px; }}
        
        .progyny-section {{ background: #f8fafc; padding: 20px; margin: 20px 0; 
                           border-radius: 8px; border: 1px solid #e5e7eb; }}
        .mention {{ padding: 10px 0; border-bottom: 1px solid #e5e7eb; }}
        .mention:last-child {{ border-bottom: none; }}
        .mention-title {{ font-weight: 500; font-size: 13px; }}
        .mention-title a {{ color: #1e40af; text-decoration: none; }}
        .mention-meta {{ font-size: 11px; color: #999; }}
        
        .footer {{ margin-top: 40px; padding-top: 20px; border-top: 1px solid #e5e7eb; 
                  text-align: center; font-size: 12px; color: #999; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🏛️ Competitive Intelligence Report</h1>
            <p>{today} | 30-Day Window | FemTech & Women's Health Focus</p>
        </div>
        
        <div class="exec-summary">
            <h2>📊 Executive Summary</h2>
            <p>{exec_summary}</p>
        </div>
        
        <div class="stats">
            <div class="stat">
                <div class="stat-number">{len(critical)}</div>
                <div class="stat-label">Critical</div>
            </div>
            <div class="stat">
                <div class="stat-number">{len(high)}</div>
                <div class="stat-label">High</div>
            </div>
            <div class="stat">
                <div class="stat-number">{len(medium)}</div>
                <div class="stat-label">Medium</div>
            </div>
            <div class="stat">
                <div class="stat-number">{len(progyny_mentions)}</div>
                <div class="stat-label">Progyny Mentions</div>
            </div>
        </div>
"""
    
    # Critical Signals
    if critical:
        html += '<div class="section"><h2>🔴 Critical Signals</h2>'
        for article in critical:
            company = get_company_from_article(article)
            date = format_article_date(article)
            html += f'''
            <div class="article">
                <div class="article-header">
                    <span class="company">{company}</span>
                    <span class="priority priority-critical">Critical</span>
                </div>
                <div class="title"><a href="{article.get('link', '#')}">{article.get('title', '')}</a></div>
                <div class="meta">{article.get('source', 'Unknown')} • {date}</div>
                <div class="summary">{article.get('summary', '')[:200]}...</div>
            </div>
'''
        html += '</div>'
    
    # High Priority
    if high:
        html += '<div class="section"><h2>🟠 High Priority</h2>'
        for article in high:
            company = get_company_from_article(article)
            date = format_article_date(article)
            html += f'''
            <div class="article">
                <div class="article-header">
                    <span class="company">{company}</span>
                    <span class="priority priority-high">High</span>
                </div>
                <div class="title"><a href="{article.get('link', '#')}">{article.get('title', '')}</a></div>
                <div class="meta">{article.get('source', 'Unknown')} • {date}</div>
                <div class="summary">{article.get('summary', '')[:200]}...</div>
            </div>
'''
        html += '</div>'
    
    # Medium Priority
    if medium:
        html += '<div class="section"><h2>🟡 Medium Priority</h2>'
        for article in medium:
            company = get_company_from_article(article)
            date = format_article_date(article)
            html += f'''
            <div class="article">
                <div class="article-header">
                    <span class="company">{company}</span>
                    <span class="priority priority-medium">Medium</span>
                </div>
                <div class="title"><a href="{article.get('link', '#')}">{article.get('title', '')}</a></div>
                <div class="meta">{article.get('source', 'Unknown')} • {date}</div>
            </div>
'''
        html += '</div>'
    
    # Glassdoor Section
    try:
        glassdoor_html = generate_glassdoor_html()
        html += glassdoor_html
    except Exception as e:
        html += f'<!-- Glassdoor error: {e} -->'
    
    # LinkedIn Executive Section
    try:
        linkedin_html = generate_linkedin_html()
        html += linkedin_html
    except Exception as e:
        html += f'<!-- LinkedIn error: {e} -->'
    
    # Reddit Intelligence Section
    try:
        reddit_html = generate_reddit_html()
        html += reddit_html
    except Exception as e:
        html += f'<!-- Reddit error: {e} -->'
    
    # Progyny Section
    if progyny_mentions:
        html += '''
        <div class="section">
            <h2>📊 Progyny Market Mentions</h2>
            <div class="progyny-section">
'''
        for mention in progyny_mentions:
            date = format_article_date(mention)
            html += f'''
                <div class="mention">
                    <div class="mention-title"><a href="{mention.get('url', '#')}">{mention.get('title', '')}</a></div>
                    <div class="mention-meta">{mention.get('source', 'Unknown')} • {date}</div>
                </div>
'''
        html += '</div></div>'
    
    html += '''
        <div class="footer">
            <p>Competitive Intelligence System • 30-day filter • Max 2 sends per article</p>
            <p>Sources linked for validation</p>
        </div>
    </div>
</body>
</html>
'''
    
    with open(EMAIL_OUTPUT, 'w') as f:
        f.write(html)
    
    print(f"✅ Email generated: {EMAIL_OUTPUT}")
    print(f"   Critical: {len(critical)} | High: {len(high)} | Medium: {len(medium)}")
    print(f"   Progyny mentions: {len(progyny_mentions)}")
    
    return html

if __name__ == "__main__":
    generate_html_email()
