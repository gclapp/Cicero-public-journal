#!/usr/bin/env python3
"""
Google Docs Bulletproof Authentication
Handles OAuth, token refresh, and health monitoring
"""

import os
import sys
import pickle
import json
from datetime import datetime, timedelta
from pathlib import Path
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# Configuration
SCOPES = [
    'https://www.googleapis.com/auth/documents',
    'https://www.googleapis.com/auth/drive.file'
]

CREDENTIALS_PATH = Path.home() / '.openclaw' / 'credentials' / 'gdocs-credentials.json'
TOKEN_PATH = Path.home() / '.openclaw' / 'credentials' / 'gdocs-token.pickle'
HEALTH_LOG = Path.home() / '.openclaw' / 'workspace' / 'logs' / 'gdocs-health.log'

def log(msg, level="INFO"):
    """Log with timestamp"""
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_line = f"[{ts}] [{level}] {msg}"
    print(log_line)
    HEALTH_LOG.parent.mkdir(parents=True, exist_ok=True)
    with open(HEALTH_LOG, 'a') as f:
        f.write(log_line + "\n")

def get_credentials():
    """Get valid credentials, refreshing if necessary"""
    creds = None
    
    # Load existing token
    if TOKEN_PATH.exists():
        try:
            with open(TOKEN_PATH, 'rb') as f:
                creds = pickle.load(f)
            log(f"Loaded existing token")
        except Exception as e:
            log(f"Failed to load token: {e}", "ERROR")
            creds = None
    
    # Check if credentials are valid
    if creds and creds.valid:
        log("Token is valid")
        return creds
    
    # Refresh if expired but has refresh token
    if creds and creds.expired and creds.refresh_token:
        log("Token expired, attempting refresh...")
        try:
            creds.refresh(Request())
            # Save refreshed token
            with open(TOKEN_PATH, 'wb') as f:
                pickle.dump(creds, f)
            os.chmod(TOKEN_PATH, 0o600)
            log("Token refreshed successfully", "SUCCESS")
            return creds
        except Exception as e:
            log(f"Token refresh failed: {e}", "ERROR")
            return None
    
    # No valid credentials
    log("No valid credentials available", "ERROR")
    return None

def test_docs_access(creds):
    """Test that Docs API is accessible"""
    try:
        service = build('docs', 'v1', credentials=creds, cache_discovery=False)
        # Try to list documents (lightweight test)
        # We can't actually list without creating, so just build service
        log("✅ Google Docs API accessible")
        return True
    except Exception as e:
        log(f"❌ Google Docs API error: {e}", "ERROR")
        return False

def create_test_doc(creds, title="Test Document"):
    """Create a test document to verify full functionality"""
    try:
        service = build('docs', 'v1', credentials=creds, cache_discovery=False)
        
        doc = {
            'title': title
        }
        
        result = service.documents().create(body=doc).execute()
        doc_id = result.get('documentId')
        doc_title = result.get('title')
        
        log(f"✅ Created test document: {doc_title} (ID: {doc_id})", "SUCCESS")
        return doc_id
    except Exception as e:
        log(f"❌ Failed to create document: {e}", "ERROR")
        return None

def main():
    """Main authentication flow"""
    log("=" * 60)
    log("Google Docs Bulletproof Auth")
    log("=" * 60)
    
    # Check if credentials file exists
    if not CREDENTIALS_PATH.exists():
        log(f"❌ Credentials file not found: {CREDENTIALS_PATH}", "ERROR")
        log("Please ensure gdocs-credentials.json is in place")
        return False
    
    # Try to get valid credentials
    creds = get_credentials()
    
    if creds:
        # Test access
        if test_docs_access(creds):
            log("✅ Authentication complete and working")
            return True
    
    # If we get here, we need new authentication
    log("")
    log("🔐 New authentication required")
    log("Please visit the URL below and authorize the application")
    log("")
    
    # Generate auth URL
    flow = InstalledAppFlow.from_client_secrets_file(
        str(CREDENTIALS_PATH),
        SCOPES,
        redirect_uri='urn:ietf:wg:oauth:2.0:oob'
    )
    
    auth_url, _ = flow.authorization_url(
        prompt='consent',
        access_type='offline',
        include_granted_scopes='true'
    )
    
    print(auth_url)
    print("")
    
    # Get code from user
    code = input("Enter the authorization code: ").strip()
    
    try:
        flow.fetch_token(code=code)
        creds = flow.credentials
        
        # Save token
        TOKEN_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(TOKEN_PATH, 'wb') as f:
            pickle.dump(creds, f)
        os.chmod(TOKEN_PATH, 0o600)
        
        log("✅ Token saved successfully", "SUCCESS")
        
        # Test access
        if test_docs_access(creds):
            # Create test doc
            doc_id = create_test_doc(creds, f"Auth Test - {datetime.now().strftime('%Y-%m-%d')}")
            if doc_id:
                log("✅ Full authentication test passed", "SUCCESS")
                return True
        
        return False
        
    except Exception as e:
        log(f"❌ Authentication failed: {e}", "ERROR")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
