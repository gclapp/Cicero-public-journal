#!/usr/bin/env python3
"""
Memory Guardian - Ensures memory is never lost again
Runs at end of every session to verify memory was written
"""

import os
import sys
from pathlib import Path
from datetime import datetime

MEMORY_DIR = Path.home() / ".openclaw" / "workspace" / "memory"
TODAY_FILE = MEMORY_DIR / f"{datetime.now().strftime('%Y-%m-%d')}.md"

def check_memory_written():
    """Verify today's memory file exists and has content"""
    if not TODAY_FILE.exists():
        return False, f"Memory file missing: {TODAY_FILE}"
    
    content = TODAY_FILE.read_text()
    if len(content) < 100:
        return False, f"Memory file too short ({len(content)} chars)"
    
    # Check if it was written in the last hour
    mtime = TODAY_FILE.stat().st_mtime
    age_hours = (datetime.now().timestamp() - mtime) / 3600
    
    if age_hours > 2:
        return False, f"Memory file stale ({age_hours:.1f} hours old)"
    
    return True, f"Memory file OK: {len(content)} chars, {age_hours:.1f} hours old"

def emergency_write_memory():
    """Write minimal memory if automatic system failed"""
    MEMORY_DIR.mkdir(parents=True, exist_ok=True)
    
    content = f"""# {datetime.now().strftime('%Y-%m-%d')} - EMERGENCY MEMORY BACKUP

## Session Active
- Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- Status: Memory guardian triggered - automatic logging failed

## CRITICAL: Review and Expand This File
The automatic memory system failed. This is an emergency backup.
Please manually review and expand this file with:
- Key decisions made
- User preferences expressed
- Tasks completed or started
- Important context for future sessions

## Next Actions
- [ ] Fix root cause of memory system failure
- [ ] Backfill any lost context from this session
- [ ] Verify memory system working for next session

---
*Emergency backup created by memory_guardian.py*
"""
    
    TODAY_FILE.write_text(content)
    return TODAY_FILE

if __name__ == "__main__":
    ok, msg = check_memory_written()
    
    if not ok:
        print(f"⚠️  MEMORY ALERT: {msg}")
        print("📝 Writing emergency backup...")
        backup_file = emergency_write_memory()
        print(f"✅ Emergency backup written: {backup_file}")
        sys.exit(1)
    else:
        print(f"✅ {msg}")
        sys.exit(0)
