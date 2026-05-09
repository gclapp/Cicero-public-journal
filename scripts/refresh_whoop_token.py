#!/usr/bin/env python3
"""
Refresh Whoop Token - Standalone token refresh script
Uses stored refresh token to get new access token

Usage: python3 refresh_whoop_token.py [--check] [--force]
"""

import os
import sys
import json
import requests
import argparse
from datetime import datetime
from pathlib import Path

# Configuration
CREDENTIALS_DIR = Path.home() / ".openclaw" / "credentials"
TOKEN_FILE = CREDENTIALS_DIR / "whoop-tokens.json"
CONFIG_FILE = CREDENTIALS_DIR / "whoop-config.json"
ACCESS_TOKEN_FILE = Path.home() / ".whoop_token"
REFRESH_TOKEN_FILE = Path.home() / ".whoop_refresh_token"


def log(message):
    """Log with timestamp"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}")


def validate_token(access_token):
    """Validate token by making API call"""
    try:
        headers = {"Authorization": f"Bearer {access_token}"}
        response = requests.get(
            "https://api.prod.whoop.com/developer/v2/user/profile/basic",
            headers=headers,
            timeout=10
        )
        return response.status_code == 200
    except Exception as e:
        log(f"Validation error: {e}")
        return False


def refresh_token(force=False):
    """Refresh Whoop token"""
    log("=" * 60)
    log("WHOOP TOKEN REFRESH")
    log("=" * 60)
    
    # Check if files exist
    if not TOKEN_FILE.exists():
        log(f"❌ Token file not found: {TOKEN_FILE}")
        return False
    
    if not CONFIG_FILE.exists():
        log(f"❌ Config file not found: {CONFIG_FILE}")
        return False
    
    # Load current tokens
    try:
        with open(TOKEN_FILE, 'r') as f:
            tokens = json.load(f)
        
        access_token = tokens.get('access_token', '')
        refresh_token_value = tokens.get('refresh_token', '')
        
        if not refresh_token_value and REFRESH_TOKEN_FILE.exists():
            refresh_token_value = REFRESH_TOKEN_FILE.read_text().strip()
        
        if not refresh_token_value:
            log("❌ No refresh token available")
            return False
        
        log(f"Current access token: {access_token[:20]}...")
        log(f"Refresh token: {refresh_token_value[:20]}...")
        
    except Exception as e:
        log(f"❌ Failed to load tokens: {e}")
        return False
    
    # Check if current token is still valid (unless force)
    if not force and access_token:
        log("Checking current token validity...")
        if validate_token(access_token):
            log("✅ Current token is still valid, no refresh needed")
            log("Use --force to refresh anyway")
            return True
        else:
            log("⚠️ Current token is invalid, refreshing...")
    
    # Load config
    try:
        with open(CONFIG_FILE, 'r') as f:
            config = json.load(f)
        
        client_id = config['client_id']
        client_secret = config['client_secret']
        redirect_uri = config['redirect_uri']
        
    except Exception as e:
        log(f"❌ Failed to load config: {e}")
        return False
    
    # Make refresh request
    log("Making refresh request to Whoop API...")
    
    data = {
        'grant_type': 'refresh_token',
        'refresh_token': refresh_token_value,
        'client_id': client_id,
        'client_secret': client_secret,
        'redirect_uri': redirect_uri
    }
    
    try:
        response = requests.post(
            'https://api.prod.whoop.com/oauth/oauth2/token',
            data=data,
            timeout=15
        )
        
        log(f"Response status: {response.status_code}")
        
        if response.status_code == 200:
            new_tokens = response.json()
            
            new_access = new_tokens.get('access_token', '')
            new_refresh = new_tokens.get('refresh_token', '')
            expires_in = new_tokens.get('expires_in', 0)
            
            log(f"New access token: {new_access[:20]}...")
            if new_refresh:
                log(f"New refresh token: {new_refresh[:20]}...")
            else:
                log("No new refresh token (using existing)")
            log(f"Expires in: {expires_in} seconds")
            
            # Validate new token
            log("Validating new token...")
            if not validate_token(new_access):
                log("❌ New token failed validation!")
                return False
            
            # Save tokens
            log("Saving tokens...")
            
            with open(TOKEN_FILE, 'w') as f:
                json.dump(new_tokens, f, indent=2)
            
            ACCESS_TOKEN_FILE.write_text(new_access)
            
            if new_refresh:
                REFRESH_TOKEN_FILE.write_text(new_refresh)
            else:
                REFRESH_TOKEN_FILE.write_text(refresh_token_value)
            
            # Set permissions
            os.chmod(TOKEN_FILE, 0o600)
            os.chmod(ACCESS_TOKEN_FILE, 0o600)
            os.chmod(REFRESH_TOKEN_FILE, 0o600)
            
            log("✅ Token refreshed successfully!")
            log(f"✅ New token valid for {expires_in/60:.0f} minutes")
            return True
            
        elif response.status_code == 401:
            log("❌ Refresh failed: Invalid credentials (401)")
            log("The refresh token may have expired. Full re-authentication required.")
            log("")
            log("To re-authenticate, run:")
            log("  python3 ~/.openclaw/workspace/skills/whoop-openclaw-skill/scripts/whoop_oauth.py \\")
            log("    --config ~/.openclaw/credentials/whoop-config.json")
            return False
            
        else:
            log(f"❌ Refresh failed: HTTP {response.status_code}")
            try:
                error_data = response.json()
                log(f"Error: {error_data}")
            except:
                log(f"Response: {response.text}")
            return False
            
    except requests.exceptions.Timeout:
        log("❌ Request timeout - Whoop API may be down")
        return False
    except Exception as e:
        log(f"❌ Refresh error: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description='Refresh Whoop Token')
    parser.add_argument('--check', action='store_true', help='Only check current token, do not refresh')
    parser.add_argument('--force', action='store_true', help='Force refresh even if current token is valid')
    args = parser.parse_args()
    
    if args.check:
        # Just check current token
        if not TOKEN_FILE.exists():
            log("❌ Token file not found")
            sys.exit(1)
        
        with open(TOKEN_FILE, 'r') as f:
            tokens = json.load(f)
        
        access_token = tokens.get('access_token', '')
        
        if not access_token:
            log("❌ No access token found")
            sys.exit(1)
        
        if validate_token(access_token):
            log("✅ Token is valid")
            sys.exit(0)
        else:
            log("❌ Token is invalid")
            sys.exit(1)
    
    # Refresh token
    success = refresh_token(force=args.force)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
