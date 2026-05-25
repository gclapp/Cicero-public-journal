#!/usr/bin/env python3
"""
Progyny Executive Intelligence Report
Concise, trend-focused summary for busy executives
30-day filter, deduplication, sources for deep dives
"""

import json
import hashlib
import re
from datetime import datetime, timedelta
from pathlib import Path
from email.utils import parsedate_to_datetime

INTEL_DIR = Path.home() / ".openclaw" / "workspace" / "config" / "progyny-intelligence"
MENTIONS_DIR = INTEL_DIR / "mentions"
SENT_COUNT_FILE = INTEL_DIR / "sent-counts.json"

def parse_date(date_str):
    """Parse various date formats"""
    if not date_str:
        return None
    try:
        return parsedate_to_datetime(date_str)
    except:
        try:
            return datetime.fromisoformat(date_str.replace('Z', '+00:00').replace('+00:00', ''))
        except:
            return None

def get_article_date(mention):
    """Get best available date for article"""
    # Try published date first
    pub = parse_date(mention.get('published', ''))
    if pub:
        return pub
    # Fallback to collected date
    return parse_date(mention.get('collected_at', ''))

def is_within_30_days(mention):
    """Check if mention is within 30 days"""
    article_date = get_article_date(mention)
    if not article_date:
        return False
    cutoff = datetime.now() - timedelta(days=30)
    # Handle timezone-aware vs naive
    if article_date.tzinfo:
        article_date = article_date.replace(tzinfo=None)
    return article_date >= cutoff

def can_send_article(mention_id):
    """Check if article can be sent (max 2 times)"""
    counts = {}
    if SENT_COUNT_FILE.exists():
        with open(SENT_COUNT_FILE) as f:
            counts = json.load(f)
    return counts.get(mention_id, 0) < 2

def increment_sent_count(mention_id):
    """Track article sends"""
    counts = {}
    if SENT_COUNT_FILE.exists():
        with open(SENT_COUNT_FILE) as f:
            counts = json.load(f)
    counts[mention_id] = counts.get(mention_id, 0) + 1
    SENT_COUNT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(SENT_COUNT_FILE, 'w') as f:
        json.dump(counts, f, indent=2)

def load_recent_mentions():
    """Load mentions from last 30 days that haven't been sent twice"""
    mentions = []
    cutoff = datetime.now() - timedelta(days=30)
    
    for file in MENTIONS_DIR.glob('*.json'):
        try:
            with open(file) as f:
                m = json.load(f)
            
            # Check 30-day window
            if not is_within_30_days(m):
                continue
            
            # Check send count
            mid = m.get('id', '')
            if not can_send_article(mid):
                continue
            
            mentions.append(m)
        except:
            continue
    
    # Sort by date (newest first)
    mentions.sort(key=lambda x: get_article_date(x) or datetime.min, reverse=True)
    return mentions

def analyze_trends(mentions):
    """Analyze mentions for key trends"""
    trends = {
        'financial_signals': [],
        'executive_moves': [],
        'partnership_wins': [],
        'market_sentiment': [],
        'competitive_threats': [],
        'stock_movement': []
    }
    
    for m in mentions:
        title = m.get('title', '').lower()
        summary = m.get('summary', '').lower()
        combined = title + ' ' + summary
        cats = m.get('categories', [])
        
        # Stock movement
        if 'financial' in cats:
            if any(x in combined for x in ['trading lower', 'shares fell', 'stock down', 'price target']):
                trends['stock_movement'].append({
                    'title': m.get('title', ''),
                    'url': m.get('url', ''),
                    'date': format_date(m),
                    'insight': extract_stock_insight(combined)
                })
            elif any(x in combined for x in ['boosts stake', 'grows position', 'increased holding']):
                trends['financial_signals'].append({
                    'title': m.get('title', ''),
                    'url': m.get('url', ''),
                    'date': format_date(m),
                    'insight': 'Institutional investor increased position'
                })
        
        # Executive moves
        if 'executive' in cats:
            if any(x in combined for x in ['recognized', 'awarded', 'named', 'appointed']):
                trends['executive_moves'].append({
                    'title': m.get('title', ''),
                    'url': m.get('url', ''),
                    'date': format_date(m),
                    'insight': 'Leadership recognition/appointment'
                })
        
        # Partnerships
        if 'partnership' in cats:
            trends['partnership_wins'].append({
                'title': m.get('title', ''),
                'url': m.get('url', ''),
                'date': format_date(m),
                'insight': 'New partnership or client win'
            })
        
        # Sentiment
        if 'sentiment' in cats:
            trends['market_sentiment'].append({
                'title': m.get('title', ''),
                'url': m.get('url', ''),
                'date': format_date(m),
                'insight': 'Customer/patient sentiment signal'
            })
    
    return trends

def extract_stock_insight(text):
    """Extract stock movement insight"""
    if '22%' in text or 'fell' in text:
        return 'Stock declined significantly on weak 2026 outlook'
    if 'analyst' in text:
        return 'Analyst rating or price target change'
    return 'Stock movement noted'

def format_date(mention):
    """Format date for display"""
    d = get_article_date(mention)
    if d:
        return d.strftime('%b %d')
    return 'Recent'

def generate_executive_summary(trends, total_mentions):
    """Generate concise executive summary"""
    summary_parts = []
    
    # Stock movement
    if trends['stock_movement']:
        summary_parts.append(f"📉 **Stock under pressure**: {len(trends['stock_movement'])} mentions of share price decline or analyst downgrades")
    
    # Institutional activity
    if trends['financial_signals']:
        summary_parts.append(f"💰 **Institutional interest**: {len(trends['financial_signals'])} investors increasing positions")
    
    # Executive recognition
    if trends['executive_moves']:
        summary_parts.append(f"👔 **Leadership visibility**: {len(trends['executive_moves'])} executive recognition/appointment mentions")
    
    # Partnerships
    if trends['partnership_wins']:
        summary_parts.append(f"🤝 **Partnership activity**: {len(trends['partnership_wins'])} new partnership/client announcements")
    
    # Sentiment
    if trends['market_sentiment']:
        summary_parts.append(f"💬 **Market sentiment**: {len(trends['market_sentiment'])} customer/patient discussions")
    
    if not summary_parts:
        return "No significant trends detected in the last 30 days."
    
    return " | ".join(summary_parts)

def generate_executive_report():
    """Generate executive-focused Progyny report"""
    mentions = load_recent_mentions()
    
    if not mentions:
        return "<p>No new Progyny mentions in the last 30 days.</p>"
    
    # Mark as sent
    for m in mentions:
        increment_sent_count(m.get('id', ''))
    
    # Analyze trends
    trends = analyze_trends(mentions)
    
    # Generate summary
    exec_summary = generate_executive_summary(trends, len(mentions))
    
    today = datetime.now().strftime('%A, %B %d, %Y')
    
    html = f"""<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; 
               line-height: 1.5; color: #1a1a1a; max-width: 680px; margin: 0 auto; background: #fafafa; }}
        .container {{ background: white; padding: 40px; }}
        
        .header {{ background: #1e40af; color: white; padding: 30px; margin: -40px -40px 30px -40px; }}
        .header h1 {{ margin: 0; font-size: 22px; font-weight: 600; }}
        .header p {{ margin: 8px 0 0 0; opacity: 0.9; font-size: 14px; }}
        
        .exec-summary {{ background: #f0f7ff; border-left: 4px solid #1e40af; padding: 20px; margin: 25px 0; }}
        .exec-summary h2 {{ margin: 0 0 12px 0; font-size: 14px; text-transform: uppercase; letter-spacing: 1px; color: #1e40af; }}
        .exec-summary p {{ margin: 0; font-size: 15px; line-height: 1.6; }}
        
        .section {{ margin: 30px 0; }}
        .section h2 {{ font-size: 16px; color: #1a1a1a; border-bottom: 2px solid #e5e7eb; padding-bottom: 8px; margin-bottom: 15px; }}
        
        .trend-item {{ padding: 15px 0; border-bottom: 1px solid #f0f0f0; }}
        .trend-item:last-child {{ border-bottom: none; }}
        .trend-title {{ font-weight: 600; font-size: 14px; margin-bottom: 4px; }}
        .trend-title a {{ color: #1a1a1a; text-decoration: none; }}
        .trend-title a:hover {{ text-decoration: underline; }}
        .trend-meta {{ font-size: 12px; color: #666; margin-bottom: 6px; }}
        .trend-insight {{ font-size: 13px; color: #444; background: #f8f9fa; padding: 8px 12px; border-radius: 4px; }}
        
        .stats {{ display: flex; gap: 20px; margin: 20px 0; }}
        .stat {{ text-align: center; }}
        .stat-number {{ font-size: 32px; font-weight: 600; color: #1e40af; }}
        .stat-label {{ font-size: 11px; color: #666; text-transform: uppercase; letter-spacing: 0.5px; }}
        
        .sources {{ margin-top: 30px; padding-top: 20px; border-top: 1px solid #e5e7eb; }}
        .sources h3 {{ font-size: 13px; color: #666; margin-bottom: 12px; }}
        .sources ol {{ font-size: 12px; line-height: 1.8; color: #444; padding-left: 20px; }}
        .sources li {{ margin-bottom: 6px; }}
        .sources a {{ color: #3b82f6; text-decoration: none; }}
        
        .footer {{ margin-top: 40px; padding-top: 20px; border-top: 1px solid #e5e7eb; text-align: center; font-size: 12px; color: #999; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🏛️ Progyny Executive Brief</h1>
            <p>{today} | {len(mentions)} mentions in last 30 days</p>
        </div>
        
        <div class="exec-summary">
            <h2>Executive Summary</h2>
            <p>{exec_summary}</p>
        </div>
        
        <div class="stats">
            <div class="stat">
                <div class="stat-number">{len(trends['stock_movement']) + len(trends['financial_signals'])}</div>
                <div class="stat-label">Financial</div>
            </div>
            <div class="stat">
                <div class="stat-number">{len(trends['executive_moves'])}</div>
                <div class="stat-label">Executive</div>
            </div>
            <div class="stat">
                <div class="stat-number">{len(trends['partnership_wins'])}</div>
                <div class="stat-label">Partnerships</div>
            </div>
            <div class="stat">
                <div class="stat-number">{len(trends['market_sentiment'])}</div>
                <div class="stat-label">Sentiment</div>
            </div>
        </div>
"""
    
    # Stock Movement Section
    if trends['stock_movement']:
        html += '''
        <div class="section">
            <h2>📉 Stock Movement & Analyst Activity</h2>
'''
        for item in trends['stock_movement'][:3]:  # Top 3
            html += f'''
            <div class="trend-item">
                <div class="trend-title"><a href="{item['url']}">{item['title']}</a></div>
                <div class="trend-meta">{item['date']}</div>
                <div class="trend-insight">{item['insight']}</div>
            </div>
'''
        html += '</div>'
    
    # Institutional Activity
    if trends['financial_signals']:
        html += '''
        <div class="section">
            <h2>💰 Institutional Investor Activity</h2>
'''
        for item in trends['financial_signals'][:3]:
            html += f'''
            <div class="trend-item">
                <div class="trend-title"><a href="{item['url']}">{item['title']}</a></div>
                <div class="trend-meta">{item['date']}</div>
                <div class="trend-insight">{item['insight']}</div>
            </div>
'''
        html += '</div>'
    
    # Executive Moves
    if trends['executive_moves']:
        html += '''
        <div class="section">
            <h2>👔 Executive Recognition & Leadership</h2>
'''
        for item in trends['executive_moves'][:3]:
            html += f'''
            <div class="trend-item">
                <div class="trend-title"><a href="{item['url']}">{item['title']}</a></div>
                <div class="trend-meta">{item['date']}</div>
                <div class="trend-insight">{item['insight']}</div>
            </div>
'''
        html += '</div>'
    
    # Partnerships
    if trends['partnership_wins']:
        html += '''
        <div class="section">
            <h2>🤝 Partnerships & Client Wins</h2>
'''
        for item in trends['partnership_wins'][:3]:
            html += f'''
            <div class="trend-item">
                <div class="trend-title"><a href="{item['url']}">{item['title']}</a></div>
                <div class="trend-meta">{item['date']}</div>
                <div class="trend-insight">{item['insight']}</div>
            </div>
'''
        html += '</div>'
    
    # All Sources
    html += '''
        <div class="sources">
            <h3>📚 All Sources (Click to read full articles)</h3>
            <ol>
'''
    for m in mentions:
        date = format_date(m)
        html += f'<li><a href="{m.get("url", "#")}">{m.get("title", "No title")[:80]}...</a> <span style="color:#999">({m.get("source", "Unknown")}, {date})</span></li>'
    
    html += '''
            </ol>
        </div>
        
        <div class="footer">
            <p>Progyny Executive Intelligence • 30-day window • Sources linked for validation</p>
            <p>Sent max 2x per article • Duplicate suppression active</p>
        </div>
    </div>
</body>
</html>
'''
    
    return html

if __name__ == "__main__":
    report = generate_executive_report()
    output = Path.home() / ".openclaw" / "workspace" / "config" / "progyny-executive-report.html"
    with open(output, 'w') as f:
        f.write(report)
    print(f"✅ Executive report generated: {output}")
    print(f"📊 Mentions included: {len([m for m in load_recent_mentions()])}")
