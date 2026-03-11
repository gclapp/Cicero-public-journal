#!/usr/bin/env python3
"""
twitter_browser_post.py - Post to Twitter/X using browser automation
Requires: Playwright, logged-in Twitter session
"""

import asyncio
import json
import sys
from pathlib import Path
from datetime import datetime

# Add workspace to path
sys.path.insert(0, '/home/ubuntu/.openclaw/workspace')

async def post_to_twitter(content, image_path=None):
    """Post content to Twitter using browser automation"""
    from playwright.async_api import async_playwright
    
    async with async_playwright() as p:
        # Launch browser
        browser = await p.chromium.launch(headless=False)  # Headless=False for first run
        context = await browser.new_context(
            viewport={'width': 1280, 'height': 800}
        )
        
        # Load saved session if exists
        session_file = Path.home() / ".openclaw" / "config" / "twitter_session.json"
        if session_file.exists():
            with open(session_file) as f:
                storage_state = json.load(f)
            await context.add_cookies(storage_state.get('cookies', []))
        
        page = await context.new_page()
        
        try:
            # Go to Twitter
            await page.goto("https://x.com/home")
            await page.wait_for_load_state('networkidle')
            
            # Check if logged in
            if "login" in page.url or "i/flow/login" in page.url:
                print("❌ Not logged in. Please log in manually.")
                await page.pause()  # Let user log in
                
                # Save session after login
                cookies = await context.cookies()
                session_file.parent.mkdir(parents=True, exist_ok=True)
                with open(session_file, 'w') as f:
                    json.dump({'cookies': cookies}, f)
                print("✅ Session saved")
            
            # Click "What is happening?!" text area
            tweet_box = await page.wait_for_selector('[data-testid="tweetTextarea_0"]', timeout=10000)
            await tweet_box.click()
            await tweet_box.fill(content)
            
            # Add image if provided
            if image_path:
                # Find file input
                file_input = await page.wait_for_selector('input[type="file"]', timeout=5000)
                await file_input.set_input_files(image_path)
                
                # Wait for upload
                await page.wait_for_timeout(3000)
            
            # Click Post button
            post_btn = await page.wait_for_selector('[data-testid="tweetButton"]', timeout=10000)
            
            # Check if button is enabled
            is_disabled = await post_btn.is_disabled()
            if is_disabled:
                print("❌ Post button is disabled (content may be empty or over limit)")
                return False
            
            await post_btn.click()
            
            # Wait for post to complete
            await page.wait_for_timeout(3000)
            
            print("✅ Twitter post published successfully")
            
            # Log the post
            log_post('twitter', content[:100], datetime.now().isoformat())
            
        except Exception as e:
            print(f"❌ Error posting to Twitter: {e}")
            return False
        finally:
            await browser.close()
        
        return True

def log_post(platform, content_preview, timestamp):
    """Log post to analytics"""
    log_file = Path.home() / ".openclaw" / "workspace" / "data" / "social_posts.json"
    log_file.parent.mkdir(parents=True, exist_ok=True)
    
    posts = []
    if log_file.exists():
        with open(log_file) as f:
            posts = json.load(f)
    
    posts.append({
        'platform': platform,
        'content_preview': content_preview,
        'timestamp': timestamp,
        'status': 'posted'
    })
    
    with open(log_file, 'w') as f:
        json.dump(posts, f, indent=2)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 twitter_browser_post.py 'Your tweet content here'")
        sys.exit(1)
    
    content = sys.argv[1]
    image = sys.argv[2] if len(sys.argv) > 2 else None
    
    asyncio.run(post_to_twitter(content, image))
