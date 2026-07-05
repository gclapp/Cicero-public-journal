#!/usr/bin/env python3
"""Monitor OpenClaw logs for duplicate Telegram outbound sends and alert."""
import json, re, sys, os
from datetime import datetime, timezone, timedelta
from pathlib import Path

LOG_DIR = Path('/tmp/openclaw')
ALERT_LOG = Path('/home/ubuntu/.openclaw/workspace/logs/telegram-duplicate-alerts.log')
STATE_FILE = Path('/home/ubuntu/.openclaw/workspace/state/telegram-duplicate-state.json')

ALERT_LOG.parent.mkdir(parents=True, exist_ok=True)
STATE_FILE.parent.mkdir(parents=True, exist_ok=True)

# Load previous state
recent_sends = {}
if STATE_FILE.exists():
    try:
        with open(STATE_FILE) as f:
            recent_sends = json.load(f)
    except Exception:
        recent_sends = {}

# Clean old entries (> 5 min)
cutoff = (datetime.now(timezone.utc) - timedelta(minutes=5)).isoformat()
recent_sends = {k: v for k, v in recent_sends.items() if v.get('ts', '') > cutoff}

duplicates = []
# Parse today's log
log_file = LOG_DIR / f'openclaw-{datetime.now(timezone.utc).strftime("%Y-%m-%d")}.log'
if log_file.exists():
    with open(log_file, 'r', errors='ignore') as f:
        for line in f:
            if 'telegram outbound send ok' not in line:
                continue
            m = re.search(r'messageId[:=](\d+)', line)
            txt_m = re.search(r'text":"([^"]{20,})', line)
            if not m:
                continue
            msg_id = m.group(1)
            text = (txt_m.group(1) if txt_m else '')[:120]
            ts = datetime.now(timezone.utc).isoformat()
            key = text
            if key in recent_sends:
                duplicates.append({
                    'ts': ts,
                    'text': text,
                    'first_message_id': recent_sends[key]['msg_id'],
                    'duplicate_message_id': msg_id
                })
            else:
                recent_sends[key] = {'msg_id': msg_id, 'ts': ts}

# Save state
with open(STATE_FILE, 'w') as f:
    json.dump(recent_sends, f, indent=2)

# Log duplicates
if duplicates:
    with open(ALERT_LOG, 'a') as f:
        for d in duplicates:
            f.write(json.dumps(d) + '\n')
    print(f'ALERT: {len(duplicates)} duplicate Telegram sends detected')
    sys.exit(1)
else:
    print('OK: no duplicate Telegram sends detected')
    sys.exit(0)
