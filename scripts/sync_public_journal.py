#!/usr/bin/env python3
"""
sync_public_journal.py - Sync private journal entries to public journal
Creates sanitized public versions of private entries
"""

import json
from pathlib import Path
from datetime import datetime
import re

WORKSPACE = Path.home() / ".openclaw" / "workspace"
PRIVATE_JOURNAL_DIR = WORKSPACE / "memory"
PUBLIC_JOURNAL_DIR = WORKSPACE / "public-journal"
SYNC_LOG = WORKSPACE / "data" / "journal-sync-log.json"

def load_sync_log():
    """Load record of synced entries"""
    if SYNC_LOG.exists():
        with open(SYNC_LOG) as f:
            return json.load(f)
    return {"synced_files": [], "last_sync": None}

def save_sync_log(log):
    """Save sync record"""
    SYNC_LOG.parent.mkdir(parents=True, exist_ok=True)
    with open(SYNC_LOG, 'w') as f:
        json.dump(log, f, indent=2)

def sanitize_for_public(content):
    """Remove sensitive info from private journal for public version"""
    # Remove specific personal details
    content = re.sub(r'\b\d{3}-\d{2}-\d{4}\b', '[SSN REDACTED]', content)  # SSN
    content = re.sub(r'\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b', '[CARD REDACTED]', content)  # Credit cards
    
    # Remove API keys and passwords
    content = re.sub(r'(api[_-]?key|password|token|secret)["\']?\s*[:=]\s*["\']?[^\s"\']+', r'\1: [REDACTED]', content, flags=re.IGNORECASE)
    
    # Remove specific addresses
    content = re.sub(r'\d+\s+[^\n]+(?:Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|Drive|Dr|Lane|Ln|Way)[^\n,]*', '[ADDRESS REDACTED]', content, flags=re.IGNORECASE)
    
    return content

def sync_journal_entries():
    """Sync private journal entries to public journal"""
    sync_log = load_sync_log()
    synced_count = 0
    
    # Ensure directories exist
    PRIVATE_JOURNAL_DIR.mkdir(parents=True, exist_ok=True)
    PUBLIC_JOURNAL_DIR.mkdir(parents=True, exist_ok=True)
    
    # Find all private journal files (YYYY-MM-DD.md format)
    for journal_file in PRIVATE_JOURNAL_DIR.glob("[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9].md"):
        if journal_file.name in sync_log["synced_files"]:
            continue  # Already synced
        
        # Read private content
        with open(journal_file) as f:
            content = f.read()
        
        # Sanitize for public
        public_content = sanitize_for_public(content)
        
        # Add public journal header
        public_content = f"""# {journal_file.stem}

*Public journal entry — auto-generated from private notes*

---

{public_content}

---

*Synced: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
"""
        
        # Write to public journal
        public_file = PUBLIC_JOURNAL_DIR / journal_file.name
        with open(public_file, 'w') as f:
            f.write(public_content)
        
        # Mark as synced
        sync_log["synced_files"].append(journal_file.name)
        synced_count += 1
        print(f"✅ Synced: {journal_file.name}")
    
    # Update sync log
    sync_log["last_sync"] = datetime.now().isoformat()
    save_sync_log(sync_log)
    
    if synced_count > 0:
        print(f"\n📊 Synced {synced_count} new journal entries")
    else:
        print("📊 No new journal entries to sync")
    
    return synced_count

if __name__ == "__main__":
    sync_journal_entries()
