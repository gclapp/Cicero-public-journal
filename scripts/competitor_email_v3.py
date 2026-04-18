#!/usr/bin/env python3
"""
Competitive Intelligence Email Generator v3
- Executive summary at top
- Better prioritization (Critical/High/Medium)
- "Why This Matters" context for each article
- Trend analysis
- Fixed deduplication tracking
"""

import json
import re
from datetime import datetime, timedelta
from pathlib import Path
from email.utils import parsedate_to_datetime

ARTICLES_FILE = Path.home() / ".openclaw" / "workspace" / "config" / "competitor-articles-v3.json"
LINKEDIN_FILE = Path.home() / ".openclaw" / "workspace" / "config" / "linkedin-updates.json"
SENT_COUNT_FILE = Path.home() / ".openclaw" / "workspace" / "config" / "competitor-sent-count-v3.json"
EMAIL_OUTPUT = Path.home() / ".openclaw" / "workspace" / "config" / "competitor-email-v3.html"

def load_json(filepath):
    if filepath.exists():
        with open(filepath) as f:
            return json.load(f)
    return {}

def parse_article_date(article):
    """Get best date for article"""
    # Try published field
    pub = article.get('published', '')
    if pub:
        dt = parse_date_string(pub)
        if dt:
            return dt
    
    # Fallback to found_at
    found = article.get('found_at', '')
    if found:
        try:
            return datetime.fromisoformat(found.replace('Z', '+00:00').replace('+00:00', ''))
        except:
            pass
    
    return datetime.now()

def parse_date_string(date_str):
    """Parse various date formats"""
    if not date_str:
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
            return datetime.strptime(date_str[:len(fmt)+10], fmt)
        except:
            continue
    
    try:
        return datetime.fromisoformat(date_str.replace('Z', '+00:00').replace('+00:00', ''))
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
    # Use pre-formatted date if available
    if 'published_formatted' in article:
        return article['published_formatted']
    
    dt = parse_article_date(article)
    if dt:
        return dt.strftime('%b %d, %Y')
    return 'Unknown date'

def get_company_from_article(article):
    """Determine company from article content"""
    if 'company' in article:
        return article['company']
    
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

def get_company_logo_url(company_name):
    """Get logo URL for a company"""
    company_domains = {
        'Maven': 'mavenclinic.com',
        'Carrot': 'carrotfertility.com',
        'KindBody': 'kindbody.com',
        'WIN Fertility': 'winfertility.com',
        'Pomelo Health': 'pomelohealth.com',
        'Midi Health': 'midi-health.com',
        'Evernow': 'evernow.com',
        'Pacify': 'pacify.com',
        'Progyny': 'progyny.com',
        'Oura': 'ouraring.com',
        'Flo Health': 'flo.health',
        'General': 'example.com'
    }
    
    domain = company_domains.get(company_name, f"{company_name.lower().replace(' ', '')}.com")
    return f"https://www.google.com/s2/favicons?domain={domain}&sz=64"

def analyze_trends(articles):
    """Analyze articles for trend patterns"""
    if not articles:
        return "No significant competitive activity detected in the last 30 days."
    
    # Count by theme
    ai_mentions = sum(1 for a in articles if any(k in (a.get('title','') + a.get('summary','')).lower() 
                                                  for k in ['ai', 'artificial intelligence', 'machine learning']))
    funding_mentions = sum(1 for a in articles if any(k in (a.get('title','') + a.get('summary','')).lower() 
                                                      for k in ['funding', 'raises', 'series', 'investment']))
    partnership_mentions = sum(1 for a in articles if any(k in (a.get('title','') + a.get('summary','')).lower() 
                                                          for k in ['partnership', 'partners', 'collaboration']))
    
    # Count by company
    company_counts = {}
    for a in articles:
        company = get_company_from_article(a)
        company_counts[company] = company_counts.get(company, 0) + 1
    
    # Build trend analysis
    trends = []
    
    if ai_mentions >= 2:
        trends.append(f"🤖 <strong>AI Investment:</strong> {ai_mentions} AI-related signals detected. Competitors are rapidly investing in automation capabilities.")
    
    if funding_mentions >= 2:
        trends.append(f"💰 <strong>Capital Deployment:</strong> {funding_mentions} funding events indicate strong investor confidence in the sector.")
    
    if partnership_mentions >= 2:
        trends.append(f"🤝 <strong>Partnership Activity:</strong> {partnership_mentions} new partnerships suggest ecosystem-building as a core strategy.")
    
    # Top companies
    top_companies = sorted(company_counts.items(), key=lambda x: x[1], reverse=True)[:3]
    if top_companies and top_companies[0][0] != 'General':
        company_str = ', '.join([f"{c} ({n})" for c, n in top_companies if c != 'General'])
        if company_str:
            trends.append(f"📊 <strong>Most Active:</strong> {company_str}")
    
    if not trends:
        return f"Market activity distributed across {len(company_counts)} companies. No dominant trend emerging."
    
    return " ".join(trends)

def generate_glassdoor_html():
    """Generate Glassdoor satisfaction table"""
    try:
        import sys
        sys.path.insert(0, '/home/ubuntu/.openclaw/workspace/scripts')
        from glassdoor_fetcher import load_existing
        data = load_existing()
        
        if not data:
            return ''
        
        html = '''
    <div class="section">
        <h2>🏢 Employee Satisfaction (Glassdoor)</h2>
        <table style="width:100%; border-collapse: collapse; font-size: 13px; margin-top: 15px;">
            <tr style="background: #1e40af; color: white;">
                <th style="padding: 12px; text-align: left;">Company</th>
                <th style="padding: 12px; text-align: center;">Rating</th>
                <th style="padding: 12px; text-align: center;">Reviews</th>
                <th style="padding: 12px; text-align: center;">Recommend</th>
                <th style="padding: 12px; text-align: center;">CEO Approval</th>
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
                <td style="padding: 12px; border-bottom: 1px solid #e5e7eb; font-weight: 500;">{company}</td>
                <td style="padding: 12px; text-align: center; border-bottom: 1px solid #e5e7eb; color: {rating_color}; font-weight: 600;">{rating}</td>
                <td style="padding: 12px; text-align: center; border-bottom: 1px solid #e5e7eb;">{reviews}</td>
                <td style="padding: 12px; text-align: center; border-bottom: 1px solid #e5e7eb;">{recommend}</td>
                <td style="padding: 12px; text-align: center; border-bottom: 1px solid #e5e7eb;">{ceo}</td>
            </tr>
'''
        
        html += '</table></div>'
        return html
    except Exception as e:
        return ''

def generate_linkedin_html():
    """Generate LinkedIn/job changes section"""
    try:
        LINKEDIN_FILE = Path.home() / ".openclaw" / "workspace" / "config" / "linkedin-updates.json"
        if not LINKEDIN_FILE.exists():
            return ''
        
        with open(LINKEDIN_FILE) as f:
            data = json.load(f)
        
        if isinstance(data, list):
            updates = data
        else:
            updates = data.get('posts', []) or data.get('updates', [])
        
        # Filter to recent
        cutoff = datetime.now() - timedelta(days=30)
        recent_updates = []
        for u in updates:
            found_at = u.get('found_at', '')
            if found_at:
                try:
                    dt = datetime.fromisoformat(found_at.replace('Z', '+00:00').replace('+00:00', ''))
                    if dt >= cutoff:
                        recent_updates.append(u)
                except:
                    recent_updates.append(u)
            else:
                recent_updates.append(u)
        
        if not recent_updates:
            return ''
        
        html = '''
    <div class="section">
        <h2>💼 Executive & Job Changes</h2>
        <p style="font-size: 13px; color: #666; margin-bottom: 15px;">Recent leadership movements and executive updates</p>
'''
        
        for update in recent_updates[:5]:
            if not isinstance(update, dict):
                continue
            
            company = update.get('company', 'Unknown')
            title = update.get('title', update.get('description', 'No title'))[:100]
            url = update.get('link', update.get('url', '#'))
            update_type = update.get('type', 'update')
            
            badge_color = '#16a34a' if update_type == 'job_change' else '#2563eb'
            badge_text = 'Job Change' if update_type == 'job_change' else 'Executive'
            
            html += f'''
        <div class="mention" style="margin-bottom: 12px; padding: 12px; background: #f8fafc; border-radius: 6px; border-left: 3px solid {badge_color};">
            <div style="font-size: 12px; color: {badge_color}; font-weight: 600; margin-bottom: 4px;">{badge_text} • {company}</div>
            <div style="font-size: 13px; font-weight: 500; margin-bottom: 4px;"><a href="{url}" style="color: #1a1a1a; text-decoration: none;">{title}...</a></div>
            <div style="font-size: 11px; color: #666;">👔 Leadership changes signal potential strategy shifts</div>
        </div>
'''
        
        html += '</div>'
        return html
    except Exception as e:
        return ''

def generate_reddit_html():
    """Generate Reddit intelligence section"""
    try:
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
            return ''
        
        all_mentions = []
        cutoff = datetime.now() - timedelta(days=30)
        
        # Handle different data structures
        if isinstance(data, dict):
            companies = ['Progyny', 'Maven', 'Carrot', 'Kindbody']
            for company in companies:
                company_data = data.get(company, {})
                if isinstance(company_data, dict):
                    mentions = company_data.get('mentions', [])
                    for m in mentions[:3]:
                        m['company'] = company
                        all_mentions.append(m)
        elif isinstance(data, list):
            all_mentions = data[:10]
        
        if not all_mentions:
            return ''
        
        html = '''
    <div class="section">
        <h2>🔍 Reddit Intelligence</h2>
        <p style="font-size: 13px; color: #666; margin-bottom: 15px;">Community discussions and sentiment</p>
'''
        
        for mention in all_mentions[:5]:
            title = mention.get('title', 'No title')[:80]
            subreddit = mention.get('subreddit', mention.get('source', 'Unknown'))
            score = mention.get('score', mention.get('upvotes', 0))
            url = mention.get('url', mention.get('permalink', '#'))
            company = mention.get('company', '')
            
            html += f'''
        <div class="mention" style="margin-bottom: 10px; padding: 10px; background: #f8fafc; border-radius: 6px;">
            <div style="font-size: 12px; font-weight: 500; margin-bottom: 3px;">
                <span style="background: #e5e7eb; padding: 2px 6px; border-radius: 4px; font-size: 10px; margin-right: 8px;">{company}</span>
                <a href="{url}" style="color: #1a1a1a; text-decoration: none;">{title}...</a>
            </div>
            <div style="font-size: 11px; color: #666;">r/{subreddit} • ⬆️ {score}</div>
        </div>
'''
        
        html += '</div>'
        return html
    except Exception as e:
        return ''

def generate_html_email():
    """Generate competitive intelligence email"""
    
    # Load data
    articles_data = load_json(ARTICLES_FILE)
    
    if isinstance(articles_data, list):
        articles_list = articles_data
    else:
        articles_list = articles_data.get('articles', [])
    
    # Filter to recent and relevant
    filtered = []
    for article in articles_list:
        if not isinstance(article, dict):
            continue
        if not is_within_30_days(article):
            continue
        filtered.append(article)
    
    # Categorize
    critical = [a for a in filtered if a.get('priority') == 'critical'][:5]
    high = [a for a in filtered if a.get('priority') == 'high'][:5]
    medium = [a for a in filtered if a.get('priority') == 'medium'][:10]
    
    # Generate trend analysis
    trend_summary = analyze_trends(filtered)
    
    today = datetime.now().strftime('%A, %B %d, %Y')
    
    html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; 
               line-height: 1.5; color: #1a1a1a; max-width: 700px; margin: 0 auto; background: #fafafa; }}
        .container {{ background: white; padding: 40px; }}
        
        .header {{ background: linear-gradient(135deg, #1e40af, #3b82f6); color: white; 
                   padding: 30px; margin: -40px -40px 30px -40px; }}
        .header h1 {{ margin: 0; font-size: 24px; font-weight: 600; }}
        .header p {{ margin: 8px 0 0 0; opacity: 0.9; font-size: 14px; }}
        
        .exec-summary {{ background: #f0f7ff; border-left: 4px solid #1e40af; 
                        padding: 20px; margin: 25px 0; border-radius: 0 8px 8px 0; }}
        .exec-summary h2 {{ margin: 0 0 12px 0; font-size: 14px; text-transform: uppercase; 
                           letter-spacing: 1px; color: #1e40af; }}
        .exec-summary p {{ margin: 0; font-size: 14px; line-height: 1.6; }}
        
        .stats {{ display: flex; gap: 15px; margin: 20px 0; justify-content: center; flex-wrap: wrap; }}
        .stat {{ text-align: center; background: #f8fafc; padding: 15px 25px; border-radius: 8px; min-width: 80px; }}
        .stat-number {{ font-size: 28px; font-weight: 600; color: #1e40af; }}
        .stat-label {{ font-size: 11px; color: #666; text-transform: uppercase; }}
        
        .section {{ margin: 30px 0; }}
        .section h2 {{ font-size: 16px; color: #1a1a1a; border-bottom: 2px solid #e5e7eb; 
                      padding-bottom: 8px; margin-bottom: 15px; }}
        
        .article {{ padding: 18px; margin-bottom: 15px; border-radius: 8px; border-left: 4px solid; }}
        .article-critical {{ background: #fef2f2; border-left-color: #dc2626; }}
        .article-high {{ background: #fff7ed; border-left-color: #ea580c; }}
        .article-medium {{ background: #fefce8; border-left-color: #ca8a04; }}
        
        .article-header {{ display: flex; align-items: center; margin-bottom: 10px; flex-wrap: wrap; gap: 8px; }}
        .company-logo {{ width: 20px; height: 20px; border-radius: 4px; margin-right: 6px; }}
        .company {{ font-size: 11px; font-weight: 600; text-transform: uppercase; 
                   color: #666; letter-spacing: 0.5px; }}
        .priority {{ font-size: 10px; padding: 3px 10px; border-radius: 12px; font-weight: 600; }}
        .priority-critical {{ background: #dc2626; color: white; }}
        .priority-high {{ background: #ea580c; color: white; }}
        .priority-medium {{ background: #ca8a04; color: white; }}
        .category {{ font-size: 10px; padding: 3px 10px; border-radius: 12px; background: #e5e7eb; color: #666; }}
        
        .title {{ font-weight: 600; font-size: 15px; margin-bottom: 6px; line-height: 1.4; }}
        .title a {{ color: #1a1a1a; text-decoration: none; }}
        .title a:hover {{ text-decoration: underline; color: #1e40af; }}
        .meta {{ font-size: 12px; color: #999; margin-bottom: 10px; }}
        .summary {{ font-size: 13px; color: #555; margin-bottom: 10px; line-height: 1.5; }}
        .why-matters {{ font-size: 12px; color: #444; background: rgba(255,255,255,0.7); 
                       padding: 12px; border-radius: 6px; border-left: 3px solid #3b82f6; }}
        
        .footer {{ margin-top: 40px; padding-top: 20px; border-top: 1px solid #e5e7eb; 
                  text-align: center; font-size: 12px; color: #999; }}
        
        @media (max-width: 600px) {{
            .container {{ padding: 20px; }}
            .header {{ margin: -20px -20px 20px -20px; padding: 20px; }}
            .stats {{ flex-direction: column; }}
            .stat {{ width: 100%; }}
        }}
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
            <p>{trend_summary}</p>
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
                <div class="stat-number">{len(filtered)}</div>
                <div class="stat-label">Total Signals</div>
            </div>
        </div>
"""
    
    # Critical Signals
    if critical:
        html += '<div class="section"><h2>🔴 Critical Signals</h2>'
        for article in critical:
            company = get_company_from_article(article)
            logo_url = get_company_logo_url(company)
            date = format_article_date(article)
            why_matters = article.get('why_matters', '')
            
            html += f'''
        <div class="article article-critical">
            <div class="article-header">
                <img src="{logo_url}" alt="{company}" class="company-logo" onerror="this.style.display='none'">
                <span class="company">{company}</span>
                <span class="priority priority-critical">Critical</span>
                <span class="category">{article.get('category', 'general')}</span>
            </div>
            <div class="title"><a href="{article.get('link', '#')}">{article.get('title', '')}</a></div>
            <div class="meta">{article.get('source', 'Unknown')} • {date}</div>
            <div class="summary">{article.get('summary', '')[:200]}...</div>
            {f'<div class="why-matters">{why_matters}</div>' if why_matters else ''}
        </div>
'''
        html += '</div>'
    
    # High Priority
    if high:
        html += '<div class="section"><h2>🟠 High Priority</h2>'
        for article in high:
            company = get_company_from_article(article)
            logo_url = get_company_logo_url(company)
            date = format_article_date(article)
            why_matters = article.get('why_matters', '')
            
            html += f'''
        <div class="article article-high">
            <div class="article-header">
                <img src="{logo_url}" alt="{company}" class="company-logo" onerror="this.style.display='none'">
                <span class="company">{company}</span>
                <span class="priority priority-high">High</span>
                <span class="category">{article.get('category', 'general')}</span>
            </div>
            <div class="title"><a href="{article.get('link', '#')}">{article.get('title', '')}</a></div>
            <div class="meta">{article.get('source', 'Unknown')} • {date}</div>
            <div class="summary">{article.get('summary', '')[:200]}...</div>
            {f'<div class="why-matters">{why_matters}</div>' if why_matters else ''}
        </div>
'''
        html += '</div>'
    
    # Medium Priority
    if medium:
        html += '<div class="section"><h2>🟡 Medium Priority</h2>'
        for article in medium:
            company = get_company_from_article(article)
            logo_url = get_company_logo_url(company)
            date = format_article_date(article)
            why_matters = article.get('why_matters', '')
            
            html += f'''
        <div class="article article-medium">
            <div class="article-header">
                <img src="{logo_url}" alt="{company}" class="company-logo" onerror="this.style.display='none'">
                <span class="company">{company}</span>
                <span class="priority priority-medium">Medium</span>
                <span class="category">{article.get('category', 'general')}</span>
            </div>
            <div class="title"><a href="{article.get('link', '#')}">{article.get('title', '')}</a></div>
            <div class="meta">{article.get('source', 'Unknown')} • {date}</div>
            {f'<div class="why-matters">{why_matters}</div>' if why_matters else ''}
        </div>
'''
        html += '</div>'
    
    # Glassdoor Section
    glassdoor_html = generate_glassdoor_html()
    if glassdoor_html:
        html += glassdoor_html
    
    # LinkedIn Section
    linkedin_html = generate_linkedin_html()
    if linkedin_html:
        html += linkedin_html
    
    # Reddit Section
    reddit_html = generate_reddit_html()
    if reddit_html:
        html += reddit_html
    
    # No content message
    if not any([critical, high, medium]):
        html += '''
        <div class="section">
            <p style="text-align: center; color: #666; padding: 40px;">
                No new competitive signals found in the last 30 days.<br>
                <span style="font-size: 13px;">The system continues monitoring RSS feeds, web search, and LinkedIn.</span>
            </p>
        </div>
'''
    
    html += '''
        <div class="footer">
            <p>Competitive Intelligence System v3 | Strict deduplication | 30-day window</p>
            <p>Sources: Google Alerts, Brave Search, LinkedIn, Glassdoor, Reddit</p>
        </div>
    </div>
</body>
</html>
'''
    
    EMAIL_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with open(EMAIL_OUTPUT, 'w') as f:
        f.write(html)
    
    print(f"✅ Email generated: {EMAIL_OUTPUT}")
    print(f"   Critical: {len(critical)} | High: {len(high)} | Medium: {len(medium)}")
    
    return html

if __name__ == "__main__":
    generate_html_email()