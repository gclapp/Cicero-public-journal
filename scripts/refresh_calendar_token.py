#!/usr/bin/env python3
"""
Refresh Google Calendar Token - Standalone token refresh script
Uses stored refresh token to get new access token

Usage: python3 refresh_calendar_token.py [--check] [--force]
"""

import os
import sys
import pickle
import argparse
from datetime import datetime
from pathlib import Path

# Configuration
CREDENTIALS_DIR = Path.home() / ".openclaw" / "credentials"
TOKEN_FILE = CREDENTIALS_DIR / "calendar-token.pickle"
CREDENTIALS_FILE = CREDENTIALS_DIR / "calendar-credentials.json"


def log(message):
    """Log with timestamp"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}")


def load_credentials():
    """Load credentials from pickle file"""
    try:
        with open(TOKEN_FILE, 'rb') as f:
            creds = pickle.load(f)
        return creds
    except Exception as e:
        log(f"❌ Failed to load credentials: {e}")
        return None


def save_credentials(creds):
    """Save credentials to pickle file"""
    try:
        with open(TOKEN_FILE, 'wb') as f:
            pickle.dump(creds, f)
        os.chmod(TOKEN_FILE, 0o600)
        return True
    except Exception as e:
        log(f"❌ Failed to save credentials: {e}")
        return False


def check_token_valid(creds):
    """Check if token is valid"""
    if not creds:
        return False
    
    if hasattr(creds, 'valid') and creds.valid:
        return True
    
    if hasattr(creds, 'expired') and not creds.expired:
        return True
    
    return False


def refresh_token(force=False):
    """Refresh Google Calendar token"""
    log("=" * 60)
    log("GOOGLE CALENDAR TOKEN REFRESH")
    log("=" * 60)
    
    # Check if token file exists
    if not TOKEN_FILE.exists():
        log(f"❌ Token file not found: {TOKEN_FILE}")
        log("")
        log("You need to authenticate first. Run:")
        log("  python3 ~/.openclaw/workspace/scripts/calendar_auth.py")
        return False
    
    # Load current credentials
    creds = load_credentials()
    if not creds:
        return False
    
    # Check current token status
    log(f"Token file: {TOKEN_FILE}")
    
    if hasattr(creds, 'expiry'):
        log(f"Token expiry: {creds.expiry}")
        if creds.expiry:
            time_to_expiry = creds.expiry - datetime.now()
            log(f"Time to expiry: {time_to_expiry}")
    
    if hasattr(creds, 'valid'):
        log(f"Token valid: {creds.valid}")
    
    if hasattr(creds, 'expired'):
        log(f"Token expired: {creds.expired}")
    
    if hasattr(creds, 'refresh_token'):
        has_refresh = bool(creds.refresh_token)
        log(f"Has refresh token: {has_refresh}")
    else:
        has_refresh = False
        log("Has refresh token: False (attribute missing)")
    
    # Check if refresh is needed
    if not force:
        if check_token_valid(creds):
            log("")
            log("✅ Token is still valid, no refresh needed")
            log("Use --force to refresh anyway")
            return True
        else:
            log("")
            log("⚠️ Token is invalid or expired, attempting refresh...")
    else:
        log("")
        log("🔄 Force refresh requested...")
    
    # Check if we have a refresh token
    if not has_refresh:
        log("❌ No refresh token available!")
        log("")
        log("Full re-authentication required. Run:")
        log("  python3 ~/.openclaw/workspace/scripts/calendar_auth.py")
        return False
    
    # Attempt to refresh
    log("Making refresh request to Google OAuth...")
    
    try:
        from google.auth.transport.requests import Request
        
        creds.refresh(Request())
        
        if creds.valid:
            log("✅ Token refreshed successfully!")
            
            if hasattr(creds, 'expiry'):
                log(f"✅ New expiry: {creds.expiry}")
            
            # Save refreshed credentials
            if save_credentials(creds):
                log("✅ Credentials saved")
                return True
            else:
                log("❌ Failed to save credentials")
                return False
        else:
            log("❌ Refresh returned invalid credentials")
            return False
            
    except Exception as e:
        log(f"❌ Refresh failed: {e}")
        log("")
        log("Full re-authentication may be required. Run:")
        log("  python3 ~/.openclaw/workspace/scripts/calendar_auth.py")
        return False


def main():
    parser = argparse.ArgumentParser(description='Refresh Google Calendar Token')
    parser.add_argument('--check', action='store_true', help='Only check current token, do not refresh')
    parser.add_argument('--force', action='store_true', help='Force refresh even if current token is valid')
    args = parser.parse_args()
    
    if args.check:
        # Just check current token
        if not TOKEN_FILE.exists():
            log("❌ Token file not found")
            sys.exit(1)
        
        creds = load_credentials()
        if not creds:
            log("❌ Failed to load credentials")
            sys.exit(1)
        
        if check_token_valid(creds):
            log("✅ Token is valid")
            if hasattr(creds, 'expiry') and creds.expiry:
                time_to_expiry = creds.expiry - datetime.now()
                log(f"Expires in: {time_to_expiry}")
            sys.exit(0)
        else:
            log("❌ Token is invalid or expired")
            if hasattr(creds, 'expired') and creds.expired:
                log("Token has expired")
            sys.exit(1)
    
    # Refresh token
    success = refresh_token(force=args.force)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
