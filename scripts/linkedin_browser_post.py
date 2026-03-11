#!/usr/bin/env python3
"""
linkedin_browser_post.py - Post to LinkedIn using browser automation
Requires: Playwright, logged-in LinkedIn session
"""

import asyncio
import json
import sys
from pathlib import Path
from datetime import datetime

# Add workspace to path
sys.path.insert(0, '/home/ubuntu/.openclaw/workspace')

async def post_to_linkedin(content, image_path=None):
    """Post content to LinkedIn using browser automation"""
    from playwright.async_api import async_playwright
    
    async with async_playwright() as p:
        # Launch browser
        browser = await p.chromium.launch(headless=False)  # Headless=False for first run to login
        context = await browser.new_context(
            viewport={'width': 1280, 'height': 800}
        )
        
        # Load saved session if exists
        session_file = Path.home() / ".openclaw" / "config" / "linkedin_session.json"
        if session_file.exists():
            with open(session_file) as f:
                storage_state = json.load(f)
            await context.add_cookies(storage_state.get('cookies', []))
        
        page = await context.new_page()
        
        try:
            # Go to LinkedIn
            await page.goto("https://www.linkedin.com/feed/")
            await page.wait_for_load_state('networkidle')
            
            # Check if logged in
            if "login" in page.url:
                print("❌ Not logged in. Please log in manually.")
                await page.pause()  # Let user log in
                
                # Save session after login
                cookies = await context.cookies()
                session_file.parent.mkdir(parents=True, exist_ok=True)
                with open(session_file, 'w') as f:
                    json.dump({'cookies': cookies}, f)
                print("✅ Session saved")
            
            # Click "Start a post" button
            start_post = await page.wait_for_selector('[data-test-id="share-creation-trigger"]', timeout=10000)
            await start_post.click()
            
            # Wait for post dialog
            await page.wait_for_selector('[data-test-id="share-creation-modal"]', timeout=10000)
            
            # Find text editor and type content
            editor = await page.wait_for_selector('[data-test-id="share-creation-modal"] div[contenteditable="true"]', timeout=10000)
            await editor.fill(content)
            
            # Add image if provided
            if image_path:
                # Click add media button
                media_btn = await page.wait_for_selector('[aria-label="Add media"]')
                await media_btn.click()
                
                # Upload image
                file_input = await page.wait_for_selector('input[type="file"]')
                await file_input.set_input_files(image_path)
                
                # Wait for upload
                await page.wait_for_timeout(3000)
            
            # Click Post button
            post_btn = await page.wait_for_selector('[data-test-id="share-creation-modal"] button[type="submit"]')
            await post_btn.click()
            
            # Wait for post to complete
            await page.wait_for_timeout(3000)
            
            print("✅ LinkedIn post published successfully")
            
            # Log the post
            log_post('linkedin', content[:100], datetime.now().isoformat())
            
        except Exception as e:
            print(f"❌ Error posting to LinkedIn: {e}")
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
        print("Usage: python3 linkedin_browser_post.py 'Your post content here'")
        sys.exit(1)
    
    content = sys.argv[1]
    image = sys.argv[2] if len(sys.argv) > 2 else None
    
    asyncio.run(post_to_linkedin(content, image))
