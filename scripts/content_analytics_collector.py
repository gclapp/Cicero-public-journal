#!/usr/bin/env python3
"""
content_analytics_collector.py - Collects engagement data from social platforms
Updates the analytics dashboard data file
"""

import json
from pathlib import Path
from datetime import datetime, timedelta

DATA_FILE = Path.home() / ".openclaw" / "workspace" / "dashboard" / "content-analytics-data.json"
DASHBOARD_DIR = Path.home() / ".openclaw" / "workspace" / "dashboard"

def load_data():
    """Load existing analytics data"""
    if DATA_FILE.exists():
        with open(DATA_FILE) as f:
            return json.load(f)
    return {
        "posts": [],
        "followers": {
            "linkedin": 0,
            "twitter": 0,
            "substack": 0
        },
        "last_updated": None
    }

def save_data(data):
    """Save analytics data"""
    DASHBOARD_DIR.mkdir(parents=True, exist_ok=True)
    data["last_updated"] = datetime.now().isoformat()
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=2)

def add_post(platform, title, content_type, impressions=0, engagements=0):
    """Add a new post to analytics"""
    data = load_data()
    
    post = {
        "id": f"{platform}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        "date": datetime.now().strftime('%Y-%m-%d'),
        "platform": platform,
        "title": title[:100] + "..." if len(title) > 100 else title,
        "content_type": content_type,  # article, thread, tweet, poll, etc.
        "impressions": impressions,
        "engagements": engagements,
        "status": "published",
        "published_at": datetime.now().isoformat()
    }
    
    data["posts"].append(post)
    save_data(data)
    return post["id"]

def update_post_metrics(post_id, impressions=None, engagements=None):
    """Update metrics for an existing post"""
    data = load_data()
    
    for post in data["posts"]:
        if post["id"] == post_id:
            if impressions is not None:
                post["impressions"] = impressions
            if engagements is not None:
                post["engagements"] = engagements
            post["last_updated"] = datetime.now().isoformat()
            save_data(data)
            return True
    
    return False

def update_followers(platform, count):
    """Update follower count for a platform"""
    data = load_data()
    data["followers"][platform] = count
    save_data(data)

def get_weekly_summary():
    """Get summary of last 7 days"""
    data = load_data()
    week_ago = datetime.now() - timedelta(days=7)
    
    recent_posts = [
        p for p in data["posts"]
        if datetime.fromisoformat(p["published_at"]) > week_ago
    ]
    
    summary = {
        "total_posts": len(recent_posts),
        "total_impressions": sum(p["impressions"] for p in recent_posts),
        "total_engagements": sum(p["engagements"] for p in recent_posts),
        "by_platform": {}
    }
    
    for platform in ["linkedin", "twitter", "substack"]:
        platform_posts = [p for p in recent_posts if p["platform"] == platform]
        summary["by_platform"][platform] = {
            "posts": len(platform_posts),
            "impressions": sum(p["impressions"] for p in platform_posts),
            "engagements": sum(p["engagements"] for p in platform_posts)
        }
    
    return summary

def generate_report():
    """Generate a text report for Geoff"""
    data = load_data()
    summary = get_weekly_summary()
    
    report = f"""📊 Content Analytics Report
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}

📈 Last 7 Days Summary:
• Total Posts: {summary['total_posts']}
• Total Impressions: {summary['total_impressions']:,}
• Total Engagements: {summary['total_engagements']:,}
• Avg Engagement Rate: {(summary['total_engagements'] / max(summary['total_impressions'], 1) * 100):.2f}%

By Platform:
"""
    
    for platform, stats in summary["by_platform"].items():
        if stats["posts"] > 0:
            rate = (stats["engagements"] / max(stats["impressions"], 1) * 100)
            report += f"\n{platform.upper()}:\n"
            report += f"  Posts: {stats['posts']}\n"
            report += f"  Impressions: {stats['impressions']:,}\n"
            report += f"  Engagements: {stats['engagements']:,}\n"
            report += f"  Engagement Rate: {rate:.2f}%\n"
    
    report += f"\n👥 Current Followers:\n"
    for platform, count in data["followers"].items():
        report += f"  {platform.capitalize()}: {count:,}\n"
    
    return report

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage:")
        print("  content_analytics_collector.py add <platform> <title> <content_type>")
        print("  content_analytics_collector.py update <post_id> <impressions> <engagements>")
        print("  content_analytics_collector.py followers <platform> <count>")
        print("  content_analytics_collector.py report")
        sys.exit(1)
    
    cmd = sys.argv[1]
    
    if cmd == "add" and len(sys.argv) >= 5:
        post_id = add_post(sys.argv[2], sys.argv[3], sys.argv[4])
        print(f"✅ Added post: {post_id}")
    
    elif cmd == "update" and len(sys.argv) >= 5:
        success = update_post_metrics(sys.argv[2], int(sys.argv[3]), int(sys.argv[4]))
        print("✅ Updated" if success else "❌ Post not found")
    
    elif cmd == "followers" and len(sys.argv) >= 4:
        update_followers(sys.argv[2], int(sys.argv[3]))
        print(f"✅ Updated {sys.argv[2]} followers: {sys.argv[3]}")
    
    elif cmd == "report":
        print(generate_report())
    
    else:
        print("Invalid command")
