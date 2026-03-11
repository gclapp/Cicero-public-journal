#!/usr/bin/env python3
"""
Competitive Intelligence Email Generator
Reads new articles from monitor and generates HTML email content
Includes PGNY alongside competitors as requested
"""

import json
import os
from datetime import datetime

NEW_ARTICLES_FILE = os.path.expanduser("~/.openclaw/workspace/config/competitor-new-articles.json")

def is_pgn_article(article):
    """Check if article is about Progyny/PGNY"""
    source = article.get('source', '').lower()
    title = article.get('title', '').lower()
    return 'progyny' in source or 'pgny' in source or 'progyny' in title

def generate_email_content():
    """Generate HTML email content from new articles"""
    
    if not os.path.exists(NEW_ARTICLES_FILE):
        return None, 0
    
    with open(NEW_ARTICLES_FILE, 'r') as f:
        articles = json.load(f)
    
    if not articles:
        return None, 0
    
    # Separate PGNY from competitors
    pgn_articles = [a for a in articles if is_pgn_article(a)]
    competitor_articles = [a for a in articles if not is_pgn_article(a)]
    
    # Priority breakdown for all articles
    high_priority = [a for a in articles if a['priority'] == 'high']
    medium_priority = [a for a in articles if a['priority'] == 'medium']
    low_priority = [a for a in articles if a['priority'] == 'low']
    
    html = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .header {{ background: #1a1a2e; color: white; padding: 20px; text-align: center; }}
        .section {{ margin: 20px 0; padding: 15px; border-radius: 5px; }}
        .pgn-section {{ background: #e6f3ff; border-left: 4px solid #0066cc; }}
        .high {{ background: #ffe6e6; border-left: 4px solid #cc0000; }}
        .medium {{ background: #fff4e6; border-left: 4px solid #ff9900; }}
        .low {{ background: #f0f0f0; border-left: 4px solid #666; }}
        .article {{ margin: 10px 0; padding: 10px; background: white; border-radius: 3px; }}
        .source {{ font-size: 0.85em; color: #666; }}
        .pgn-badge {{ background: #0066cc; color: white; padding: 2px 8px; border-radius: 3px; font-size: 0.75em; }}
        .comp-badge {{ background: #666; color: white; padding: 2px 8px; border-radius: 3px; font-size: 0.75em; }}
        .link {{ color: #0066cc; text-decoration: none; }}
        .link:hover {{ text-decoration: underline; }}
        .summary {{ font-size: 0.9em; color: #555; margin-top: 5px; }}
        h2 {{ margin-top: 0; }}
        .stats {{ background: #f9f9f9; padding: 10px; border-radius: 5px; margin: 10px 0; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🎯 Competitive Intelligence Report</h1>
        <p>{datetime.now().strftime('%B %d, %Y')}</p>
        <p><small>Monitoring: Progyny + 5 Competitors</small></p>
    </div>
    
    <div class="stats">
        <strong>📊 Summary:</strong> {len(articles)} total articles | 
        <span style="color: #cc0000;">{len(high_priority)} High</span> | 
        <span style="color: #ff9900;">{len(medium_priority)} Medium</span> | 
        <span style="color: #666;">{len(low_priority)} General</span>
    </div>
"""
    
    # PGNY Section - Featured prominently
    if pgn_articles:
        html += f"""
    <div class="section pgn-section">
        <h2>🔷 Progyny (PGNY) News ({len(pgn_articles)} items)</h2>
"""
        # Sort PGNY by priority
        pgn_high = [a for a in pgn_articles if a['priority'] == 'high']
        pgn_medium = [a for a in pgn_articles if a['priority'] == 'medium']
        pgn_low = [a for a in pgn_articles if a['priority'] == 'low']
        
        for article in pgn_high + pgn_medium + pgn_low:
            priority_badge = "🔴" if article['priority'] == 'high' else "🟡" if article['priority'] == 'medium' else "⚪"
            html += f"""
        <div class="article">
            <span class="pgn-badge">PGNY</span> {priority_badge} 
            <strong><a href="{article['link']}" class="link">{article['title']}</a></strong>
            <div class="source">{article['category']} | {article.get('published', 'Recent')}</div>
            {f'<div class="summary">{article.get("summary", "")[:200]}...</div>' if article.get('summary') else ''}
        </div>
"""
        html += "    </div>\n"
    
    # Competitor Section
    if competitor_articles:
        comp_high = [a for a in competitor_articles if a['priority'] == 'high']
        comp_medium = [a for a in competitor_articles if a['priority'] == 'medium']
        comp_low = [a for a in competitor_articles if a['priority'] == 'low']
        
        if comp_high:
            html += f"""
    <div class="section high">
        <h2>🔴 Competitor - High Priority ({len(comp_high)} items)</h2>
"""
            for article in comp_high:
                html += f"""
        <div class="article">
            <span class="comp-badge">{article['source'].replace(' - Google Alerts', '')}</span>
            <strong><a href="{article['link']}" class="link">{article['title']}</a></strong>
            <div class="source">{article['category']} | {article.get('published', 'Recent')}</div>
        </div>
"""
            html += "    </div>\n"
        
        if comp_medium:
            html += f"""
    <div class="section medium">
        <h2>🟡 Competitor - Medium Priority ({len(comp_medium)} items)</h2>
"""
            for article in comp_medium:
                html += f"""
        <div class="article">
            <span class="comp-badge">{article['source'].replace(' - Google Alerts', '')}</span>
            <strong><a href="{article['link']}" class="link">{article['title']}</a></strong>
            <div class="source">{article['category']} | {article.get('published', 'Recent')}</div>
        </div>
"""
            html += "    </div>\n"
        
        if comp_low:
            html += f"""
    <div class="section low">
        <h2>⚪ Competitor - General News ({len(comp_low)} items)</h2>
"""
            for article in comp_low:
                html += f"""
        <div class="article">
            <span class="comp-badge">{article['source'].replace(' - Google Alerts', '')}</span>
            <strong><a href="{article['link']}" class="link">{article['title']}</a></strong>
            <div class="source">{article.get('published', 'Recent')}</div>
        </div>
"""
            html += "    </div>\n"
    
    html += """
    <div style="margin-top: 30px; padding: 15px; background: #f9f9f9; border-radius: 5px; font-size: 0.85em; color: #666;">
        <strong>Monitored Entities:</strong> Progyny (PGNY), Maven, Carrot, KindBody, WIN Fertility, Pomelo Health<br>
        <strong>Sources:</strong> Google Alerts RSS feeds | <strong>Schedule:</strong> Daily 6:00 AM PT
    </div>
</body>
</html>
"""
    
    return html, len(articles)

def main():
    html, count = generate_email_content()
    
    if html:
        # Save HTML for email script to use
        html_file = os.path.expanduser("~/.openclaw/workspace/config/competitor-email.html")
        with open(html_file, 'w') as f:
            f.write(html)
        print(f"Generated email with {count} articles: {html_file}")
        return html_file
    else:
        print("No new articles to report")
        return None

if __name__ == "__main__":
    main()
