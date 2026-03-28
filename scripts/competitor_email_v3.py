#!/usr/bin/env python3
"""
Competitive Intelligence Email Generator v3.1
Clean, professional design with executive summary
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
    combined = title + ' ' + summary
    
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

def generate_trend_summary(critical, high, medium, reddit_posts, progyny_mentions):
    """Generate executive summary of key trends"""
    summary_parts = []
    total_signals = len(critical) + len(high) + len(medium)
    
    if total_signals == 0:
        summary_parts.append("No new competitive signals in the last 24 hours.")
    else:
        summary_parts.append(f"{total_signals} new signals: {len(critical)} critical, {len(high)} high, {len(medium)} medium priority.")
    
    if reddit_posts:
        summary_parts.append(f"Reddit: {len(reddit_posts)} discussions across fertility communities.")
    
    if progyny_mentions:
        summary_parts.append(f"Progyny: {len(progyny_mentions)} mentions — monitor sentiment.")
    
    themes = []
    for article in critical + high:
        title = article.get('title', '').lower()
        if 'funding' in title or 'raised' in title:
            themes.append("funding activity")
        elif 'ai' in title or 'artificial intelligence' in title:
            themes.append("AI investments")
        elif 'partnership' in title:
            themes.append("partnerships")
        elif 'acquisition' in title:
            themes.append("M&A")
    
    if themes:
        unique_themes = list(set(themes))[:2]
        summary_parts.append(f"Themes: {', '.join(unique_themes)}.")
    
    return " ".join(summary_parts) if summary_parts else "Monitoring active. No significant developments."

def generate_importance_summary(article):
    """Generate 'why it matters' summary"""
    title = article.get('title', '').lower()
    summary = article.get('summary', '').lower()
    combined = title + ' ' + summary
    
    if 'funding' in combined or 'raised' in combined or 'series' in combined:
        return "💰 <strong>Capital signal:</strong> New funding indicates growth acceleration."
    elif 'ai' in combined or 'artificial intelligence' in combined:
        return "🤖 <strong>AI investment:</strong> Technology competition heating up."
    elif 'partnership' in combined or 'partner' in combined:
        return "🤝 <strong>Partnership:</strong> Ecosystem expansion and integration play."
    elif 'acquisition' in combined or 'acquire' in combined:
        return "🏢 <strong>M&A:</strong> Market consolidation reshaping landscape."
    elif 'launch' in combined or 'product' in combined:
        return "🚀 <strong>Product:</strong> New offerings signal competitive pressure."
    else:
        return "📊 <strong>Market signal:</strong> Track for pattern analysis."

def generate_html_email():
    """Generate clean, professional HTML email"""
    
    # Load all data
    articles_data = load_json(ARTICLES_FILE)
    linkedin_posts = load_json(LINKEDIN_POSTS_FILE)
    reddit_data = load_json(REDDIT_FILE)
    progyny_data = load_json(PROGYNY_FILE)
    
    # Time cutoffs
    now = datetime.now()
    cutoff_24h = now - timedelta(hours=24)
    cutoff_30d = now - timedelta(days=30)
    
    # Process articles
    articles_list = []
    if isinstance(articles_data, list):
        articles_list = articles_data
    elif isinstance(articles_data, dict):
        articles_list = articles_data.get('articles', [])
    
    # Load sent counts
    sent_count_file = Path.home() / ".openclaw" / "workspace" / "config" / "competitor-sent-count-v2.json"
    sent_counts = load_json(sent_count_file)
    
    recent_articles = []
    for article in articles_list:
        if not isinstance(article, dict):
            continue
        
        # Check age (30 days max)
        found_at_str = article.get('found_at', '2000-01-01')
        try:
            found_at = datetime.fromisoformat(found_at_str.replace('Z', '+00:00').replace('+00:00', ''))
            if found_at < cutoff_30d:
                continue
        except:
            continue
        
        # Check send count (2 max) - but show all articles under 30 days for visibility
        article_id = article.get('id', '')
        send_count = sent_counts.get(article_id, 0)
        
        # Include article if under 30 days old (regardless of send count for display)
        # But mark if it's new or repeated
        article['_send_count'] = send_count
        article['_is_new'] = send_count < 2
        recent_articles.append(article)
        
        # Increment count for new articles
        if send_count < 2:
            sent_counts[article_id] = send_count + 1
    
    # Save sent counts
    with open(sent_count_file, 'w') as f:
        json.dump(sent_counts, f, indent=2)
    
    # Helper to format article dates
    def format_article_date(article):
        """Extract and format date from article"""
        # Try published date first (RSS format)
        pub_date = article.get('published', '')
        if pub_date:
            try:
                # Parse RSS date format: "Wed, 18 Mar 2026 22:06:58 GMT"
                from email.utils import parsedate_to_datetime
                dt = parsedate_to_datetime(pub_date)
                return dt.strftime('%b %d, %Y')
            except:
                pass
            try:
                # Try ISO format
                dt = datetime.fromisoformat(pub_date.replace('Z', '+00:00').replace('+00:00', ''))
                return dt.strftime('%b %d, %Y')
            except:
                pass
        
        # Fallback to found_at
        found_at = article.get('found_at', '')
        if found_at:
            try:
                dt = datetime.fromisoformat(found_at.replace('Z', '+00:00').replace('+00:00', ''))
                return dt.strftime('%b %d, %Y')
            except:
                pass
        
        return 'Recent'
    
    # Categorize - include ALL articles under 30 days, sorted by priority and date
    # Sort by found_at descending (newest first)
    recent_articles_sorted = sorted(
        recent_articles, 
        key=lambda x: x.get('found_at', '2000-01-01'), 
        reverse=True
    )
    
    critical = [a for a in recent_articles_sorted if a.get('priority') == 'critical'][:5]
    high = [a for a in recent_articles_sorted if a.get('priority') == 'high'][:5]
    medium = [a for a in recent_articles_sorted if a.get('priority') in ('medium', 'low')]
    
    # Get other data
    progyny_mentions = progyny_data.get('mentions', [])[:5]
    exec_news = progyny_data.get('executive_news', [])[:3]
    reddit_posts = reddit_data.get('posts', [])[:5]
    exec_posts = linkedin_posts.get('posts', [])[:3] if isinstance(linkedin_posts, dict) else []
    
    # Hard-coded Reddit posts about Progyny (from previous scans)
    # These are important patient sentiment signals
    progyny_reddit_posts = [
        {
            "title": "Is Progyny scammy or just incompetent? Their billing practices seem slimey",
            "subreddit": "r/IVF",
            "date": "2025-05-09",
            "score": 1,
            "url": "https://reddit.com/r/IVF/comments/1kiooao/is_progyny_scammy_or_just_incompetent_their/",
            "summary": "Patient describes billing issues: insurance paid labwork in full per EOB, but Progyny sent separate bill claiming it goes toward deductible. Plan has no co-insurance for labwork. Additional bill for consultation where not all codes were billed to insurance.",
            "sentiment": "negative",
            "severity": "high",
            "action_needed": "⚠️ Billing coordination issue - flag for customer success team"
        },
        {
            "title": "Does Progyny cover Omnitrope/HGH?",
            "subreddit": "r/IVF",
            "date": "2025-05-17",
            "score": 1,
            "url": "https://reddit.com/r/IVF/comments/1kp10oh/does_progyny_cover_omnitropehgh/",
            "summary": "Patient asking how to get Omnitrope/HGH/Saizen covered. Common question about medication coverage.",
            "sentiment": "neutral",
            "severity": "low",
            "action_needed": "📋 Coverage question - consider FAQ/documentation update"
        }
    ]
    
    # Generate summary
    trend_summary = generate_trend_summary(critical, high, medium, reddit_posts, progyny_mentions)
    today_str = now.strftime('%A, %B %d, %Y')
    
    # Build HTML
    html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; 
               line-height: 1.5; color: #1a1a1a; max-width: 680px; margin: 0 auto; background: #fafafa; }}
        .container {{ background: white; padding: 40px; }}
        .header {{ border-bottom: 2px solid #1a1a1a; padding-bottom: 20px; margin-bottom: 30px; }}
        .header h1 {{ margin: 0; font-size: 24px; font-weight: 600; }}
        .header p {{ margin: 8px 0 0 0; color: #666; font-size: 14px; }}
        
        .exec-summary {{ background: #f0f7ff; padding: 20px; margin: 20px 0; 
                       border-left: 4px solid #0066cc; border-radius: 0 4px 4px 0; }}
        .exec-summary h2 {{ margin: 0 0 12px 0; font-size: 14px; font-weight: 600; color: #0066cc; }}
        .exec-summary p {{ margin: 0; font-size: 14px; line-height: 1.6; color: #333; }}
        
        .stats {{ display: flex; gap: 30px; margin: 20px 0; padding: 15px 0; 
                 border-top: 1px solid #e5e5e5; border-bottom: 1px solid #e5e5e5; }}
        .stat {{ text-align: center; }}
        .stat-number {{ font-size: 28px; font-weight: 600; color: #1a1a1a; }}
        .stat-label {{ font-size: 11px; color: #999; text-transform: uppercase; }}
        
        .section-title {{ font-size: 12px; font-weight: 600; text-transform: uppercase; 
                         letter-spacing: 1px; color: #666; margin: 30px 0 15px 0;
                         border-bottom: 1px solid #e5e5e5; padding-bottom: 8px; }}
        
        .article {{ margin: 20px 0; padding: 20px 0; border-bottom: 1px solid #f0f0f0; }}
        .article-header {{ display: flex; align-items: center; margin-bottom: 12px; }}
        .logo {{ width: 24px; height: 24px; margin-right: 10px; border-radius: 4px; }}
        .company {{ font-size: 11px; font-weight: 600; text-transform: uppercase; color: #999; }}
        
        .priority {{ display: inline-flex; align-items: center; margin-left: auto; }}
        .priority-dot {{ width: 8px; height: 8px; border-radius: 50%; margin-right: 6px; }}
        .priority-critical {{ background: #dc2626; }}
        .priority-high {{ background: #ea580c; }}
        .priority-medium {{ background: #ca8a04; }}
        .priority-label {{ font-size: 11px; font-weight: 500; text-transform: uppercase; color: #666; }}
        
        .title {{ font-size: 16px; font-weight: 600; margin-bottom: 6px; }}
        .title a {{ color: #1a1a1a; text-decoration: none; }}
        .meta {{ font-size: 12px; color: #999; margin-bottom: 10px; }}
        .summary {{ font-size: 14px; color: #444; margin-bottom: 12px; }}
        .why-matters {{ font-size: 13px; color: #555; padding: 12px 16px; 
                       background: #f8f8f8; border-left: 3px solid #ddd; }}
        
        .progyny-section {{ background: #fafafa; padding: 20px; margin: 20px 0; 
                           border: 1px solid #e5e5e5; border-radius: 4px; }}
        .progyny-title {{ font-size: 14px; font-weight: 600; margin-bottom: 12px; color: #1a1a1a; }}
        .mention {{ padding: 12px 0; border-bottom: 1px solid #eee; }}
        .mention:last-child {{ border-bottom: none; }}
        .mention-title {{ font-size: 13px; font-weight: 500; margin-bottom: 4px; }}
        .mention-title a {{ color: #2563eb; text-decoration: none; }}
        .mention-meta {{ font-size: 11px; color: #999; }}
        .mention-summary {{ font-size: 12px; color: #666; font-style: italic; margin-top: 4px; }}
        
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
                <div class="stat-number">{len(progyny_mentions)}</div>
                <div class="stat-label">Progyny Mentions</div>
            </div>
        </div>
"""
    
    # Progyny Section
    if progyny_mentions or exec_news or progyny_reddit_posts:
        html += '<div class="section-title">What the Market is Saying About Progyny</div><div class="progyny-section">'
        
        # Reddit Sentiment Analysis (PRIORITY)
        if progyny_reddit_posts:
            html += '<div class="progyny-title">🚨 Reddit Patient Sentiment (Action Required)</div>'
            for post in progyny_reddit_posts:
                # Format date
                post_date = post.get('date', 'Recent')
                try:
                    dt = datetime.strptime(post_date, '%Y-%m-%d')
                    post_date = dt.strftime('%b %d, %Y')
                except:
                    pass
                
                # Color coding based on sentiment
                sentiment_color = '#16a34a' if post['sentiment'] == 'positive' else '#ea580c' if post['sentiment'] == 'neutral' else '#dc2626'
                sentiment_bg = '#f0fdf4' if post['sentiment'] == 'positive' else '#fff7ed' if post['sentiment'] == 'neutral' else '#fef2f2'
                severity_badge = ''
                if post['severity'] == 'high':
                    severity_badge = '<span style="background:#dc2626;color:white;padding:2px 6px;border-radius:3px;font-size:10px;margin-left:8px;">HIGH</span>'
                elif post['severity'] == 'medium':
                    severity_badge = '<span style="background:#ea580c;color:white;padding:2px 6px;border-radius:3px;font-size:10px;margin-left:8px;">MEDIUM</span>'
                
                html += f'''
            <div class="mention" style="background:{sentiment_bg};border-left:4px solid {sentiment_color};padding:15px;margin:10px 0;border-radius:4px;">
                <div class="mention-title"><a href="{post['url']}">{post['title']}</a>{severity_badge}</div>
                <div class="mention-meta">{post['subreddit']} • {post_date} • ⬆️ {post['score']}</div>
                <div class="summary" style="margin:8px 0;font-size:13px;color:#444;">{post['summary'][:200]}...</div>
                <div style="font-size:12px;color:#666;font-weight:600;margin-top:8px;">{post['action_needed']}</div>
            </div>
                '''
        
        if progyny_mentions:
            html += '<div class="progyny-title">📢 News Mentions</div>'
            for mention in progyny_mentions[:3]:
                source = mention.get('subreddit', mention.get('source', 'News'))
                
                # Parse date
                mention_date_raw = mention.get('created_utc', mention.get('published', mention.get('date', None)))
                mention_date = 'Recent'
                if isinstance(mention_date_raw, (int, float)):
                    mention_date = datetime.fromtimestamp(mention_date_raw).strftime('%b %d, %Y')
                elif isinstance(mention_date_raw, str):
                    try:
                        # Try parsing ISO format
                        dt = datetime.fromisoformat(mention_date_raw.replace('Z', '+00:00').replace('+00:00', ''))
                        mention_date = dt.strftime('%b %d, %Y')
                    except:
                        mention_date = mention_date_raw[:10] if len(mention_date_raw) > 10 else mention_date_raw
                
                html += f'''
            <div class="mention">
                <div class="mention-title"><a href="{mention.get('url', '#')}">{mention.get('title', 'No title')[:80]}...</a></div>
                <div class="mention-meta">{source} • {mention_date}</div>
            </div>
                '''
        
        if exec_news:
            html += '<div class="progyny-title" style="margin-top: 20px;">👔 Executive News</div>'
            for news in exec_news[:2]:
                pub_date = news.get('published', 'Recent')
                html += f'''
            <div class="mention">
                <div class="mention-title"><a href="{news.get('url', '#')}">{news.get('headline', 'No headline')[:80]}...</a></div>
                <div class="mention-meta">{news.get('executive', '')} • {pub_date}</div>
            </div>
                '''
        html += '</div>'
    
    # Critical Signals
    if critical:
        html += '<div class="section-title">🔴 Critical Signals</div>'
        for article in critical:
            company = get_company_from_article(article)
            logo_url = get_company_logo_url(company)
            importance = generate_importance_summary(article)
            pub_date = format_article_date(article)
            is_new = article.get('_is_new', False)
            new_badge = '<span style="background:#dc2626;color:white;padding:2px 6px;border-radius:3px;font-size:10px;margin-left:8px;">NEW</span>' if is_new else ''
            html += f'''
        <div class="article">
            <div class="article-header">
                <img src="{logo_url}" alt="{company}" class="logo" onerror="this.style.display='none'">
                <span class="company">{company}</span>
                <span class="priority">
                    <span class="priority-dot priority-critical"></span>
                    <span class="priority-label">Critical</span>{new_badge}
                </span>
            </div>
            <div class="title"><a href="{article.get('link', '#')}">{article.get('title', 'No title')}</a></div>
            <div class="meta">{article.get('source', 'Unknown')} • {pub_date}</div>
            <div class="summary">{article.get('summary', '')[:200]}...</div>
            <div class="why-matters">{importance}</div>
        </div>
            '''
    
    # High Priority
    if high:
        html += '<div class="section-title">🟠 High Priority</div>'
        for article in high:
            company = get_company_from_article(article)
            logo_url = get_company_logo_url(company)
            importance = generate_importance_summary(article)
            pub_date = format_article_date(article)
            is_new = article.get('_is_new', False)
            new_badge = '<span style="background:#ea580c;color:white;padding:2px 6px;border-radius:3px;font-size:10px;margin-left:8px;">NEW</span>' if is_new else ''
            html += f'''
        <div class="article">
            <div class="article-header">
                <img src="{logo_url}" alt="{company}" class="logo" onerror="this.style.display='none'">
                <span class="company">{company}</span>
                <span class="priority">
                    <span class="priority-dot priority-high"></span>
                    <span class="priority-label">High</span>{new_badge}
                </span>
            </div>
            <div class="title"><a href="{article.get('link', '#')}">{article.get('title', 'No title')}</a></div>
            <div class="meta">{article.get('source', 'Unknown')} • {pub_date}</div>
            <div class="summary">{article.get('summary', '')[:200]}...</div>
            <div class="why-matters">{importance}</div>
        </div>
            '''
    
    # Medium Priority
    if medium:
        html += '<div class="section-title">🟡 Medium Priority</div>'
        for article in medium[:10]:  # Limit to 10 medium priority
            company = get_company_from_article(article)
            logo_url = get_company_logo_url(company)
            importance = generate_importance_summary(article)
            pub_date = format_article_date(article)
            is_new = article.get('_is_new', False)
            new_badge = '<span style="background:#ca8a04;color:white;padding:2px 6px;border-radius:3px;font-size:10px;margin-left:8px;">NEW</span>' if is_new else ''
            html += f'''
        <div class="article">
            <div class="article-header">
                <img src="{logo_url}" alt="{company}" class="logo" onerror="this.style.display='none'">
                <span class="company">{company}</span>
                <span class="priority">
                    <span class="priority-dot priority-medium"></span>
                    <span class="priority-label">Medium</span>{new_badge}
                </span>
            </div>
            <div class="title"><a href="{article.get('link', '#')}">{article.get('title', 'No title')}</a></div>
            <div class="meta">{article.get('source', 'Unknown')} • {pub_date}</div>
            <div class="summary">{article.get('summary', '')[:200]}...</div>
            <div class="why-matters">{importance}</div>
        </div>
            '''
    
    # Reddit Intel
    try:
        import sys
        sys.path.insert(0, '/home/ubuntu/.openclaw/workspace/scripts')
        from reddit_intel_collector import format_for_email
        reddit_html = format_for_email()
        html += reddit_html
    except Exception as e:
        html += f'<!-- Reddit error: {e} -->'
    
    # LinkedIn Posts
    if exec_posts:
        html += '<div class="section-title">💼 LinkedIn Executive Activity</div>'
        for post in exec_posts[:5]:
            company = post.get('company', 'Unknown')
            logo_url = get_company_logo_url(company)
            
            # Parse LinkedIn post date
            post_date_raw = post.get('date', post.get('published', post.get('timestamp', None)))
            post_date = 'Recent'
            if isinstance(post_date_raw, (int, float)):
                post_date = datetime.fromtimestamp(post_date_raw).strftime('%b %d, %Y')
            elif isinstance(post_date_raw, str):
                try:
                    dt = datetime.fromisoformat(post_date_raw.replace('Z', '+00:00').replace('+00:00', ''))
                    post_date = dt.strftime('%b %d, %Y')
                except:
                    post_date = post_date_raw[:10] if len(post_date_raw) > 10 else post_date_raw
            
            html += f'''
        <div class="article">
            <div class="article-header">
                <img src="{logo_url}" alt="{company}" class="logo" onerror="this.style.display='none'">
                <span class="company">{post.get('executive', 'Unknown')} • {company}</span>
            </div>
            <div class="summary">{post.get('description', '')[:150]}...</div>
            <div class="meta">{post_date} • <a href="{post.get('url', '#')}">View on LinkedIn</a></div>
        </div>
            '''
    
    # Glassdoor
    try:
        import sys
        sys.path.insert(0, '/home/ubuntu/.openclaw/workspace/scripts')
        from glassdoor_fetcher import generate_glassdoor_html, fetch_glassdoor_data
        fetch_glassdoor_data()
        html += generate_glassdoor_html()
    except Exception as e:
        html += f'<!-- Glassdoor error: {e} -->'
    
    html += '''
        <div class="footer">
            Generated by Cicero • Competitive Intelligence System<br>
            Sources: RSS Feeds, Web Search, Reddit, LinkedIn, Glassdoor
        </div>
    </div>
</body>
</html>
    '''
    
    # Save
    EMAIL_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with open(EMAIL_OUTPUT, 'w') as f:
        f.write(html)
    
    print(f"✅ Email generated: {EMAIL_OUTPUT}")
    print(f"   Critical: {len(critical)} | High: {len(high)} | Medium: {len(medium)}")
    print(f"   Progyny mentions: {len(progyny_mentions)}")
    return EMAIL_OUTPUT

if __name__ == "__main__":
    generate_html_email()
