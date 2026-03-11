# Social Media Skills Required

## Priority 1: Core Posting Skills

### LinkedIn
**Skill:** `linkedin-writer` or `linkedin-api`
**Purpose:** Post content, schedule posts, monitor notifications
**Features needed:**
- Post text + images
- Schedule posts for optimal times
- Monitor comments/replies
- Send connection requests (optional)

### Twitter/X
**Skill:** `twitter-post` or `x-twitter`
**Purpose:** Post tweets, threads, monitor mentions
**Features needed:**
- Post single tweets
- Post threaded tweets
- Monitor replies/mentions
- Retweet/quote tweet

## Priority 2: Engagement & Monitoring

### LinkedIn Engagement
**Skill:** `linkedin-content` or `linkedin-cli`
**Purpose:** Comment on others' posts, respond to DMs
**Features needed:**
- Comment on posts by URL
- Reply to comments on your posts
- Basic DM responses

### Twitter Engagement
**Skill:** `twitter-watch-reply` or `twitter-operations`
**Purpose:** Monitor timeline, auto-respond to mentions
**Features needed:**
- Watch for mentions
- Auto-reply templates
- Track engagement metrics

## Priority 3: Analytics & Optimization

**Skill:** `analytics` (general) or platform-specific
**Purpose:** Track post performance, optimize timing
**Features needed:**
- View impressions/engagement
- Track follower growth
- Identify best-performing content

## Recommended Installation Order

1. **linkedin-writer** — Core posting capability
2. **twitter-post** — Core tweeting capability
3. **twitter-watch-reply** — Engagement monitoring
4. **analytics** — Performance tracking

## Alternative: Browser Automation

If official API skills don't work well, we can use:
- **browser** tool with saved sessions
- **playwright** or **scrapling** for automation
- More fragile but often more capable

## Credentials Required

**LinkedIn:**
- Username/password or session cookies
- May need 2FA handling

**Twitter/X:**
- API keys (developer account) OR
- Username/password for browser automation

## Security Note

⚠️ **Important:** Social media credentials are high-risk. We'll store them in:
- `~/.openclaw/config/linkedin.json`
- `~/.openclaw/config/twitter.json`
- With proper file permissions (600)

Never commit credentials to GitHub.
