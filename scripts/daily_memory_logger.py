#!/usr/bin/env python3
"""
Daily Memory Logger - Robust automatic memory logging
Creates memory/YYYY-MM-DD.md at end of each session
"""

import os
import sys
import json
from pathlib import Path
from datetime import datetime, timedelta

MEMORY_DIR = Path.home() / ".openclaw" / "workspace" / "memory"
LOG_FILE = Path.home() / ".openclaw" / "workspace" / "logs" / "memory-system.log"

def log(msg):
    """Log to file and console"""
    print(msg)
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG_FILE, 'a') as f:
        f.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {msg}\n")

def get_session_summary():
    """Get summary of current session from context"""
    # This would integrate with OpenClaw's session tracking
    # For now, create a template
    return {
        'date': datetime.now().strftime('%Y-%m-%d'),
        'time': datetime.now().strftime('%H:%M:%S'),
        'summary': 'Session summary - to be filled',
        'decisions': [],
        'preferences': [],
        'tasks_completed': [],
        'tasks_started': [],
        'issues': []
    }

def write_daily_memory():
    """Write daily memory file"""
    MEMORY_DIR.mkdir(parents=True, exist_ok=True)
    
    today = datetime.now()
    today_file = MEMORY_DIR / f"{today.strftime('%Y-%m-%d')}.md"
    
    # If file exists, append to it
    if today_file.exists():
        content = today_file.read_text()
        # Check if we already logged this hour
        if f"## Session {today.strftime('%H:')}" in content:
            log(f"Memory already logged for this hour: {today_file}")
            return True
    else:
        content = f"""# {today.strftime('%Y-%m-%d')} - Daily Memory Log

## Overview
- Date: {today.strftime('%Y-%m-%d %A')}
- Sessions: Multiple
- Status: Active

"""
    
    # Add new session entry
    session_entry = f"""
## Session {today.strftime('%H:%M')}

### Summary
[Session summary to be added]

### Key Points
- 

### Decisions Made
- 

### User Preferences Expressed
- 

### Tasks Completed
- 

### Tasks Started
- 

### Issues/Blockers
- 

---
"""
    
    content += session_entry
    
    try:
        today_file.write_text(content)
        log(f"✅ Memory written: {today_file}")
        return True
    except Exception as e:
        log(f"❌ Failed to write memory: {e}")
        return False

def verify_memory_system():
    """Verify memory system is working"""
    # Check yesterday's file exists
    yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
    yesterday_file = MEMORY_DIR / f"{yesterday}.md"
    
    if not yesterday_file.exists():
        log(f"⚠️  WARNING: Yesterday's memory file missing: {yesterday_file}")
    else:
        log(f"✅ Yesterday's memory file exists: {yesterday_file}")
    
    # Check today's file
    today = datetime.now().strftime('%Y-%m-%d')
    today_file = MEMORY_DIR / f"{today}.md"
    
    if today_file.exists():
        size = today_file.stat().st_size
        log(f"✅ Today's memory file exists: {today_file} ({size} bytes)")
    else:
        log(f"⚠️  Today's memory file missing: {today_file}")

if __name__ == "__main__":
    log("=" * 60)
    log("Daily Memory Logger - Starting")
    
    # Verify system
    verify_memory_system()
    
    # Write today's memory
    success = write_daily_memory()
    
    if success:
        log("✅ Memory system operational")
        sys.exit(0)
    else:
        log("❌ Memory system failed")
        sys.exit(1)
