# App-Specific Password Setup Guide

## LinkedIn App-Specific Password

LinkedIn doesn't have traditional "app-specific passwords" like Google, but they offer **two safer options**:

### Option A: LinkedIn Two-Factor Authentication + Session Cookies (Recommended)

1. **Enable 2FA on LinkedIn:**
   - Go to https://www.linkedin.com/mypreferences/d/two-step-verification
   - Click "Set up"
   - Choose "Authenticator App" or "SMS"
   - Complete setup

2. **After 2FA is enabled:**
   - When I run the browser script, you'll enter your password + 2FA code
   - Session cookies get saved
   - Future posts use saved session (no password needed)

### Option B: LinkedIn "Sign in with Apple/Google" Alternative

If your LinkedIn is connected to Google/Apple:
- Use that account's app-specific password instead
- But this is less direct

---

## Twitter/X App-Specific Password

Twitter/X also doesn't have app-specific passwords, but here's the safest approach:

### Step 1: Enable Two-Factor Authentication

1. Go to https://x.com/settings/security
2. Click "Two-factor authentication"
3. Choose method:
   - **Authenticator app** (recommended — Google Authenticator, Authy)
   - **Text message** (SMS)
   - **Security key** (YubiKey, etc.)

4. Complete setup

### Step 2: Generate a Backup Code (Temporary Access)

1. In the same 2FA settings
2. Look for "Backup codes" or "Recovery codes"
3. Generate and save these codes
4. Use one code when I run the initial login script

---

## The Actual Process

**What we'll do:**

1. **You enable 2FA** on both platforms (links above)
2. **I run the login script:**
   ```bash
   python3 scripts/linkedin_browser_post.py "Test"
   ```
3. **Browser opens** — you see the login page
4. **You enter:**
   - Your regular password
   - The 2FA code from your authenticator app
5. **Session saved** — cookies stored securely
6. **Done** — future posts use saved session

**Security benefits:**
- ✅ Your password is never stored
- ✅ 2FA protects even if session is compromised
- ✅ You can revoke sessions anytime from account settings
- ✅ No app-specific password needed (Twitter/LinkedIn don't offer them)

---

## Revoking Access (If Needed)

**LinkedIn:**
- https://www.linkedin.com/mypreferences/d/login-activity
- See all active sessions
- Click "End session" to revoke

**Twitter/X:**
- https://x.com/settings/sessions
- See all active sessions
- Click "Log out" to revoke

---

## Alternative: Dedicated Browser Profile

If you prefer maximum isolation:

1. Create a new Chrome/Firefox profile just for automation
2. Log in to LinkedIn/Twitter there
3. Export cookies from that profile
4. I use those cookies for posting

This keeps automation completely separate from your personal browsing.

---

## Summary

| Platform | App-Specific Password? | Best Alternative |
|----------|----------------------|------------------|
| LinkedIn | ❌ Not available | 2FA + Session cookies |
| Twitter/X | ❌ Not available | 2FA + Session cookies |

**Next step:** Enable 2FA on both platforms, then we'll do the initial login to save sessions.
