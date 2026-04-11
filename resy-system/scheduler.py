#!/usr/bin/env python3
"""
Resy Scheduler - Runs scanner every 12 hours
Can be run as a daemon or via cron
"""

import schedule
import time
import subprocess
import sys
from datetime import datetime
from pathlib import Path

LOG_FILE = Path(__file__).parent / "logs" / "scheduler.log"

def log(message):
    """Log with timestamp"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_msg = f"[{timestamp}] {message}"
    print(log_msg)
    
    # Ensure logs directory exists
    LOG_FILE.parent.mkdir(exist_ok=True)
    
    with open(LOG_FILE, 'a') as f:
        f.write(log_msg + '\n')

def run_scanner():
    """Run the calendar scanner"""
    log("=" * 60)
    log("Starting scheduled scan...")
    
    scanner_path = Path(__file__).parent / "calendar_scanner.py"
    
    try:
        result = subprocess.run(
            [sys.executable, str(scanner_path)],
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout
        )
        
        # Log output
        if result.stdout:
            for line in result.stdout.strip().split('\n'):
                log(f"  {line}")
        
        if result.returncode == 0:
            log("✅ Scan completed successfully")
        else:
            log(f"❌ Scan failed with code {result.returncode}")
            if result.stderr:
                log(f"  Error: {result.stderr}")
                
    except subprocess.TimeoutExpired:
        log("❌ Scan timed out after 5 minutes")
    except Exception as e:
        log(f"❌ Error running scanner: {e}")
    
    log("=" * 60)
    log("")

def main():
    """Main scheduler loop"""
    log("🍽️  Resy Scheduler Started")
    log("   Running every 12 hours (00:00 and 12:00)")
    log("")
    
    # Schedule every 12 hours
    schedule.every(12).hours.do(run_scanner)
    
    # Also run immediately on startup
    run_scanner()
    
    # Keep running
    while True:
        schedule.run_pending()
        time.sleep(60)  # Check every minute

if __name__ == "__main__":
    main()
