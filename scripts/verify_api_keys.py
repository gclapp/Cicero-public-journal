#!/usr/bin/env python3
"""
verify_api_keys.py - Verify all API keys are working
Run this to check key status without rediscovering keys
"""

import os
import json
import requests
from pathlib import Path

def check_brave_api():
    """Check Brave API key"""
    key = os.getenv('BRAVE_API_KEY')
    if not key:
        return False, "BRAVE_API_KEY not set in environment"
    
    try:
        response = requests.get(
            "https://api.search.brave.com/res/v1/web/search?q=test",
            headers={"X-Subscription-Token": key},
            timeout=10
        )
        if response.status_code == 200:
            return True, f"Working (key: {key[:15]}...)"
        else:
            return False, f"HTTP {response.status_code}"
    except Exception as e:
        return False, str(e)

def check_openai_api():
    """Check OpenAI API key"""
    key = os.getenv('OPENAI_API_KEY')
    if not key:
        return False, "OPENAI_API_KEY not set"
    return True, f"Set (key: {key[:15]}...)"

def check_elevenlabs_api():
    """Check ElevenLabs API key"""
    key = os.getenv('ELEVENLABS_API_KEY')
    if not key:
        return False, "ELEVENLABS_API_KEY not set"
    return True, f"Set (key: {key[:15]}...)"

def main():
    # Source the env file first
    env_file = Path.home() / ".openclaw/workspace/config/api-keys.env"
    if env_file.exists():
        with open(env_file) as f:
            for line in f:
                if line.startswith('export ') and '=' in line:
                    line = line.replace('export ', '').strip()
                    key, value = line.split('=', 1)
                    value = value.strip().strip('"')
                    os.environ[key] = value
    
    print("=" * 60)
    print("API KEY VERIFICATION")
    print("=" * 60)
    
    checks = [
        ("Brave Search", check_brave_api),
        ("OpenAI", check_openai_api),
        ("ElevenLabs", check_elevenlabs_api),
    ]
    
    all_good = True
    for name, check_func in checks:
        status, msg = check_func()
        icon = "✅" if status else "🔴"
        print(f"{icon} {name}: {msg}")
        if not status:
            all_good = False
    
    print("=" * 60)
    if all_good:
        print("✅ All API keys working")
    else:
        print("🔴 Some keys need attention")
    print("=" * 60)
    
    return 0 if all_good else 1

if __name__ == "__main__":
    exit(main())
