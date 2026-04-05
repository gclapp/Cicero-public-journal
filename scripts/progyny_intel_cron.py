#!/usr/bin/env python3
"""
Integrate Progyny Intelligence with Competitive Intelligence
Stores all Progyny mentions daily, generates weekly summary
"""

import sys
import json
from pathlib import Path

sys.path.insert(0, '/home/ubuntu/.openclaw/workspace/scripts')
from progyny_intelligence import store_mention, generate_weekly_summary, format_weekly_email

# Load current Progyny data
PROGYNY_FILE = Path.home() / ".openclaw" / "workspace" / "config" / "progyny-sentiment.json"

def process_daily_progyny_data():
    """Process today's Progyny mentions and store them"""
    if not PROGYNY_FILE.exists():
        print("No Progyny data file found")
        return 0
    
    with open(PROGYNY_FILE) as f:
        data = json.load(f)
    
    mentions = data.get('mentions', [])
    exec_news = data.get('executive_news', [])
    stored_count = 0
    
    # Store regular mentions
    for mention in mentions:
        result = store_mention(mention, source_type='news')
        if result:
            stored_count += 1
            print(f"✅ Stored: {mention.get('title', '')[:60]}...")
    
    # Store executive news
    for news in exec_news:
        # Convert exec news format to mention format
        mention = {
            'title': news.get('headline', ''),
            'url': news.get('url', ''),
            'source': 'Executive News',
            'published': '',
            'summary': news.get('description', '')
        }
        result = store_mention(mention, source_type='executive')
        if result:
            stored_count += 1
            print(f"✅ Stored exec news: {mention.get('title', '')[:60]}...")
    
    print(f"\n📊 Stored {stored_count} new Progyny mentions")
    return stored_count

def generate_and_send_weekly():
    """Generate weekly summary and send email"""
    summary = generate_weekly_summary()
    
    if not summary:
        print("No mentions to summarize")
        return
    
    html = format_weekly_email(summary)
    
    # Save HTML for email
    output_file = Path.home() / ".openclaw" / "workspace" / "config" / "progyny-weekly-summary.html"
    with open(output_file, 'w') as f:
        f.write(html)
    
    print(f"✅ Weekly summary generated: {summary['total_mentions']} mentions")
    print(f"📧 HTML saved to: {output_file}")
    print(f"\nTo send: python3 scripts/send_email.py --to '[REDACTED],geoffrey.clapp@progyny.com,steven.leist@progyny.com' --subject '🏛️ Progyny Weekly Intelligence' --body-file config/progyny-weekly-summary.html --html")
    
    return summary

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--daily', action='store_true', help='Process daily mentions')
    parser.add_argument('--weekly', action='store_true', help='Generate weekly summary')
    args = parser.parse_args()
    
    if args.daily:
        process_daily_progyny_data()
    elif args.weekly:
        generate_and_send_weekly()
    else:
        # Default: do both
        print("=== Daily Processing ===")
        process_daily_progyny_data()
        print("\n=== Weekly Summary ===")
        generate_and_send_weekly()
