#!/bin/bash
# Gmail Pub/Sub Webhook Server
# Receives push notifications when new emails arrive

SCRIPT_DIR="/home/ubuntu/.openclaw/workspace/scripts"
LOG_FILE="/home/ubuntu/.openclaw/workspace/logs/gmail-webhook-server.log"
PID_FILE="/tmp/gmail-webhook.pid"

case "$1" in
    start)
        if [ -f "$PID_FILE" ] && kill -0 $(cat "$PID_FILE") 2>/dev/null; then
            echo "Gmail webhook server already running (PID: $(cat $PID_FILE))"
            exit 1
        fi
        
        echo "Starting Gmail webhook server..."
        nohup python3 "$SCRIPT_DIR/gmail_webhook_server.py" >> "$LOG_FILE" 2>&1 &
        echo $! > "$PID_FILE"
        echo "Started with PID: $(cat $PID_FILE)"
        echo "Logs: tail -f $LOG_FILE"
        ;;
    
    stop)
        if [ -f "$PID_FILE" ]; then
            PID=$(cat "$PID_FILE")
            if kill -0 "$PID" 2>/dev/null; then
                echo "Stopping Gmail webhook server (PID: $PID)..."
                kill "$PID"
                rm "$PID_FILE"
                echo "Stopped"
            else
                echo "Process not running, cleaning up PID file"
                rm "$PID_FILE"
            fi
        else
            echo "No PID file found"
        fi
        ;;
    
    status)
        if [ -f "$PID_FILE" ] && kill -0 $(cat "$PID_FILE") 2>/dev/null; then
            echo "Gmail webhook server is running (PID: $(cat $PID_FILE))"
        else
            echo "Gmail webhook server is not running"
        fi
        ;;
    
    restart)
        $0 stop
        sleep 2
        $0 start
        ;;
    
    *)
        echo "Usage: $0 {start|stop|status|restart}"
        exit 1
        ;;
esac
