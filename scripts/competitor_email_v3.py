#!/usr/bin/env python3
"""
Competitive Intelligence Email Generator v3
Clean, professional design with minimal colors
"""

import json
from datetime import datetime, timedelta
from pathlib import Path

ARTICLES_FILE = Path.home() / ".openclaw" / "workspace" / "config" / "competitor-articles-v2.json"
LINKEDIN_FILE = Path.home() / ".openclaw" / "workspace" / "config" / "linkedin-updates.json"
LINKEDIN_POSTS_FILE = Path.home() / ".openclaw" / "workspace" / "config" / "linkedin-executive-posts.json"
REDDIT_FILE = Path.home() / ".openclaw" / "workspace" / "config" / "reddit-competitive-intel.json"
PROGYNY_FILE = Path.home() / ".openclaw" / "workspace" / "config" / "progyny-sentiment.json"
EMAIL_OUTPUT = Path.home() / ".openclaw" / "workspace" / "config" / "competitor-email-v3.html"

def load_json(filepath):
    """Load JSON file"""
    if filepath.exists():
        with open(filepath) as f:
            return json.load(f)
    return {}

def get_company_logo_url(company_name):
    """Get logo URL for a company"""
    company_domains = {
        'Maven': 'mavenclinic.com',
        'Carrot': 'carrotfertility.com',
        'KindBody': 'kindbody.com',
        'WIN Fertility': 'winfertility.com',
        'Pomelo Health': 'pomelohealth.com',
        'Pomelo': 'pomelohealth.com',
        'Midi Health': 'midi-health.com',
        'Midi': 'midi-health.com',
        'Evernow': 'evernow.com',
        'Pacify': 'pacify.com',
        'Progyny': 'progyny.com'
    }
    
    domain = company_domains.get(company_name, f"{company_name.lower().replace(' ', '')}.com")
    return f"https://www.google.com/s2/favicons?domain={domain}&sz=64"

def get_company_from_article(article):
    """Extract company name from article"""
    title = article.get('title', '').lower()
    summary = article.get('summary', '').lower()
    source = article.get('source', '').lower()
    combined = title + ' ' + summary + ' ' + source
    
    companies = {
        'Maven': ['maven', 'maven clinic'],
        'Carrot': ['carrot', 'carrot fertility'],
        'KindBody': ['kindbody', 'kind body'],
        'WIN Fertility': ['win fertility', 'winfertility'],
        'Pomelo': ['pomelo', 'pomelo health'],
        'Midi': ['midi', 'midi health'],
        'Evernow': ['evernow'],
        'Pacify': ['pacify'],
        'Progyny': ['progyny']
    }
    
    for company, keywords in companies.items():
        for keyword in keywords:
            if keyword in combined:
                return company
    
    return 'General'

def generate_importance_summary(article):
    """Generate 'why it matters' summary"""
    title = article.get('title', '').lower()
    summary = article.get('summary', '').lower()
    combined = title + ' ' + summary
    
    if 'funding' in combined or 'raised' in combined or 'series' in combined:
        return "💰 <strong>Capital signal:</strong> New funding indicates growth acceleration and potential competitive pressure."
    elif 'ai' in combined or 'artificial intelligence' in combined or 'ml' in combined:
        return "🤖 <strong>AI arms race:</strong> Technology investment may become table stakes. Assess differentiation strategy."
    elif 'partnership' in combined or 'partner' in combined:
        return "🤝 <strong>Ecosystem play:</strong> Partnerships expand reach and integration. Monitor for competitive moats."
    elif 'acquisition' in combined or 'acquire' in combined or 'merger' in combined:
        return "🏢 <strong>Market consolidation:</strong> M&A reshapes competitive landscape. Watch for talent and tech grabs."
    elif 'launch' in combined or 'product' in combined or 'platform' in combined:
        return "🚀 <strong>Product momentum:</strong> New offerings signal market expansion and feature competition."
    else:
        return "📊 <strong>Market signal:</strong> Track for pattern analysis and competitive positioning."

def generate_html_email():
    """Generate clean, professional HTML email"""
    
    articles_data = load_json(ARTICLES_FILE)
    linkedin_data = load_json(LINKEDIN_FILE)
    linkedin_posts = load_json(LINKEDIN_POSTS_FILE)
    reddit_data = load_json(REDDIT_FILE)
    progyny_data = load_json(PROGYNY_FILE)
    
    # Get recent articles (last 24 hours)
    cutoff = datetime.now() - timedelta(hours=24)
    
    # Handle different data structures
    if isinstance(articles_data, list):
        articles_list = articles_data
    elif isinstance(articles_data, dict):
        articles_list = articles_data.get('articles', [])
        if isinstance(articles_list, dict):
            # Convert dict to list
            articles_list = [{'id': k, **v} for k, v in articles_list.items()]
    else:
        articles_list = []
    
    # Age cutoff: 30 days max
    age_cutoff = datetime.now() - timedelta(days=30)
    
    # Load sent counts to track how many times each article was sent
    sent_count_file = Path.home() / ".openclaw" / "workspace" / "config" / "competitor-sent-count-v2.json"
    sent_counts = load_json(sent_count_file) if sent_count_file.exists() else {}
    
    recent_articles = []
    for article in articles_list:
        try:
            data = article if isinstance(article, dict) else {}
            
            # Check article age
            found_at_str = data.get('found_at', '2000-01-01')
            found_at = datetime.fromisoformat(found_at_str.replace('Z', '+00:00').replace('+00:00', ''))
            
            # Skip if older than 30 days
            if found_at < age_cutoff:
                continue
            
            # Check send count (max 2 times)
            article_id = data.get('id', '')
            if sent_counts.get(article_id, 0) >= 2:
                continue
            
            # Include if recent or not yet sent
            if found_at > cutoff or not data.get('sent', False):
                recent_articles.append(data)
                # Increment send count
                sent_counts[article_id] = sent_counts.get(article_id, 0) + 1
        except:
            # If can't parse date, skip to be safe
            pass
    
    # Save updated sent counts
    with open(sent_count_file, 'w') as f:
        json.dump(sent_counts, f, indent=2)
    
    # Categorize by priority
    critical = [a for a in recent_articles if a.get('priority') == 'critical'][:3]
    high = [a for a in recent_articles if a.get('priority') == 'high'][:3]
    medium = [a for a in recent_articles if a.get('priority') == 'medium'][:3]
    
    # Get Progyny mentions
    progyny_mentions = progyny_data.get('mentions', [])[:5]
    exec_news = progyny_data.get('executive_news', [])[:3]
    
    # Get Reddit intel
    reddit_posts = reddit_data.get('posts', [])[:5]
    
    # Get LinkedIn posts
    exec_posts = linkedin_posts.get('posts', [])[:3] if isinstance(linkedin_posts, dict) else []
    
    today_str = datetime.now().strftime('%A, %B %d, %Y')
    
    html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; 
               line-height: 1.5; color: #1a1a1a; max-width: 680px; margin: 0 auto; background: #fafafa; }}
        .container {{ background: white; padding: 40px; }}
        .header {{ border-bottom: 2px solid #1a1a1a; padding-bottom: 20px; margin-bottom: 30px; }}
        .header h1 {{ margin: 0; font-size: 24px; font-weight: 600; letter-spacing: -0.5px; }}
        .header p {{ margin: 8px 0 0 0; color: #666; font-size: 14px; }}
        
        .section-title {{ font-size: 12px; font-weight: 600; text-transform: uppercase; 
                         letter-spacing: 1px; color: #666; margin: 30px 0 15px 0;
                         border-bottom: 1px solid #e5e5e5; padding-bottom: 8px; }}
        
        .article {{ margin: 20px 0; padding: 20px 0; border-bottom: 1px solid #f0f0f0; }}
        .article:last-child {{ border-bottom: none; }}
        
        .article-header {{ display: flex; align-items: center; margin-bottom: 12px; }}
        .logo {{ width: 24px; height: 24px; margin-right: 10px; border-radius: 4px; }}
        .company {{ font-size: 11px; font-weight: 600; text-transform: uppercase; 
                   letter-spacing: 0.5px; color: #999; }}
        
        .priority {{ display: inline-flex; align-items: center; margin-left: auto; }}
        .priority-dot {{ width: 8px; height: 8px; border-radius: 50%; margin-right: 6px; }}
        .priority-critical {{ background: #dc2626; }}
        .priority-high {{ background: #ea580c; }}
        .priority-medium {{ background: #ca8a04; }}
        .priority-label {{ font-size: 11px; font-weight: 500; text-transform: uppercase; color: #666; }}
        
        .title {{ font-size: 16px; font-weight: 600; margin-bottom: 6px; line-height: 1.4; }}
        .title a {{ color: #1a1a1a; text-decoration: none; }}
        .title a:hover {{ text-decoration: underline; }}
        
        .meta {{ font-size: 12px; color: #999; margin-bottom: 10px; }}
        .summary {{ font-size: 14px; color: #444; margin-bottom: 12px; }}
        
        .why-matters {{ font-size: 13px; color: #555; padding: 12px 16px; 
                       background: #f8f8f8; border-left: 3px solid #ddd; }}
        
        .progyny-section {{ background: #fafafa; padding: 20px; margin: 20px 0; 
                           border: 1px solid #e5e5e5; border-radius: 4px; }}
        .progyny-title {{ font-size: 14px; font-weight: 600; margin-bottom: 12px; 
                         color: #1a1a1a; }}
        .mention {{ padding: 12px 0; border-bottom: 1px solid #eee; }}
        .mention:last-child {{ border-bottom: none; padding-bottom: 0; }}
        .mention-title {{ font-size: 13px; font-weight: 500; margin-bottom: 4px; }}
        .mention-title a {{ color: #2563eb; text-decoration: none; }}
        .mention-meta {{ font-size: 11px; color: #999; }}
        
        .stats {{ display: flex; gap: 30px; margin: 20px 0; padding: 15px 0; 
                 border-top: 1px solid #e5e5e5; border-bottom: 1px solid #e5e5e5; }}
        .stat {{ text-align: center; }}
        .stat-number {{ font-size: 28px; font-weight: 600; color: #1a1a1a; }}
        .stat-label {{ font-size: 11px; color: #999; text-transform: uppercase; letter-spacing: 0.5px; }}
        
        .footer {{ margin-top: 40px; padding-top: 20px; border-top: 1px solid #e5e5e5;
                  font-size: 12px; color: #999; text-align: center; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Competitive Intelligence Report</h1>
            <p>{today_str} | 24-Hour Window</p>
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
    
    # Progyny Market Sentiment Section
    if progyny_mentions or exec_news:
        html += """
        <div class="section-title">What the Market is Saying About Progyny</div>
        <div class="progyny-section">
"""
        
        if progyny_mentions:
            html += '<div class="progyny-title">📢 Recent Mentions</div>'
            for mention in progyny_mentions[:3]:
                source = mention.get('subreddit', mention.get('source', 'News'))
                html += f"""
            <div class="mention">
                <div class="mention-title"><a href="{mention.get('url', '#')}">{mention.get('title', 'No title')[:80]}...</a></div>
                <div class="mention-meta">{source} | {mention.get('score', 0)} upvotes</div>
            </div>
"""
        
        if exec_news:
            html += '<div class="progyny-title" style="margin-top: 20px;">👔 Executive News</div>'
            for news in exec_news[:2]:
                html += f"""
            <div class="mention">
                <div class="mention-title"><a href="{news.get('url', '#')}">{news.get('headline', 'No headline')[:80]}...</a></div>
                <div class="mention-meta">{news.get('executive', '')} • {news.get('published', 'Recent')}</div>
            </div>
"""
        
        html += "</div>"
    
    # Critical Signals
    if critical:
        html += '<div class="section-title">🔴 Critical Signals</div>'
        for article in critical:
            company = get_company_from_article(article)
            logo_url = get_company_logo_url(company)
            importance = generate_importance_summary(article)
            html += f"""
        <div class="article">
            <div class="article-header">
                <img src="{logo_url}" alt="{company}" class="logo" onerror="this.style.display='none'">
                <span class="company">{company}</span>
                <span class="priority">
                    <span class="priority-dot priority-critical"></span>
                    <span class="priority-label">Critical</span>
                </span>
            </div>
            <div class="title"><a href="{article.get('link', '#')}">{article.get('title', 'No title')}</a></div>
            <div class="meta">{article.get('source', 'Unknown')} • {article.get('published', 'Recent')}</div>
            <div class="summary">{article.get('summary', '')[:200]}...</div>
            <div class="why-matters">{importance}</div>
        </div>
"""
    
    # High Priority
    if high:
        html += '<div class="section-title">🟠 High Priority</div>'
        for article in high:
            company = get_company_from_article(article)
            logo_url = get_company_logo_url(company)
            importance = generate_importance_summary(article)
            html += f"""
        <div class="article">
            <div class="article-header">
                <img src="{logo_url}" alt="{company}" class="logo" onerror="this.style.display='none'">
                <span class="company">{company}</span>
                <span class="priority">
                    <span class="priority-dot priority-high"></span>
                    <span class="priority-label">High</span>
                </span>
            </div>
            <div class="title"><a href="{article.get('link', '#')}">{article.get('title', 'No title')}</a></div>
            <div class="meta">{article.get('source', 'Unknown')} • {article.get('published', 'Recent')}</div>
            <div class="summary">{article.get('summary', '')[:200]}...</div>
            <div class="why-matters">{importance}</div>
        </div>
"""
    
    # Medium Priority
    if medium:
        html += '<div class="section-title">🟡 Medium Priority</div>'
        for article in medium:
            company = get_company_from_article(article)
            logo_url = get_company_logo_url(company)
            importance = generate_importance_summary(article)
            html += f"""
        <div class="article">
            <div class="article-header">
                <img src="{logo_url}" alt="{company}" class="logo" onerror="this.style.display='none'">
                <span class="company">{company}</span>
                <span class="priority">
                    <span class="priority-dot priority-medium"></span>
                    <span class="priority-label">Medium</span>
                </span>
            </div>
            <div class="title"><a href="{article.get('link', '#')}">{article.get('title', 'No title')}</a></div>
            <div class="meta">{article.get('source', 'Unknown')} • {article.get('published', 'Recent')}</div>
            <div class="summary">{article.get('summary', '')[:200]}...</div>
            <div class="why-matters">{importance}</div>
        </div>
"""
    
    # Reddit Intel - Use new collector with comprehensive monitoring
    try:
        import sys
        sys.path.insert(0, '/home/ubuntu/.openclaw/workspace/scripts')
        from reddit_intel_collector import format_for_email
        reddit_html = format_for_email()
        html += reddit_html
    except Exception as e:
        html += f"<!-- Reddit intel error: {e} -->"
        # Fallback to old method
        if reddit_posts:
            html += '<div class="section-title">💬 Reddit Intelligence</div>'
            for post in reddit_posts[:3]:
                category = post.get('findings', [{}])[0].get('category', 'General')
                html += f"""
        <div class="article">
            <div class="article-header">
                <span class="company">r/{post.get('subreddit', 'unknown')}</span>
                <span class="priority">
                    <span class="priority-label">{category}</span>
                </span>
            </div>
            <div class="title"><a href="{post.get('url', '#')}">{post.get('title', 'No title')}</a></div>
            <div class="meta">{post.get('score', 0)} upvotes • {post.get('num_comments', 0)} comments</div>
        </div>
"""
    
    # LinkedIn Executive Posts
    if exec_posts:
        html += '<div class="section-title">💼 LinkedIn Executive Activity</div>'
        for post in exec_posts[:3]:
            company = post.get('company', 'Unknown')
            logo_url = get_company_logo_url(company)
            html += f"""
        <div class="article">
            <div class="article-header">
                <img src="{logo_url}" alt="{company}" class="logo" onerror="this.style.display='none'">
                <span class="company">{post.get('executive', 'Unknown')}</span>
            </div>
            <div class="summary">{post.get('description', '')[:150]}...</div>
            <div class="meta"><a href="{post.get('url', '#')}">View on LinkedIn</a></div>
        </div>
"""
    
    # Glassdoor Section
    try:
        import sys
        sys.path.insert(0, '/home/ubuntu/.openclaw/workspace/scripts')
        from glassdoor_fetcher import generate_glassdoor_html, fetch_glassdoor_data
        # Ensure data is fresh
        fetch_glassdoor_data()
        glassdoor_html = generate_glassdoor_html()
        html += glassdoor_html
    except Exception as e:
        html += f"<!-- Glassdoor error: {e} -->"
    
    html += """
        <div class="footer">
            Generated by Cicero • Competitive Intelligence System<br>
            Sources: RSS Feeds, Web Search, Reddit, LinkedIn, Glassdoor
        </div>
    </div>
</body>
</html>
"""
    
    # Save email
    EMAIL_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with open(EMAIL_OUTPUT, 'w') as f:
        f.write(html)
    
    total_articles = len(critical) + len(high) + len(medium)
    print(f"✅ Email generated: {EMAIL_OUTPUT}")
    print(f"   Critical: {len(critical)} | High: {len(high)} | Medium: {len(medium)}")
    print(f"   Progyny mentions: {len(progyny_mentions)}")
    print(f"   Reddit posts: {len(reddit_posts)}")
    print(f"   LinkedIn posts: {len(exec_posts)}")
    
    return EMAIL_OUTPUT

if __name__ == "__main__":
    generate_html_email()
