# Whoop Token Refresh Guide (Web-Based Methods)

Since you cannot access the command line, here are web-based methods to refresh your Whoop token.

## Method 1: Postman Web (Easiest)

Postman has a web interface that can handle OAuth flows without installing anything.

### Step 1: Open Postman Web
1. Go to https://web.postman.com/
2. Sign in or create a free account

### Step 2: Create a New Request
1. Click "+" to create a new request
2. Change GET to POST
3. Enter URL: `https://api.prod.whoop.com/oauth/oauth2/token`

### Step 3: Configure the OAuth Flow
1. Go to the "Authorization" tab
2. Select type: "OAuth 2.0"
3. Click "Get New Access Token"
4. Fill in:
   - **Token Name**: Whoop Token
   - **Grant Type**: Authorization Code
   - **Callback URL**: `https://oauth.pstmn.io/v1/callback`
   - **Auth URL**: `https://api.prod.whoop.com/oauth/oauth2/auth`
   - **Access Token URL**: `https://api.prod.whoop.com/oauth/oauth2/token`
   - **Client ID**: (from your whoop-config.json)
   - **Client Secret**: (from your whoop-config.json)
   - **Scope**: `read:recovery read:cycles read:workout read:sleep read:profile read:body_measurement`
   - **State**: (leave blank)
   - **Client Authentication**: Send as Basic Auth header

### Step 4: Authorize
1. Click "Request Token"
2. A popup will open asking you to log in to Whoop
3. Log in and authorize the app
4. The token will appear in Postman

### Step 5: Send Token to Cicero
1. Copy the access token (long string starting with letters/numbers)
2. Email it to: [REDACTED]
3. Subject: "Whoop Token"
4. I'll save it and Vitus will resume working

---

## Method 2: Simple HTML Page (No External Tools)

If you prefer not to use Postman, I can create a simple HTML page that handles the OAuth flow.

### Option A: I Create the Page
1. I generate an HTML file with the OAuth flow built-in
2. You open it in your browser
3. Click "Authorize with Whoop"
4. Log in and copy the token
5. Email it to me

### Option B: Manual Browser Method
1. Open this URL in your browser (replace YOUR_CLIENT_ID):
```
https://api.prod.whoop.com/oauth/oauth2/auth?
  response_type=code&
  client_id=YOUR_CLIENT_ID&
  redirect_uri=https://oauth.pstmn.io/v1/callback&
  scope=read:recovery%20read:cycles%20read:workout%20read:sleep%20read:profile%20read:body_measurement&
  state=random_state_123
```

2. Log in to Whoop and authorize
3. You'll be redirected to a page with an error (that's OK)
4. Copy the URL from your browser address bar
5. The URL contains `?code=XXXX` - copy that code
6. Email me the code

---

## Method 3: Refresh Token (If Available)

If you previously got a refresh token, we can use that instead.

### Check for Refresh Token
1. Look for a file called `whoop-refresh-token.txt` or similar
2. If it exists, email me the contents
3. I can use it to get a new access token without you doing anything

---

## What I Need From You

**Option 1 (Easiest):**
- Your Whoop Client ID and Client Secret (from whoop-config.json)
- I'll guide you through Postman step-by-step

**Option 2:**
- I create an HTML page for you
- You open it and click authorize

**Option 3:**
- You check if you have a refresh token saved anywhere

---

## After Token Refresh

Once I have the new token:
1. Vitus will resume daily health briefings
2. All health monitoring will work again
3. You'll get your morning coaching email tomorrow at 7 AM PT

---

## Questions?

Reply to this email or message me on Telegram if you need help with any step.
