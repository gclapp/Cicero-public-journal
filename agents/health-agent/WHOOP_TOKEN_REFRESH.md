# Whoop Token Refresh - Web-Based Method

## The Problem
Whoop OAuth tokens expire after 1 hour. Geoff cannot access the command line to run the OAuth flow.

## The Solution: Web-Based Token Refresh

Since Whoop uses standard OAuth 2.0, we can use a simple web-based approach that Geoff can do entirely in his browser.

---

## Method 1: Postman Web (Easiest - Recommended)

Postman has a web interface that can handle OAuth flows without command line.

### Step 1: Open Postman Web
1. Go to https://web.postman.com/ in your browser
2. Sign in or create a free account

### Step 2: Create a New Request
1. Click "+" to create a new request
2. Change GET to POST
3. Enter URL: `https://api.prod.whoop.com/oauth/oauth2/token`

### Step 3: Set Up OAuth 2.0
1. Go to the "Authorization" tab
2. Select type: "OAuth 2.0"
3. Click "Get New Access Token"
4. Fill in these details:
   - **Token Name:** Whoop Token
   - **Grant Type:** Authorization Code
   - **Callback URL:** `http://localhost:8080/callback`
   - **Auth URL:** `https://api.prod.whoop.com/oauth/oauth2/auth`
   - **Access Token URL:** `https://api.prod.whoop.com/oauth/oauth2/token`
   - **Client ID:** `[From your Whoop Developer Dashboard]`
   - **Client Secret:** `[From your Whoop Developer Dashboard]`
   - **Scope:** `offline read:recovery read:sleep read:workout read:profile`
   - **State:** `[leave blank or enter any random string]`

### Step 4: Authenticate
1. Click "Request Token"
2. A popup will open asking you to log in to Whoop
3. Log in with your Whoop credentials
4. Authorize the app
5. Postman will capture the token

### Step 5: Send to Vitus
1. Copy the `access_token` value
2. Email it to: [REDACTED]
3. Subject: "Whoop Token Refresh"

---

## Method 2: Simple HTML Page (No External Tools)

If you prefer not to use Postman, I can create a simple web page you can open locally.

### What You Need:
1. Your Whoop Client ID and Client Secret from the Developer Dashboard
2. A text editor (or just email me the credentials securely)

### Steps:
1. Go to https://developer-dashboard.whoop.com/
2. Log in with your Whoop account
3. Find your existing app (or create one)
4. Note down:
   - Client ID
   - Client Secret
   - Redirect URL (should be `http://localhost:8080/callback`)

### Then either:
**Option A:** Email me the credentials and I'll generate the token for you
**Option B:** I create a simple HTML file you open locally

---

## Method 3: Manual cURL (For Advanced Users)

If you have access to any terminal (even on your phone via Termius or similar):

```bash
# Step 1: Get authorization URL (open this in browser)
echo "https://api.prod.whoop.com/oauth/oauth2/auth?response_type=code&client_id=YOUR_CLIENT_ID&redirect_uri=http://localhost:8080/callback&scope=offline%20read:recovery%20read:sleep%20read:workout&state=random123"

# Step 2: After authorizing, you'll get a code in the URL
# Copy that code and run:

curl -X POST https://api.prod.whoop.com/oauth/oauth2/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "grant_type=authorization_code" \
  -d "code=YOUR_AUTH_CODE" \
  -d "client_id=YOUR_CLIENT_ID" \
  -d "client_secret=YOUR_CLIENT_SECRET" \
  -d "redirect_uri=http://localhost:8080/callback"
```

---

## Method 4: Refresh Token (If You Have One)

If you previously got a refresh token, this is the easiest method:

### Using Postman Web:
1. Create a POST request to: `https://api.prod.whoop.com/oauth/oauth2/token`
2. Go to Body tab, select "x-www-form-urlencoded"
3. Add these key-value pairs:
   - `grant_type`: `refresh_token`
   - `refresh_token`: `[your old refresh token]`
   - `client_id`: `[your client id]`
   - `client_secret`: `[your client secret]`
   - `scope`: `offline`
4. Click Send
5. Copy the new `access_token` from the response

---

## What I Need From You

To help you with any of these methods, I need:

1. **Your Whoop Developer Dashboard credentials:**
   - Client ID
   - Client Secret
   - Your registered Redirect URL

2. **Your preference:**
   - Method 1 (Postman Web) - Easiest
   - Method 2 (Simple HTML page) - No external accounts
   - Method 3 (Manual) - If you're comfortable with terminals
   - Method 4 (Refresh) - If you have an old refresh token

---

## Security Note

Your Client ID and Client Secret are sensitive. When sending them:
- Email to [REDACTED] only
- Use a secure method if possible
- I will not store them permanently
- They are only used to generate your access token

---

## After Token Refresh

Once you send me the new access token:
1. I'll save it to the system
2. Vitus will resume normal health monitoring
3. You should receive your next briefing within 24 hours

---

*Questions? Just reply to this email or send a new one to [REDACTED]*

🫀 Vitus | Your Dedicated Health Coach