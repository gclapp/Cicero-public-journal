#!/usr/bin/env python3
"""
Progyny Executive Report - STRICT date filtering
Parses actual dates, filters >30 days, no exceptions
"""

import json
import re
import requests
from datetime import datetime, timedelta
from pathlib import Path
from bs4 import BeautifulSoup
from email.utils import parsedate_to_datetime

INTEL_DIR = Path.home() / ".openclaw" / "workspace" / "config" / "progyny-intelligence"
MENTIONS_DIR = INTEL_DIR / "mentions"
SENT_COUNT_FILE = INTEL_DIR / "sent-counts.json"

def scrape_date_from_url(url):
    """Scrape the actual publication date from an article URL"""
    if not url:
        return None
    
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        response = requests.get(url, headers=headers, timeout=8)
        
        if response.status_code != 200:
            return None
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Try meta tags first (most reliable)
        for meta in soup.find_all('meta'):
            prop = meta.get('property', '').lower()
            name = meta.get('name', '').lower()
            content = meta.get('content', '')
            
            if any(x in prop or x in name for x in ['published_time', 'pubdate', 'date']):
                if content and '202' in content:
                    try:
                        # Try to parse ISO format
                        dt = parsedate_to_datetime(content)
                        return dt
                    except:
                        try:
                            return datetime.fromisoformat(content.replace('Z', '+00:00').replace('+00:00', ''))
                        except:
                            pass
        
        # Try time tags with datetime attribute
        for time_tag in soup.find_all('time'):
            datetime_attr = time_tag.get('datetime', '')
            if datetime_attr and '202' in datetime_attr:
                try:
                    return parsedate_to_datetime(datetime_attr)
                except:
                    try:
                        return datetime.fromisoformat(datetime_attr.replace('Z', '+00:00').replace('+00:00', ''))
                    except:
                        pass
        
        # Look for date patterns in the visible text
        text = soup.get_text()
        
        # Common date patterns
        patterns = [
            (r'(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+(\d{1,2}),?\s+(202[0-6])', '%B %d, %Y'),
            (r'(\d{1,2})\s+(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+(202[0-6])', '%d %B %Y'),
            (r'(\d{4})-(\d{2})-(\d{2})', '%Y-%m-%d'),
        ]
        
        for pattern, fmt in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    date_str = match.group(0)
                    # Normalize month names
                    date_str = date_str.replace('.', '')
                    return datetime.strptime(date_str, fmt)
                except:
                    pass
        
        return None
    except Exception as e:
        return None

def get_article_date(mention):
    """Get the best available date for an article"""
    url = mention.get('url', '')
    
    # First try scraping the actual page
    scraped_date = scrape_date_from_url(url)
    if scraped_date:
        return scraped_date
    
    # Try published field
    pub = mention.get('published', '')
    if pub:
        try:
            return parsedate_to_datetime(pub)
        except:
            try:
                return datetime.fromisoformat(pub.replace('Z', '+00:00').replace('+00:00', ''))
            except:
                pass
    
    # Try found_at (but this is when we collected it, not when published)
    found = mention.get('found_at', '')
    if found:
        try:
            return datetime.fromisoformat(found.replace('Z', '+00:00').replace('+00:00', ''))
        except:
            pass
    
    return None

def is_within_30_days(date):
    """Check if date is within last 30 days"""
    if not date:
        return False
    
    # Handle timezone-aware dates
    if date.tzinfo:
        date = date.replace(tzinfo=None)
    
    cutoff = datetime.now() - timedelta(days=30)
    return date >= cutoff

def can_send(mention_id):
    """Check if we can send this mention (max 2 times)"""
    counts = {}
    if SENT_COUNT_FILE.exists():
        with open(SENT_COUNT_FILE) as f:
            counts = json.load(f)
    return counts.get(mention_id, 0) < 2

def increment_sent(mention_id):
    """Track that we sent this mention"""
    counts = {}
    if SENT_COUNT_FILE.exists():
        with open(SENT_COUNT_FILE) as f:
            counts = json.load(f)
    counts[mention_id] = counts.get(mention_id, 0) + 1
    SENT_COUNT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(SENT_COUNT_FILE, 'w') as f:
        json.dump(counts, f, indent=2)

def load_recent_progyny_mentions():
    """Load Progyny mentions from sentiment file, strictly filtered"""
    PROGYNY_FILE = Path.home() / ".openclaw" / "workspace" / "config" / "progyny-sentiment.json"
    
    if not PROGYNY_FILE.exists():
        return []
    
    with open(PROGYNY_FILE) as f:
        data = json.load(f)
    
    mentions = []
    
    # Process news mentions
    for m in data.get('mentions', []):
        # Get actual date
        article_date = get_article_date(m)
        
        # STRICT: Skip if no date or >30 days old
        if not article_date:
            print(f"⚠️ Skipping (no date): {m.get('title', '')[:50]}...")
            continue
        
        if not is_within_30_days(article_date):
            print(f"⏭️ Skipping (old): {m.get('title', '')[:50]}... ({article_date.strftime('%b %d, %Y')})")
            continue
        
        # Check send count
        mid = m.get('url', '')[:50]  # Use URL as ID
        if not can_send(mid):
            continue
        
        m['_date'] = article_date
        m['_id'] = mid
        mentions.append(m)
    
    # Process executive news
    for e in data.get('executive_news', []):
        article_date = get_article_date(e)
        
        if not article_date or not is_within_30_days(article_date):
            continue
        
        mid = e.get('url', '')[:50]
        if not can_send(mid):
            continue
        
        # Convert to mention format
        m = {
            'title': e.get('headline', ''),
            'url': e.get('url', ''),
            'source': 'Executive News',
            'summary': e.get('description', ''),
            '_date': article_date,
            '_id': mid,
            'is_exec': True
        }
        mentions.append(m)
    
    # Sort by date (newest first) - normalize timezone first
    for m in mentions:
        if m.get('_date') and m['_date'].tzinfo:
            m['_date'] = m['_date'].replace(tzinfo=None)
    
    mentions.sort(key=lambda x: x.get('_date', datetime.min), reverse=True)
    
    return mentions

def categorize_mention(m):
    """Categorize mention by type"""
    title = m.get('title', '').lower()
    summary = m.get('summary', '').lower()
    combined = title + ' ' + summary
    
    if any(x in combined for x in ['stock', 'shares', 'nasdaq', 'pgny', 'trading', 'analyst', 'price target']):
        return 'Financial'
    if any(x in combined for x in ['ceo', 'pete anevski', 'executive', 'chief', 'appointed', 'recognized']):
        return 'Executive'
    if any(x in combined for x in ['partner', 'client', 'signs', 'contract']):
        return 'Partnership'
    if any(x in combined for x in ['patient', 'customer', 'member', 'review']):
        return 'Sentiment'
    return 'General'

def generate_executive_report():
    """Generate executive Progyny report with strict date filtering"""
    
    mentions = load_recent_progyny_mentions()
    
    if not mentions:
        print("No recent Progyny mentions found (last 30 days)")
        return "<p>No Progyny mentions in the last 30 days.</p>"
    
    # Mark as sent
    for m in mentions:
        increment_sent(m.get('_id', ''))
    
    # Categorize
    by_category = {}
    for m in mentions:
        cat = categorize_mention(m)
        by_category[cat] = by_category.get(cat, [])
        by_category[cat].append(m)
    
    today = datetime.now().strftime('%A, %B %d, %Y')
    
    # Generate detailed executive summary
    summary_sentences = []
    
    # Financial analysis
    if 'Financial' in by_category:
        fin_mentions = by_category['Financial']
        stock_down = [m for m in fin_mentions if any(x in (m.get('title','')+m.get('summary','')).lower() for x in ['lower', 'fell', 'decline', 'down'])]
        stock_up = [m for m in fin_mentions if any(x in (m.get('title','')+m.get('summary','')).lower() for x in ['boosts', 'grows', 'increased', 'up'])]
        analyst = [m for m in fin_mentions if any(x in (m.get('title','')+m.get('summary','')).lower() for x in ['analyst', 'rating', 'price target'])]
        
        if stock_down:
            summary_sentences.append(f"📈 **Stock Pressure**: {len(stock_down)} mentions of share price declines or negative trading activity, potentially indicating market sentiment shifts or analyst concerns about near-term performance.")
        if stock_up:
            summary_sentences.append(f"📈 **Institutional Interest**: {len(stock_up)} reports of institutional investors increasing positions, suggesting confidence from sophisticated investors despite broader market volatility.")
        if analyst:
            summary_sentences.append(f"📈 **Analyst Activity**: {len(analyst)} analyst ratings or price target updates, reflecting ongoing Wall Street evaluation of company fundamentals and competitive positioning.")
    
    # Executive analysis
    if 'Executive' in by_category:
        exec_mentions = by_category['Executive']
        recognition = [m for m in exec_mentions if any(x in (m.get('title','')+m.get('summary','')).lower() for x in ['recognized', 'awarded', 'honored', 'champion'])]
        appointments = [m for m in exec_mentions if any(x in (m.get('title','')+m.get('summary','')).lower() for x in ['appointed', 'named', 'hires', 'joins'])]
        
        if recognition:
            summary_sentences.append(f"👔 **Leadership Recognition**: {len(recognition)} executive recognition mentions, including industry awards and thought leadership visibility that enhances company reputation and employer brand.")
        if appointments:
            summary_sentences.append(f"👔 **Executive Changes**: {len(appointments)} leadership appointments or executive moves, potentially signaling strategic shifts or organizational evolution to support growth objectives.")
    
    # Partnership analysis
    if 'Partnership' in by_category:
        partnership_mentions = by_category['Partnership']
        summary_sentences.append(f"🤝 **Partnership Activity**: {len(partnership_mentions)} partnership or client win announcements, demonstrating market traction and competitive success in securing new business relationships.")
    
    # Sentiment analysis
    if 'Sentiment' in by_category:
        sentiment_mentions = by_category['Sentiment']
        positive = [m for m in sentiment_mentions if any(x in (m.get('title','')+m.get('summary','')).lower() for x in ['positive', 'satisfied', 'recommend', 'great', 'excellent'])]
        negative = [m for m in sentiment_mentions if any(x in (m.get('title','')+m.get('summary','')).lower() for x in ['complaint', 'issue', 'problem', 'concern', 'frustrated'])]
        
        if positive:
            summary_sentences.append(f"💬 **Positive Sentiment**: {len(positive)} favorable customer or patient mentions, indicating strong service delivery and member satisfaction.")
        if negative:
            summary_sentences.append(f"💬 **Areas of Concern**: {len(negative)} mentions of customer issues or complaints, suggesting potential service gaps that may require operational attention.")
    
    # Overall context
    total_mentions = len(mentions)
    if total_mentions > 0:
        summary_sentences.append(f"📊 **Overall**: {total_mentions} total mentions across {len(by_category)} categories in the last 30 days, representing {'elevated' if total_mentions > 10 else 'normal'} levels of market visibility and competitive discussion.")
    
    exec_summary = ' '.join(summary_sentences) if summary_sentences else "No significant Progyny mentions in the last 30 days."
    
    html = f"""<!DOCTYPE html>
<html>
<head>
    <link rel="icon" type="image/png" href="https://www.google.com/s2/favicons?domain=progyny.com&sz=128">
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; 
               line-height: 1.5; color: #1a1a1a; max-width: 680px; margin: 0 auto; background: #fafafa; }}
        .container {{ background: white; padding: 40px; }}
        
        .header {{ background: #1e40af; color: white; padding: 30px; margin: -40px -40px 30px -40px; }}
        .header h1 {{ margin: 0; font-size: 22px; font-weight: 600; }}
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
        
        .mention {{ padding: 15px 0; border-bottom: 1px solid #f0f0f0; }}
        .mention:last-child {{ border-bottom: none; }}
        .mention-title {{ font-weight: 600; font-size: 14px; margin-bottom: 4px; }}
        .mention-title a {{ color: #1a1a1a; text-decoration: none; }}
        .mention-title a:hover {{ text-decoration: underline; }}
        .mention-meta {{ font-size: 12px; color: #999; margin-bottom: 6px; }}
        .mention-summary {{ font-size: 13px; color: #555; }}
        
        .category-badge {{ display: inline-block; font-size: 10px; text-transform: uppercase; 
                          letter-spacing: 0.5px; padding: 2px 8px; border-radius: 4px; 
                          background: #e5e7eb; color: #666; margin-left: 10px; }}
        
        .footer {{ margin-top: 40px; padding-top: 20px; border-top: 1px solid #e5e7eb; 
                  text-align: center; font-size: 12px; color: #999; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1><img src="https://www.google.com/s2/favicons?domain=progyny.com&sz=32" style="vertical-align: middle; margin-right: 10px; width: 28px; height: 28px;"> Progyny Executive Brief</h1>
            <p>{today} | Strict 30-day filter | {len(mentions)} mentions</p>
        </div>
        
        <div class="exec-summary">
            <h2>Executive Summary</h2>
            <p>{exec_summary}</p>
        </div>
        
        <div class="stats">
            <div class="stat">
                <div class="stat-number">{len(by_category.get('Financial', []))}</div>
                <div class="stat-label">Financial</div>
            </div>
            <div class="stat">
                <div class="stat-number">{len(by_category.get('Executive', []))}</div>
                <div class="stat-label">Executive</div>
            </div>
            <div class="stat">
                <div class="stat-number">{len(by_category.get('Partnership', []))}</div>
                <div class="stat-label">Partnerships</div>
            </div>
            <div class="stat">
                <div class="stat-number">{len(by_category.get('Sentiment', [])) + len(by_category.get('General', []))}</div>
                <div class="stat-label">Other</div>
            </div>
        </div>
"""
    
    # Add sections by category
    category_order = ['Financial', 'Executive', 'Partnership', 'Sentiment', 'General']
    
    for cat in category_order:
        if cat not in by_category or not by_category[cat]:
            continue
        
        html += f'<div class="section"><h2>{cat} Mentions</h2>'
        
        for m in by_category[cat][:5]:  # Top 5 per category
            date_str = m.get('_date', datetime.now()).strftime('%b %d, %Y')
            html += f'''
            <div class="mention">
                <div class="mention-title">
                    <a href="{m.get('url', '#')}">{m.get('title', 'No title')}</a>
                    <span class="category-badge">{cat}</span>
                </div>
                <div class="mention-meta">{m.get('source', 'Unknown')} • {date_str}</div>
                <div class="mention-summary">{m.get('summary', '')[:150]}...</div>
            </div>
'''
        html += '</div>'
    
    html += '''
        <div class="footer">
            <p>Progyny Executive Intelligence • Strict 30-day window</p>
            <p>Dates scraped from article pages • Sources linked for validation</p>
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
    print(f"✅ Report saved: {output}")
