#!/bin/bash
# cron-backup.sh - Backup and restore cron jobs
# Run this after any system update or restart to ensure cron jobs persist

BACKUP_DIR="/home/ubuntu/.openclaw/workspace/config/cron-backups"
BACKUP_FILE="$BACKUP_DIR/crontab-$(date +%Y%m%d-%H%M%S).txt"
LATEST_LINK="$BACKUP_DIR/crontab-latest.txt"

mkdir -p "$BACKUP_DIR"

case "${1:-backup}" in
    backup)
        echo "Backing up current crontab..."
        crontab -l > "$BACKUP_FILE"
        ln -sf "$BACKUP_FILE" "$LATEST_LINK"
        echo "Saved to: $BACKUP_FILE"
        echo "Current jobs:"
        crontab -l | wc -l
        ;;
    restore)
        if [ -f "$LATEST_LINK" ]; then
            echo "Restoring from: $LATEST_LINK"
            crontab "$LATEST_LINK"
            echo "Restored cron jobs:"
            crontab -l
        else
            echo "No backup found at $LATEST_LINK"
            exit 1
        fi
        ;;
    verify)
        echo "=== CURRENT CRON JOBS ==="
        crontab -l
        echo ""
        echo "=== EXPECTED JOBS ==="
        cat << 'EXPECTED'
1. Heartbeat check - every 55 minutes
2. Watch hunt - 9 AM & 6 PM PT daily
3. Calendar refresh - 6:55 AM PT daily
4. IMAP email check - every 15 minutes
5. Daily competitor report - 7 AM & 2 PM PT daily
6. Weekly security audit - Sundays 8 AM PT
7. Reddit weekly report - Sundays 9 AM PT
8. Weekly email report - Saturdays 9 AM PT
9. Stock price fetch with 30-day history - 6 PM PT daily
10. Token health monitor - 9 AM & 9 PM PT daily (Whoop + Calendar)
11. Whoop token monitor - every 6 hours
12. Whoop auto-refresh - every 30 minutes
13. Vitus health agent - 3x daily (morning/midday/evening)
EXPECTED
        ;;
    *)
        echo "Usage: $0 [backup|restore|verify]"
        exit 1
        ;;
esac
