#!/usr/bin/env python3
"""
social_media_poster.py - Unified social media posting with approval workflow
Posts to LinkedIn and Twitter using browser automation
"""

import asyncio
import json
import sys
from pathlib import Path
from datetime import datetime

# Configuration
CONFIG_DIR = Path.home() / ".openclaw" / "config"
PENDING_FILE = Path.home() / ".openclaw" / "workspace" / "data" / "pending_posts.json"

# Import browser posting functions
sys.path.insert(0, '/home/ubuntu/.openclaw/workspace/scripts')

def load_pending_posts():
    """Load posts awaiting approval"""
    if PENDING_FILE.exists():
        with open(PENDING_FILE) as f:
            return json.load(f)
    return []

def save_pending_posts(posts):
    """Save pending posts"""
    PENDING_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(PENDING_FILE, 'w') as f:
        json.dump(posts, f, indent=2)

def create_post(platform, content, scheduled_time=None):
    """Create a new post pending approval"""
    posts = load_pending_posts()
    
    post = {
        'id': f"post_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        'platform': platform,
        'content': content,
        'status': 'pending',
        'created_at': datetime.now().isoformat(),
        'scheduled_time': scheduled_time,
        'approved_at': None,
        'posted_at': None
    }
    
    posts.append(post)
    save_pending_posts(posts)
    
    return post['id']

def approve_post(post_id):
    """Approve a pending post for publishing"""
    posts = load_pending_posts()
    
    for post in posts:
        if post['id'] == post_id:
            post['status'] = 'approved'
            post['approved_at'] = datetime.now().isoformat()
            save_pending_posts(posts)
            return True
    
    return False

def list_pending_posts():
    """List all pending posts"""
    posts = load_pending_posts()
    pending = [p for p in posts if p['status'] == 'pending']
    return pending

def list_approved_posts():
    """List all approved but not yet posted"""
    posts = load_pending_posts()
    approved = [p for p in posts if p['status'] == 'approved' and not p['posted_at']]
    return approved

async def publish_post(post_id):
    """Publish an approved post"""
    posts = load_pending_posts()
    
    post = None
    for p in posts:
        if p['id'] == post_id:
            post = p
            break
    
    if not post:
        print(f"❌ Post {post_id} not found")
        return False
    
    if post['status'] != 'approved':
        print(f"❌ Post {post_id} is not approved")
        return False
    
    # Import and run the appropriate browser script
    if post['platform'] == 'linkedin':
        from linkedin_browser_post import post_to_linkedin
        success = await post_to_linkedin(post['content'])
    elif post['platform'] == 'twitter':
        from twitter_browser_post import post_to_twitter
        success = await post_to_twitter(post['content'])
    else:
        print(f"❌ Unknown platform: {post['platform']}")
        return False
    
    if success:
        post['status'] = 'posted'
        post['posted_at'] = datetime.now().isoformat()
        save_pending_posts(posts)
        print(f"✅ Post {post_id} published successfully")
    else:
        print(f"❌ Failed to publish post {post_id}")
    
    return success

def generate_approval_message(post):
    """Generate a message for Geoff to approve a post"""
    platform_emoji = {'linkedin': '💼', 'twitter': '🐦'}
    
    message = f"""{platform_emoji.get(post['platform'], '📱')} **Post Pending Approval**

**Platform:** {post['platform'].capitalize()}
**ID:** `{post['id']}`

**Content:**
```
{post['content']}
```

**Actions:**
• Reply "approve {post['id']}" to publish
• Reply "edit {post['id']}: [new content]" to modify
• Reply "reject {post['id']}" to cancel

_Time: {post['created_at']}_"""
    
    return message

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Social Media Poster')
    parser.add_argument('action', choices=['create', 'approve', 'publish', 'list', 'pending'])
    parser.add_argument('--platform', '-p', choices=['linkedin', 'twitter'])
    parser.add_argument('--content', '-c', help='Post content')
    parser.add_argument('--id', '-i', help='Post ID')
    
    args = parser.parse_args()
    
    if args.action == 'create' and args.platform and args.content:
        post_id = create_post(args.platform, args.content)
        print(f"✅ Created post: {post_id}")
        print(f"\n{generate_approval_message({'id': post_id, 'platform': args.platform, 'content': args.content, 'created_at': datetime.now().isoformat()})}")
    
    elif args.action == 'approve' and args.id:
        if approve_post(args.id):
            print(f"✅ Approved post: {args.id}")
            print("Run 'publish' to post it now, or it will be posted automatically")
        else:
            print(f"❌ Post not found: {args.id}")
    
    elif args.action == 'publish' and args.id:
        asyncio.run(publish_post(args.id))
    
    elif args.action == 'list' or args.action == 'pending':
        pending = list_pending_posts()
        if pending:
            print(f"📋 {len(pending)} pending posts:\n")
            for post in pending:
                print(f"• {post['id']} ({post['platform']}): {post['content'][:50]}...")
        else:
            print("No pending posts")
    
    else:
        parser.print_help()
