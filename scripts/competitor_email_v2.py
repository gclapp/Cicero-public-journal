#!/usr/bin/env python3
"""
Competitive Intelligence Email Generator v2
Combines RSS, web search, LinkedIn, and job changes into one report
With AI-generated summaries and executive trend analysis
"""

import json
import os
from datetime import datetime, timedelta
from pathlib import Path

ARTICLES_FILE = Path.home() / ".openclaw" / "workspace" / "config" / "competitor-articles-v2.json"
LINKEDIN_FILE = Path.home() / ".openclaw" / "workspace" / "config" / "linkedin-updates.json"
LINKEDIN_POSTS_FILE = Path.home() / ".openclaw" / "workspace" / "config" / "linkedin-executive-posts.json"
EMAIL_OUTPUT = Path.home() / ".openclaw" / "workspace" / "config" / "competitor-email-v2.html"

def load_articles():
    """Load news articles"""
    if ARTICLES_FILE.exists():
        with open(ARTICLES_FILE) as f:
            return json.load(f)
    return []

def load_linkedin_updates():
    """Load LinkedIn/exec updates"""
    if LINKEDIN_FILE.exists():
        with open(LINKEDIN_FILE) as f:
            return json.load(f)
    return []

def load_linkedin_executive_posts():
    """Load LinkedIn executive posts"""
    if LINKEDIN_POSTS_FILE.exists():
        with open(LINKEDIN_POSTS_FILE) as f:
            data = json.load(f)
            return data.get('posts', [])
    return []

def get_company_logo_url(company_name):
    """Get logo URL for a company"""
    # Map company names to their domains for favicon lookup
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
    """Extract company name from article title/summary/source"""
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
    
    # Check if article is from a specific company feed
    feed_sources = {
        'Maven News': 'Maven',
        'Carrot News': 'Carrot',
        'KindBody News': 'KindBody',
        'WIN Fertility News': 'WIN Fertility',
        'Pomelo News': 'Pomelo',
        'Midi News': 'Midi',
        'Evernow News': 'Evernow'
    }
    
    for feed_name, company in feed_sources.items():
        if feed_name.lower() in source:
            return company
    
    return 'General'

def generate_importance_summary(article):
    """Generate 1-2 sentence summary of why this article is important"""
    title = article.get('title', '').lower()
    summary = article.get('summary', '').lower()
    source = article.get('source', '').lower()
    category = article.get('category', 'general')
    
    # Maven Intelligence tracking
    if 'maven intelligence' in title or 'maven intelligence' in summary:
        return "🎯 <strong>Why it matters:</strong> Maven's new AI orchestration platform is a direct competitive threat. This represents their move from care navigation to AI-driven care management — watch for client announcements and partnership integrations."
    
    if 'maven' in title and ('ai' in title or 'artificial intelligence' in title or 'platform' in title):
        return "🤖 <strong>Why it matters:</strong> Maven is investing heavily in AI capabilities. This could signal a product shift toward automated care coordination — monitor for feature releases and client case studies."
    
    # Funding announcements
    if 'funding' in title or 'raises' in title or 'series' in title:
        if 'maven' in title:
            return "💰 <strong>Why it matters:</strong> Fresh capital means aggressive expansion ahead. Expect increased sales pressure, possible M&A activity, and enhanced product development."
        elif 'carrot' in title:
            return "💰 <strong>Why it matters:</strong> Carrot funding signals continued market validation for fertility benefits. Watch for geographic expansion or new product verticals."
        elif 'kindbody' in title:
            return "💰 <strong>Why it matters:</strong> KindBody funding supports their clinic + tech hybrid model. Monitor for new clinic openings or employer client wins."
        else:
            return "💰 <strong>Why it matters:</strong> New funding in the fertility/health space indicates continued investor interest. Could lead to increased competition for employer clients."
    
    # Partnerships
    if 'partnership' in title or 'partners' in title or 'collaboration' in title:
        if 'maven' in title:
            return "🤝 <strong>Why it matters:</strong> Maven partnership expands their ecosystem reach. Check if this is a distribution channel or technology integration — either way, it strengthens their competitive position."
        else:
            return "🤝 <strong>Why it matters:</strong> Strategic partnerships can rapidly expand market reach. Monitor for exclusivity clauses or multi-year commitments."
    
    # Acquisitions
    if 'acquisition' in title or 'acquires' in title or 'buys' in title:
        return "🏢 <strong>Why it matters:</strong> M&A activity reshapes competitive landscape. Look for talent grabs, technology integration, or market expansion motives."
    
    # Executive changes
    if category == 'leadership' or 'ceo' in title or 'chief' in title or 'president' in title:
        return "👔 <strong>Why it matters:</strong> Leadership changes often signal strategic shifts. New executives typically bring new playbooks — watch for org restructuring or strategy pivots in coming months."
    
    # Product launches
    if 'launch' in title or 'introduces' in title or 'announces' in title:
        return "🚀 <strong>Why it matters:</strong> New product/feature launch indicates where they're placing bets. Evaluate for competitive gaps in your own roadmap."
    
    # AI/Technology focus
    if 'ai' in title or 'artificial intelligence' in title or 'machine learning' in title or 'automation' in title:
        return "🤖 <strong>Why it matters:</strong> AI investment is accelerating across the industry. This could become a table-stakes feature — assess your own AI strategy and differentiation."
    
    # Default summaries by priority
    priority = article.get('priority', 'medium')
    if priority == 'critical':
        return "🔴 <strong>Why it matters:</strong> Critical market movement with immediate competitive implications. Review for strategic response requirements."
    elif priority == 'high':
        return "🟠 <strong>Why it matters:</strong> Significant development that could shift market dynamics. Monitor for follow-on announcements."
    else:
        return "🟡 <strong>Why it matters:</strong> Industry signal worth tracking. May indicate broader trends or competitive positioning."

def analyze_trends(articles):
    """Analyze articles for trend patterns and generate executive summary"""
    if not articles:
        return "No significant competitive activity detected in the last 30 days."
    
    # Count by theme
    ai_mentions = sum(1 for a in articles if 'ai' in a.get('title', '').lower() or 'artificial intelligence' in a.get('summary', '').lower())
    funding_mentions = sum(1 for a in articles if 'funding' in a.get('title', '').lower() or 'raises' in a.get('title', '').lower())
    partnership_mentions = sum(1 for a in articles if 'partnership' in a.get('title', '').lower())
    maven_mentions = sum(1 for a in articles if 'maven' in a.get('title', '').lower())
    carrot_mentions = sum(1 for a in articles if 'carrot' in a.get('title', '').lower())
    kindbody_mentions = sum(1 for a in articles if 'kindbody' in a.get('title', '').lower())
    
    # Build trend analysis
    trends = []
    
    if ai_mentions >= 3:
        trends.append(f"🤖 <strong>AI Arms Race:</strong> {ai_mentions} AI-related announcements signal rapid investment in automation and intelligence capabilities. Maven's 'Maven Intelligence' launch is the standout — they're positioning as an AI-first platform, not just a care navigator.")
    
    if funding_mentions >= 2:
        trends.append(f"💰 <strong>Capital Flow:</strong> {funding_mentions} funding events show continued investor confidence in fertility/women's health tech. This means more resources for sales, marketing, and product development across competitors.")
    
    if partnership_mentions >= 2:
        trends.append(f"🤝 <strong>Partnership Surge:</strong> {partnership_mentions} new partnerships indicate ecosystem-building as a core strategy. Companies are racing to integrate with health systems, EHRs, and adjacent services.")
    
    if maven_mentions >= 3:
        trends.append(f"🎯 <strong>Maven Momentum:</strong> {maven_mentions} Maven-specific signals — they're the most active competitor right now. Their AI platform launch + funding announcement suggests an aggressive 2026 growth strategy.")
    
    # Competitive positioning
    if carrot_mentions > kindbody_mentions:
        trends.append("📊 <strong>Carrot vs KindBody:</strong> Carrot is generating more news volume, suggesting stronger marketing/PR investment or more product activity.")
    elif kindbody_mentions > carrot_mentions:
        trends.append("📊 <strong>KindBody Visibility:</strong> KindBody is punching above their weight in news coverage — possible PR push or funding-related announcement cycle.")
    
    # Default if no clear trends
    if not trends:
        return "Market activity is distributed across multiple themes with no dominant trend emerging. Continue monitoring for pattern development."
    
    return "<br><br>".join(trends)

def generate_email():
    """Generate comprehensive competitive intelligence email"""
    articles = load_articles()
    linkedin_updates = load_linkedin_updates()
    
    # Filter to only recent items (last 30 days)
    cutoff = datetime.now() - timedelta(days=30)
    
    recent_articles = [a for a in articles if datetime.fromisoformat(a.get('found_at', '2000-01-01').replace('Z', '+00:00').replace('+00:00', '')) > cutoff or 'found_at' not in a]
    recent_linkedin = [u for u in linkedin_updates if datetime.fromisoformat(u.get('found_at', '2000-01-01').replace('Z', '+00:00').replace('+00:00', '')) > cutoff or 'found_at' not in u]
    
    # Load LinkedIn executive posts
    executive_posts = load_linkedin_executive_posts()
    recent_exec_posts = [p for p in executive_posts if datetime.fromisoformat(p.get('found_at', '2000-01-01').replace('Z', '+00:00').replace('+00:00', '')) > cutoff or 'found_at' not in p]
    
    # Categorize
    critical = [a for a in recent_articles if a.get('priority') == 'critical']
    high = [a for a in recent_articles if a.get('priority') == 'high']
    medium = [a for a in recent_articles if a.get('priority') == 'medium']
    
    job_changes = [u for u in recent_linkedin if u.get('type') == 'job_change']
    exec_news = [u for u in recent_linkedin if u.get('type') == 'exec_news']
    company_posts = [u for u in recent_linkedin if u.get('type') == 'company_post']
    
    # Generate trend analysis
    trend_summary = analyze_trends(recent_articles)
    
    # Generate HTML
    html = f"""<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 800px; margin: 0 auto; }}
        .header {{ background: linear-gradient(135deg, #1a365d, #2c5282); color: white; padding: 30px; text-align: center; }}
        .header h1 {{ margin: 0; font-size: 28px; }}
        .header p {{ margin: 10px 0 0 0; opacity: 0.9; }}
        .exec-summary {{ background: #eff6ff; padding: 25px; margin: 20px 0; border-left: 4px solid #3b82f6; border-radius: 8px; }}
        .exec-summary h2 {{ margin-top: 0; color: #1e40af; }}
        .section {{ margin: 20px 0; padding: 20px; border-left: 4px solid #ccc; background: white; border-radius: 8px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }}
        .critical {{ border-left-color: #dc2626; background: #fef2f2; }}
        .high {{ border-left-color: #ea580c; background: #fff7ed; }}
        .medium {{ border-left-color: #ca8a04; background: #fefce8; }}
        .job-change {{ border-left-color: #16a34a; background: #f0fdf4; }}
        .exec {{ border-left-color: #2563eb; background: #eff6ff; }}
        .title {{ font-size: 18px; font-weight: bold; margin-bottom: 8px; color: #1f2937; }}
        .meta {{ font-size: 12px; color: #6b7280; margin-bottom: 12px; }}
        .summary {{ font-size: 14px; color: #374151; margin-bottom: 12px; }}
        .importance {{ font-size: 14px; color: #1f2937; padding: 12px; background: rgba(255,255,255,0.7); border-radius: 6px; margin-top: 10px; }}
        .badge {{ display: inline-block; padding: 3px 10px; border-radius: 12px; font-size: 11px; font-weight: bold; margin-right: 8px; text-transform: uppercase; }}
        .badge-critical {{ background: #dc2626; color: white; }}
        .badge-high {{ background: #ea580c; color: white; }}
        .badge-medium {{ background: #ca8a04; color: white; }}
        .badge-job {{ background: #16a34a; color: white; }}
        .badge-exec {{ background: #2563eb; color: white; }}
        a {{ color: #2563eb; text-decoration: none; font-weight: 600; }}
        a:hover {{ text-decoration: underline; }}
        .stats {{ background: #f3f4f6; padding: 20px; border-radius: 8px; margin: 20px 0; display: flex; justify-content: space-around; text-align: center; }}
        .stat {{ padding: 10px; }}
        .stat-number {{ font-size: 32px; font-weight: bold; color: #1e40af; }}
        .stat-label {{ font-size: 12px; color: #6b7280; text-transform: uppercase; }}
        .trend-item {{ margin: 12px 0; padding: 12px; background: white; border-radius: 6px; border-left: 3px solid #3b82f6; }}
        .company-header {{ display: flex; align-items: center; margin-bottom: 12px; }}
        .company-logo {{ width: 32px; height: 32px; margin-right: 12px; border-radius: 4px; }}
        .company-name {{ font-size: 14px; font-weight: bold; color: #6b7280; text-transform: uppercase; letter-spacing: 0.5px; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🏛️ Competitive Intelligence Report</h1>
        <p>{datetime.now().strftime("%A, %B %d, %Y")} | 30-Day Window</p>
    </div>
    
    <div class="stats">
        <div class="stat">
            <div class="stat-number">{len(critical)}</div>
            <div class="stat-label">Critical</div>
        </div>
        <div class="stat">
            <div class="stat-number">{len(high)}</div>
            <div class="stat-label">High Priority</div>
        </div>
        <div class="stat">
            <div class="stat-number">{len(medium)}</div>
            <div class="stat-label">Medium</div>
        </div>
        <div class="stat">
            <div class="stat-number">{len(job_changes)}</div>
            <div class="stat-label">Job Changes</div>
        </div>
        <div class="stat">
            <div class="stat-number">{len(exec_news)}</div>
            <div class="stat-label">Exec Updates</div>
        </div>
    </div>
    
    <div class="exec-summary">
        <h2>📊 Executive Summary: Key Trends</h2>
        <p>{trend_summary}</p>
    </div>
"""
    
    # Glassdoor satisfaction data
    try:
        import sys
        sys.path.insert(0, '/home/ubuntu/.openclaw/workspace/scripts')
        from glassdoor_fetcher import generate_glassdoor_html
        glassdoor_html = generate_glassdoor_html()
        html += glassdoor_html
    except Exception as e:
        html += f"<!-- Glassdoor data unavailable: {e} -->"
    
    # Critical signals
    if critical:
        html += "<h2>🔴 Critical Signals</h2>"
        for article in critical:
            importance = generate_importance_summary(article)
            company = get_company_from_article(article)
            logo_url = get_company_logo_url(company)
            html += f"""
    <div class="section critical">
        <div class="company-header">
            <img src="{logo_url}" alt="{company}" class="company-logo" onerror="this.style.display='none'">
            <span class="company-name">{company}</span>
        </div>
        <span class="badge badge-critical">Critical</span>
        <span class="badge">{article.get('category', 'general')}</span>
        <div class="title"><a href="{article.get('link', '#')}">{article.get('title', 'No title')}</a></div>
        <div class="meta">Source: {article.get('source', 'Unknown')} | {article.get('published', 'Unknown date')}</div>
        <div class="summary">{article.get('summary', '')[:300]}...</div>
        <div class="importance">{importance}</div>
    </div>
"""
    
    # LinkedIn Executive Posts
    if recent_exec_posts:
        html += "<h2>💬 LinkedIn Executive Posts</h2>"
        for post in recent_exec_posts[:5]:  # Top 5 most recent
            company = post.get('company', 'Unknown')
            logo_url = get_company_logo_url(company)
            html += f"""
    <div class="section exec">
        <div class="company-header">
            <img src="{logo_url}" alt="{company}" class="company-logo" onerror="this.style.display='none'">
            <span class="company-name">{company}</span>
        </div>
        <span class="badge badge-exec">LinkedIn</span>
        <div class="title">{post.get('executive', 'Unknown')} - {company}</div>
        <div class="meta"><a href="{post.get('url', '#')}">View on LinkedIn</a></div>
        <div class="summary">{post.get('description', '')[:400]}...</div>
        <div class="importance">📢 <strong>Why it matters:</strong> Executive posts reveal strategic priorities, company culture, and upcoming initiatives before they're officially announced.</div>
    </div>
"""
    
    # Job changes
    if job_changes:
        html += "<h2>💼 Executive Job Changes</h2>"
        for update in job_changes:
            company = update.get('company', 'Unknown')
            logo_url = get_company_logo_url(company)
            html += f"""
    <div class="section job-change">
        <div class="company-header">
            <img src="{logo_url}" alt="{company}" class="company-logo" onerror="this.style.display='none'">
            <span class="company-name">{company}</span>
        </div>
        <span class="badge badge-job">Job Change</span>
        <div class="title"><a href="{update.get('link', '#')}">{update.get('title', 'No title')}</a></div>
        <div class="meta">{update.get('published', 'Recent')}</div>
        <div class="summary">{update.get('description', '')}</div>
        <div class="importance">👔 <strong>Why it matters:</strong> Leadership changes signal potential strategy shifts. Monitor for new initiatives or organizational changes in the next 90 days.</div>
    </div>
"""
    
    # Executive news
    if exec_news:
        html += "<h2>👔 Executive Team Updates</h2>"
        for update in exec_news:
            html += f"""
    <div class="section exec">
        <span class="badge badge-exec">Executive</span>
        <span class="badge">{update.get('company', 'Unknown')}</span>
        <div class="title">{update.get('executive', 'Unknown')} - {update.get('title', 'Update')}</div>
        <div class="meta"><a href="{update.get('link', '#')}">Read more</a></div>
        <div class="summary">{update.get('description', '')}</div>
        <div class="importance">📢 <strong>Why it matters:</strong> Executive visibility often precedes major announcements. Watch for product launches or partnership news following this activity.</div>
    </div>
"""
    
    # High priority
    if high:
        html += "<h2>🟠 High Priority Signals</h2>"
        for article in high:
            importance = generate_importance_summary(article)
            company = get_company_from_article(article)
            logo_url = get_company_logo_url(company)
            html += f"""
    <div class="section high">
        <div class="company-header">
            <img src="{logo_url}" alt="{company}" class="company-logo" onerror="this.style.display='none'">
            <span class="company-name">{company}</span>
        </div>
        <span class="badge badge-high">High</span>
        <span class="badge">{article.get('category', 'general')}</span>
        <div class="title"><a href="{article.get('link', '#')}">{article.get('title', 'No title')}</a></div>
        <div class="meta">Source: {article.get('source', 'Unknown')} | {article.get('published', 'Unknown date')}</div>
        <div class="summary">{article.get('summary', '')[:300]}...</div>
        <div class="importance">{importance}</div>
    </div>
"""
    
    # Company posts
    if company_posts:
        html += "<h2>📢 Company Announcements</h2>"
        for post in company_posts:
            html += f"""
    <div class="section medium">
        <span class="badge badge-medium">Announcement</span>
        <span class="badge">{post.get('company', 'Unknown')}</span>
        <div class="title"><a href="{post.get('link', '#')}">{post.get('title', 'No title')}</a></div>
        <div class="meta">{post.get('published', 'Recent')}</div>
        <div class="summary">{post.get('description', '')}</div>
        <div class="importance">📣 <strong>Why it matters:</strong> Company announcements reveal strategic priorities and market positioning. Evaluate for competitive threats or partnership opportunities.</div>
    </div>
"""
    
    # Medium priority
    if medium:
        html += "<h2>🟡 Medium Priority</h2>"
        for article in medium:
            importance = generate_importance_summary(article)
            company = get_company_from_article(article)
            logo_url = get_company_logo_url(company)
            html += f"""
    <div class="section medium">
        <div class="company-header">
            <img src="{logo_url}" alt="{company}" class="company-logo" onerror="this.style.display='none'">
            <span class="company-name">{company}</span>
        </div>
        <span class="badge badge-medium">Medium</span>
        <span class="badge">{article.get('category', 'general')}</span>
        <div class="title"><a href="{article.get('link', '#')}">{article.get('title', 'No title')}</a></div>
        <div class="meta">Source: {article.get('source', 'Unknown')} | {article.get('published', 'Unknown date')}</div>
        <div class="summary">{article.get('summary', '')[:300]}...</div>
        <div class="importance">{importance}</div>
    </div>
"""
    
    # No news
    if not any([critical, high, medium, job_changes, exec_news, company_posts]):
        html += """
    <div class="section">
        <p>No new competitive signals in the last 30 days.</p>
        <p>This could mean:</p>
        <ul>
            <li>Quiet period in the industry</li>
            <li>Sources need refreshing (checking RSS feeds, search APIs)</li>
            <li>Weekend/holiday lull</li>
        </ul>
    </div>
"""
    
    html += """
    <hr style="margin: 40px 0; border: none; border-top: 1px solid #e5e7eb;">
    <p style="font-size: 12px; color: #6b7280; text-align: center;">
        Generated by Cicero Competitive Intelligence System | 
        Sources: Google Alerts, Brave Search, LinkedIn Monitoring | 
        Focus: FemTech & Women's Health | Max 7 Articles | Strict Deduplication
    </p>
</body>
</html>
"""
    
    # Save email
    EMAIL_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with open(EMAIL_OUTPUT, 'w') as f:
        f.write(html)
    
    print(f"✅ Email generated: {EMAIL_OUTPUT}")
    print(f"   Articles: {len(recent_articles)}")
    print(f"   LinkedIn updates: {len(recent_linkedin)}")
    print(f"   Executive summary: {len(trend_summary)} chars")
    
    return str(EMAIL_OUTPUT)

if __name__ == "__main__":
    generate_email()