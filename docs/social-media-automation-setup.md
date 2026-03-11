# Social Media Browser Automation Setup

## Overview
Browser-based posting to LinkedIn and Twitter/X without API costs.

## How It Works
1. **Content Creation** — Draft posts using installed skills
2. **Approval Workflow** — Posts queue for your approval
3. **Browser Automation** — I log in as you and post
4. **Analytics Tracking** — All posts logged to dashboard

## Setup Steps

### Step 1: Install Playwright
```bash
pip install playwright
playwright install chromium
```

### Step 2: Initial Login (One-time per platform)

**LinkedIn:**
```bash
python3 scripts/linkedin_browser_post.py "Test post"
```
- Browser will open
- Log in to LinkedIn manually
- Session will be saved automatically
- Close browser when done

**Twitter/X:**
```bash
python3 scripts/twitter_browser_post.py "Test tweet"
```
- Browser will open
- Log in to Twitter manually
- Session will be saved automatically
- Close browser when done

### Step 3: Test the Workflow

**Create a pending post:**
```bash
python3 scripts/social_media_poster.py create --platform linkedin --content "Hello from automation!"
```

**Approve and publish:**
```bash
python3 scripts/social_media_poster.py approve --id post_20260311_123456
python3 scripts/social_media_poster.py publish --id post_20260311_123456
```

## Usage Workflow

### For You (Geoff):
1. Tell me: "Draft a LinkedIn post about [topic]"
2. I create content using the linkedin-writer skill
3. I send you the draft for approval
4. You reply: "Approve" or "Edit: [changes]"
5. I post via browser automation
6. I track results in analytics dashboard

### For Me (Cicero):
1. Draft content using appropriate skill
2. Queue for approval: `social_media_poster.py create`
3. Notify you with approval message
4. Upon approval, publish via browser
5. Log to analytics

## Security Notes

⚠️ **Session Storage:**
- Login cookies stored in `~/.openclaw/config/`
- Files: `linkedin_session.json`, `twitter_session.json`
- Permissions: 600 (owner read/write only)
- Never committed to GitHub

⚠️ **Approval Required:**
- No posts go live without explicit approval
- You can edit before publishing
- Full audit trail in `pending_posts.json`

⚠️ **Rate Limiting:**
- LinkedIn: Max 1 post per hour recommended
- Twitter: Max 10 tweets per hour recommended
- Excessive posting risks account restrictions

## Files Created

| File | Purpose |
|------|---------|
| `scripts/linkedin_browser_post.py` | LinkedIn browser automation |
| `scripts/twitter_browser_post.py` | Twitter browser automation |
| `scripts/social_media_poster.py` | Unified posting with approval |
| `data/pending_posts.json` | Queue of posts awaiting approval |
| `data/social_posts.json` | Log of all published posts |
| `config/linkedin_session.json` | Saved LinkedIn login session |
| `config/twitter_session.json` | Saved Twitter login session |

## Troubleshooting

**"Not logged in" error:**
- Session expired
- Run posting script manually to re-login
- Session will be saved again

**Post button disabled:**
- Content may be over character limit
- Check content length
- Try shorter content

**Browser doesn't open:**
- Check Playwright installation
- Try: `playwright install chromium`
- Check display/headless settings

## Next Steps

1. Run initial login for both platforms
2. Test with a draft post
3. Approve and publish
4. Check analytics dashboard
5. Schedule regular posting
