#!/usr/bin/env python3
"""
Progyny Intelligence Collector
Daily collection and storage of all Progyny mentions with full metadata
"""

import json
import hashlib
from datetime import datetime, timedelta
from pathlib import Path

# Paths
INTEL_DIR = Path.home() / ".openclaw" / "workspace" / "config" / "progyny-intelligence"
MENTIONS_DIR = INTEL_DIR / "mentions"
TRENDS_FILE = INTEL_DIR / "trends.json"
SOURCES_INDEX = INTEL_DIR / "sources-index.json"
WEEKLY_DIR = INTEL_DIR / "weekly-summaries"

# Ensure directories exist
MENTIONS_DIR.mkdir(parents=True, exist_ok=True)
WEEKLY_DIR.mkdir(parents=True, exist_ok=True)

def generate_mention_id(mention):
    """Generate unique ID for a mention"""
    content = f"{mention.get('title', '')}:{mention.get('url', '')}:{mention.get('published', '')}"
    return hashlib.md5(content.encode()).hexdigest()[:12]

def categorize_mention(mention):
    """Categorize mention by type"""
    title = mention.get('title', '').lower()
    summary = mention.get('summary', '').lower()
    combined = title + ' ' + summary
    
    categories = []
    
    # Financial/Stock
    if any(term in combined for term in ['stock', 'shares', 'earnings', 'revenue', 'analyst', 'rating', 'price target', 'nasdaq', 'pgny', 'investor', 'stake', 'holding']):
        categories.append('financial')
    
    # Executive/Leadership
    if any(term in combined for term in ['pete anevski', 'ceo', 'chief', 'executive', 'leadership', 'board', 'appointed']):
        categories.append('executive')
    
    # Product/Service
    if any(term in combined for term in ['product', 'service', 'platform', 'app', 'launch', 'feature', 'offering', 'solution']):
        categories.append('product')
    
    # Partnerships/Clients
    if any(term in combined for term in ['partner', 'client', 'employer', 'contract', 'renewal', 'signs', 'select', 'fully insured']):
        categories.append('partnership')
    
    # Competitive
    if any(term in combined for term in ['competitor', 'competition', 'market share', 'vs', 'compared to', 'maven', 'carrot', 'kindbody']):
        categories.append('competitive')
    
    # Market/Sentiment
    if any(term in combined for term in ['patient', 'member', 'customer', 'review', 'experience', 'satisfaction', 'complaint']):
        categories.append('sentiment')
    
    # Regulatory/Policy
    if any(term in combined for term in ['legislation', 'policy', 'regulation', 'mandate', 'coverage', 'insurance', 'benefit']):
        categories.append('regulatory')
    
    if not categories:
        categories.append('general')
    
    return categories

def extract_key_insights(mention):
    """Extract key insights from mention text"""
    title = mention.get('title', '')
    summary = mention.get('summary', '')
    combined = f"{title}. {summary}"
    
    insights = []
    
    # Financial metrics
    if 'million' in combined.lower() or 'billion' in combined.lower():
        # Try to extract dollar amounts
        import re
        amounts = re.findall(r'\$[\d,]+(?:\.\d+)?\s*(?:million|billion)?', combined, re.IGNORECASE)
        if amounts:
            insights.append(f"Financial: {', '.join(amounts[:2])}")
    
    # Percentage changes
    if '%' in combined:
        import re
        pct = re.findall(r'\d+(?:\.\d+)?%', combined)
        if pct:
            insights.append(f"Metrics: {', '.join(pct[:2])}")
    
    # Key actions
    if any(word in combined.lower() for word in ['announces', 'launches', 'partners', 'acquires', 'appoints']):
        action_words = [w for w in ['announces', 'launches', 'partners', 'acquires', 'appoints', 'expands'] if w in combined.lower()]
        if action_words:
            insights.append(f"Action: {action_words[0].title()}")
    
    return insights

def store_mention(mention, source_type='news'):
    """Store a single mention with full metadata"""
    mention_id = generate_mention_id(mention)
    
    # Check if already stored
    mention_file = MENTIONS_DIR / f"{mention_id}.json"
    if mention_file.exists():
        return None  # Already stored
    
    # Enrich mention data
    enriched = {
        'id': mention_id,
        'title': mention.get('title', ''),
        'url': mention.get('url', ''),
        'source': mention.get('source', 'Unknown'),
        'source_type': source_type,
        'published': mention.get('published', ''),
        'published_date': mention.get('published_date', ''),
        'summary': mention.get('summary', '')[:500],
        'categories': categorize_mention(mention),
        'insights': extract_key_insights(mention),
        'collected_at': datetime.now().isoformat(),
        'date_key': datetime.now().strftime('%Y-%m-%d')
    }
    
    # Save individual mention
    with open(mention_file, 'w') as f:
        json.dump(enriched, f, indent=2)
    
    # Update sources index
    update_sources_index(enriched)
    
    return enriched

def update_sources_index(mention):
    """Update master sources index"""
    index = {}
    if SOURCES_INDEX.exists():
        with open(SOURCES_INDEX) as f:
            index = json.load(f)
    
    url = mention.get('url', '')
    if url:
        index[mention['id']] = {
            'url': url,
            'title': mention.get('title', '')[:100],
            'source': mention.get('source', 'Unknown'),
            'date': mention.get('published_date', ''),
            'categories': mention.get('categories', [])
        }
        
        with open(SOURCES_INDEX, 'w') as f:
            json.dump(index, f, indent=2)

def load_all_mentions(days=30):
    """Load all mentions from last N days"""
    mentions = []
    cutoff = datetime.now() - timedelta(days=days)
    
    for file in MENTIONS_DIR.glob('*.json'):
        try:
            with open(file) as f:
                m = json.load(f)
                collected = datetime.fromisoformat(m.get('collected_at', '2000-01-01'))
                if collected >= cutoff:
                    mentions.append(m)
        except:
            continue
    
    # Sort by collected date
    mentions.sort(key=lambda x: x.get('collected_at', ''), reverse=True)
    return mentions

def generate_daily_digest():
    """Generate daily digest of new mentions"""
    today = datetime.now().strftime('%Y-%m-%d')
    mentions = load_all_mentions(days=1)
    
    if not mentions:
        return None
    
    digest = {
        'date': today,
        'total_mentions': len(mentions),
        'by_category': {},
        'mentions': mentions
    }
    
    for m in mentions:
        for cat in m.get('categories', ['general']):
            if cat not in digest['by_category']:
                digest['by_category'][cat] = []
            digest['by_category'][cat].append(m)
    
    return digest

def generate_weekly_summary():
    """Generate weekly trend summary"""
    week_start = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
    week_end = datetime.now().strftime('%Y-%m-%d')
    mentions = load_all_mentions(days=7)
    
    if not mentions:
        return None
    
    # Analyze trends
    categories = {}
    sources = {}
    key_themes = []
    
    for m in mentions:
        # Category counts
        for cat in m.get('categories', ['general']):
            categories[cat] = categories.get(cat, 0) + 1
        
        # Source counts
        src = m.get('source', 'Unknown')
        sources[src] = sources.get(src, 0) + 1
        
        # Collect insights
        key_themes.extend(m.get('insights', []))
    
    summary = {
        'week_start': week_start,
        'week_end': week_end,
        'total_mentions': len(mentions),
        'category_breakdown': categories,
        'top_sources': dict(sorted(sources.items(), key=lambda x: x[1], reverse=True)[:5]),
        'key_themes': list(set(key_themes))[:10],  # Unique themes
        'notable_mentions': mentions[:5],  # Top 5 most recent
        'all_mentions': [{
            'id': m['id'],
            'title': m['title'][:80],
            'url': m['url'],
            'source': m['source'],
            'date': m.get('published_date', ''),
            'categories': m['categories'],
            'insights': m['insights']
        } for m in mentions]
    }
    
    # Save weekly summary
    week_file = WEEKLY_DIR / f"week-{week_start}-to-{week_end}.json"
    with open(week_file, 'w') as f:
        json.dump(summary, f, indent=2)
    
    return summary

def format_weekly_email(summary):
    """Format weekly summary as HTML email"""
    if not summary:
        return "<p>No Progyny mentions this week.</p>"
    
    html = f"""<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; 
               line-height: 1.5; color: #1a1a1a; max-width: 700px; margin: 0 auto; }}
        .header {{ background: #1e40af; color: white; padding: 25px; text-align: center; }}
        .header h1 {{ margin: 0; font-size: 24px; }}
        .header p {{ margin: 8px 0 0 0; opacity: 0.9; }}
        .section {{ margin: 25px 0; padding: 20px; border-left: 4px solid #1e40af; background: #f8fafc; }}
        .section h2 {{ margin-top: 0; color: #1e40af; font-size: 18px; }}
        .stat-grid {{ display: flex; gap: 15px; flex-wrap: wrap; margin: 15px 0; }}
        .stat-box {{ background: white; padding: 15px; border-radius: 8px; text-align: center; min-width: 120px; }}
        .stat-number {{ font-size: 28px; font-weight: bold; color: #1e40af; }}
        .stat-label {{ font-size: 11px; color: #666; text-transform: uppercase; }}
        .theme {{ background: #dbeafe; padding: 8px 12px; border-radius: 4px; margin: 5px 0; font-size: 13px; }}
        .mention {{ padding: 15px; border-bottom: 1px solid #e5e7eb; }}
        .mention:last-child {{ border-bottom: none; }}
        .mention-title {{ font-weight: 600; margin-bottom: 5px; }}
        .mention-title a {{ color: #1a1a1a; text-decoration: none; }}
        .mention-title a:hover {{ text-decoration: underline; }}
        .mention-meta {{ font-size: 12px; color: #666; margin-bottom: 8px; }}
        .mention-cats {{ font-size: 11px; }}
        .cat-badge {{ display: inline-block; background: #e5e7eb; padding: 2px 8px; border-radius: 3px; margin-right: 5px; }}
        .source-link {{ font-size: 11px; color: #3b82f6; }}
        .footer {{ margin-top: 30px; padding: 15px; background: #f3f4f6; text-align: center; font-size: 12px; color: #666; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🏛️ Progyny Weekly Intelligence Report</h1>
        <p>{summary['week_start']} to {summary['week_end']}</p>
    </div>
    
    <div class="section">
        <h2>📊 Weekly Snapshot</h2>
        <div class="stat-grid">
            <div class="stat-box">
                <div class="stat-number">{summary['total_mentions']}</div>
                <div class="stat-label">Total Mentions</div>
            </div>
"""
    
    # Add category stats
    for cat, count in sorted(summary['category_breakdown'].items(), key=lambda x: x[1], reverse=True)[:4]:
        html += f'''
            <div class="stat-box">
                <div class="stat-number">{count}</div>
                <div class="stat-label">{cat.title()}</div>
            </div>
'''
    
    html += """
        </div>
    </div>
    
    <div class="section">
        <h2>🔍 Key Themes This Week</h2>
"""
    
    for theme in summary['key_themes'][:8]:
        html += f'<div class="theme">{theme}</div>'
    
    html += """
    </div>
    
    <div class="section">
        <h2>📰 Notable Mentions</h2>
"""
    
    for m in summary['notable_mentions']:
        cats = ' '.join([f'<span class="cat-badge">{c}</span>' for c in m.get('categories', ['general'])])
        html += f'''
        <div class="mention">
            <div class="mention-title"><a href="{m.get('url', '#')}">{m.get('title', 'No title')}</a></div>
            <div class="mention-meta">{m.get('source', 'Unknown')} • {m.get('published_date', 'Recent')}</div>
            <div class="mention-cats">{cats}</div>
        </div>
'''
    
    html += f"""
    </div>
    
    <div class="section">
        <h2>📚 All Sources This Week</h2>
        <p style="font-size: 13px; color: #666;">Complete list of all {summary['total_mentions']} mentions with links:</p>
        <ol style="font-size: 12px; line-height: 1.8;">
"""
    
    for m in summary['all_mentions']:
        html += f'<li><a href="{m["url"]}">{m["title"]}</a> <span style="color: #999;">({m["source"]})</span></li>'
    
    html += """
        </ol>
    </div>
    
    <div class="footer">
        <p>Progyny Intelligence System • Daily Collection • Weekly Summary</p>
        <p>All mentions stored with full source links for validation</p>
    </div>
</body>
</html>
"""
    
    return html

if __name__ == "__main__":
    # Test: Generate weekly summary
    summary = generate_weekly_summary()
    if summary:
        print(f"Weekly summary generated: {summary['total_mentions']} mentions")
        print(f"Categories: {summary['category_breakdown']}")
        print(f"Key themes: {summary['key_themes'][:5]}")
    else:
        print("No mentions found for weekly summary")
