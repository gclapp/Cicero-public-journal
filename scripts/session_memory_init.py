#!/usr/bin/env python3
"""
Session Memory Initializer - Creates daily memory file at session start
This should be called at the beginning of every main session.
"""

import os
import sys
from pathlib import Path
from datetime import datetime

MEMORY_DIR = Path.home() / ".openclaw" / "workspace" / "memory"
LOG_FILE = Path.home() / ".openclaw" / "workspace" / "logs" / "memory-system.log"

def log(msg):
    """Log to file and console"""
    print(msg)
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG_FILE, 'a') as f:
        f.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {msg}\n")

def init_daily_memory():
    """Initialize or open today's memory file"""
    MEMORY_DIR.mkdir(parents=True, exist_ok=True)
    
    today = datetime.now()
    today_file = MEMORY_DIR / f"{today.strftime('%Y-%m-%d')}.md"
    
    if today_file.exists():
        # File exists - read it and return path
        content = today_file.read_text()
        log(f"📂 Opening existing memory file: {today_file} ({len(content)} chars)")
        return today_file, False  # False = not newly created
    else:
        # Create new daily memory file
        content = f"""---
date: {today.strftime('%Y-%m-%d')}
day: {today.strftime('%A')}
tags: [daily]
---

# {today.strftime('%A, %B %d, %Y')}

## Overview
- Date: {today.strftime('%Y-%m-%d')}
- Day: {today.strftime('%A')}
- Status: Active session

## Sessions

### Session {today.strftime('%H:%M')} UTC

**Started:** {today.strftime('%Y-%m-%d %H:%M:%S')} UTC

"""
        today_file.write_text(content)
        log(f"✅ Created new memory file: {today_file}")
        return today_file, True  # True = newly created

def append_session_entry(memory_file, session_start_time=None):
    """Append a new session entry to the memory file"""
    if session_start_time is None:
        session_start_time = datetime.now()
    
    content = memory_file.read_text()
    
    # Check if we already have an entry for this hour
    hour_marker = f"### Session {session_start_time.strftime('%H:')}"
    if hour_marker in content:
        log(f"⏭️  Session entry already exists for this hour")
        return False
    
    session_entry = f"""
### Session {session_start_time.strftime('%H:%M')} UTC

**Started:** {session_start_time.strftime('%Y-%m-%d %H:%M:%S')} UTC

**Topics Discussed:**
- 

**Decisions Made:**
- 

**Action Items:**
- 

---
"""
    
    with open(memory_file, 'a') as f:
        f.write(session_entry)
    
    log(f"📝 Added session entry: {session_start_time.strftime('%H:%M')} UTC")
    return True

if __name__ == "__main__":
    log("=" * 60)
    log("Session Memory Initializer - Starting")
    
    # Initialize daily memory file
    memory_file, is_new = init_daily_memory()
    
    # Add session entry (if not already exists for this hour)
    appended = append_session_entry(memory_file)
    
    log(f"✅ Memory system ready: {memory_file}")
    print(f"\n📓 Memory file: {memory_file}")
    print(f"   New file: {'Yes' if is_new else 'No'}")
    print(f"   New session entry: {'Yes' if appended else 'No (already exists)'}")
