#!/usr/bin/env python3
"""
Competitive Intelligence Email Generator v2
Combines RSS, web search, LinkedIn, and job changes into one report
"""

import json
from datetime import datetime
from pathlib import Path

ARTICLES_FILE = Path.home() / ".openclaw" / "workspace" / "config" / "competitor-articles-v2.json"
LINKEDIN_FILE = Path.home() / ".openclaw" / "workspace" / "config" / "linkedin-updates.json"
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

def generate_email():
    """Generate comprehensive competitive intelligence email"""
    articles = load_articles()
    linkedin_updates = load_linkedin_updates()
    
    # Filter to only recent items (last 48 hours)
    cutoff = datetime.now() - timedelta(hours=48)
    
    recent_articles = [a for a in articles if datetime.fromisoformat(a.get('found_at', '2000-01-01')) > cutoff]
    recent_linkedin = [u for u in linkedin_updates if datetime.fromisoformat(u.get('found_at', '2000-01-01')) > cutoff]
    
    # Categorize
    critical = [a for a in recent_articles if a.get('priority') == 'critical']
    high = [a for a in recent_articles if a.get('priority') == 'high']
    medium = [a for a in recent_articles if a.get('priority') == 'medium']
    
    job_changes = [u for u in recent_linkedin if u.get('type') == 'job_change']
    exec_news = [u for u in recent_linkedin if u.get('type') == 'exec_news']
    company_posts = [u for u in recent_linkedin if u.get('type') == 'company_post']
    
    # Generate HTML
    html = f"""<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .header {{ background: #1a365d; color: white; padding: 20px; text-align: center; }}
        .section {{ margin: 20px 0; padding: 15px; border-left: 4px solid #ccc; }}
        .critical {{ border-left-color: #dc2626; background: #fef2f2; }}
        .high {{ border-left-color: #ea580c; background: #fff7ed; }}
        .medium {{ border-left-color: #ca8a04; background: #fefce8; }}
        .job-change {{ border-left-color: #16a34a; background: #f0fdf4; }}
        .exec {{ border-left-color: #2563eb; background: #eff6ff; }}
        .title {{ font-size: 18px; font-weight: bold; margin-bottom: 5px; }}
        .meta {{ font-size: 12px; color: #666; margin-bottom: 10px; }}
        .summary {{ font-size: 14px; }}
        .badge {{ display: inline-block; padding: 2px 8px; border-radius: 4px; font-size: 11px; font-weight: bold; margin-right: 5px; }}
        .badge-critical {{ background: #dc2626; color: white; }}
        .badge-high {{ background: #ea580c; color: white; }}
        .badge-medium {{ background: #ca8a04; color: white; }}
        .badge-job {{ background: #16a34a; color: white; }}
        .badge-exec {{ background: #2563eb; color: white; }}
        a {{ color: #2563eb; text-decoration: none; }}
        a:hover {{ text-decoration: underline; }}
        .stats {{ background: #f3f4f6; padding: 15px; border-radius: 8px; margin: 20px 0; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🏛️ Competitive Intelligence Report</h1>
        <p>{datetime.now().strftime("%A, %B %d, %Y")}</p>
    </div>
    
    <div class="stats">
        <strong>Today's Signals:</strong> 
        🔴 {len(critical)} Critical | 
        🟠 {len(high)} High | 
        🟡 {len(medium)} Medium |
        💼 {len(job_changes)} Job Changes |
        👔 {len(exec_news)} Executive Updates
    </div>
"""
    
    # Critical signals
    if critical:
        html += "<h2>🔴 Critical Signals</h2>"
        for article in critical:
            html += f"""
    <div class="section critical">
        <span class="badge badge-critical">CRITICAL</span>
        <span class="badge">{article.get('category', 'general')}</span>
        <div class="title"><a href="{article.get('link', '#')}">{article.get('title', 'No title')}</a></div>
        <div class="meta">Source: {article.get('source', 'Unknown')} | {article.get('published', 'Unknown date')}</div>
        <div class="summary">{article.get('summary', '')}</div>
    </div>
"""
    
    # Job changes
    if job_changes:
        html += "<h2>💼 Executive Job Changes</h2>"
        for update in job_changes:
            html += f"""
    <div class="section job-change">
        <span class="badge badge-job">JOB CHANGE</span>
        <span class="badge">{update.get('company', 'Unknown')}</span>
        <div class="title"><a href="{update.get('link', '#')}">{update.get('title', 'No title')}</a></div>
        <div class="meta">{update.get('published', 'Recent')}</div>
        <div class="summary">{update.get('description', '')}</div>
    </div>
"""
    
    # Executive news
    if exec_news:
        html += "<h2>👔 Executive Team Updates</h2>"
        for update in exec_news:
            html += f"""
    <div class="section exec">
        <span class="badge badge-exec">EXECUTIVE</span>
        <span class="badge">{update.get('company', 'Unknown')}</span>
        <div class="title">{update.get('executive', 'Unknown')} - {update.get('title', 'Update')}</div>
        <div class="meta"><a href="{update.get('link', '#')}">Read more</a></div>
        <div class="summary">{update.get('description', '')}</div>
    </div>
"""
    
    # High priority
    if high:
        html += "<h2>🟠 High Priority Signals</h2>"
        for article in high:
            html += f"""
    <div class="section high">
        <span class="badge badge-high">HIGH</span>
        <span class="badge">{article.get('category', 'general')}</span>
        <div class="title"><a href="{article.get('link', '#')}">{article.get('title', 'No title')}</a></div>
        <div class="meta">Source: {article.get('source', 'Unknown')} | {article.get('published', 'Unknown date')}</div>
        <div class="summary">{article.get('summary', '')}</div>
    </div>
"""
    
    # Company posts
    if company_posts:
        html += "<h2>📢 Company Announcements</h2>"
        for post in company_posts:
            html += f"""
    <div class="section medium">
        <span class="badge badge-medium">POST</span>
        <span class="badge">{post.get('company', 'Unknown')}</span>
        <div class="title"><a href="{post.get('link', '#')}">{post.get('title', 'No title')}</a></div>
        <div class="meta">{post.get('published', 'Recent')}</div>
        <div class="summary">{post.get('description', '')}</div>
    </div>
"""
    
    # Medium priority
    if medium:
        html += "<h2>🟡 Medium Priority</h2>"
        for article in medium:
            html += f"""
    <div class="section medium">
        <span class="badge badge-medium">MEDIUM</span>
        <span class="badge">{article.get('category', 'general')}</span>
        <div class="title"><a href="{article.get('link', '#')}">{article.get('title', 'No title')}</a></div>
        <div class="meta">Source: {article.get('source', 'Unknown')} | {article.get('published', 'Unknown date')}</div>
        <div class="summary">{article.get('summary', '')}</div>
    </div>
"""
    
    # No news
    if not any([critical, high, medium, job_changes, exec_news, company_posts]):
        html += """
    <div class="section">
        <p>No new competitive signals in the last 48 hours.</p>
        <p>This could mean:</p>
        <ul>
            <li>Quiet period in the industry</li>
            <li>Sources need refreshing (checking RSS feeds, search APIs)</li>
            <li>Weekend/holiday lull</li>
        </ul>
    </div>
"""
    
    html += """
    <hr>
    <p style="font-size: 12px; color: #666;">
        Generated by Cicero Competitive Intelligence System<br>
        Sources: Google Alerts, Web Search, LinkedIn Monitoring, Job Boards
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
    
    return str(EMAIL_OUTPUT)

if __name__ == "__main__":
    from datetime import timedelta
    generate_email()
