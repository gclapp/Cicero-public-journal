#!/usr/bin/env python3
"""
Calendar Auth Helper - Save auth code to file for processing
"""

import os
from pathlib import Path

CODE_FILE = Path.home() / ".openclaw" / "credentials" / "calendar-auth-code.txt"

def save_code(code):
    """Save auth code to file"""
    CODE_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(CODE_FILE, 'w') as f:
        f.write(code.strip())
    print(f"✅ Auth code saved to {CODE_FILE}")
    print("Run: python3 scripts/calendar_reader.py")

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        save_code(sys.argv[1])
    else:
        print("Usage: python3 scripts/save_calendar_code.py 'YOUR_AUTH_CODE'")
