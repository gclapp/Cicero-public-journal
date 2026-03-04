#!/usr/bin/env python3
"""
Gmail Pub/Sub webhook receiver
Receives push notifications when new emails arrive
"""

from flask import Flask, request, jsonify
import json
import base64
from pathlib import Path
from datetime import datetime

app = Flask(__name__)

LOG_FILE = Path.home() / ".openclaw" / "workspace" / "logs" / "gmail-webhook.log"
PENDING_DIR = Path.home() / ".openclaw" / "workspace" / "data" / "pending-emails"

def log_message(msg):
    """Log with timestamp"""
    timestamp = datetime.now().isoformat()
    log_entry = f"[{timestamp}] {msg}\n"
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG_FILE, 'a') as f:
        f.write(log_entry)
    print(log_entry.strip())

def save_notification(data):
    """Save notification for processing"""
    PENDING_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime('%Y%m%d-%H%M%S')
    filename = PENDING_DIR / f"notification-{timestamp}.json"
    with open(filename, 'w') as f:
        json.dump(data, f, indent=2)
    return filename

@app.route('/webhook/gmail', methods=['POST'])
def gmail_webhook():
    """Receive Gmail Pub/Sub notifications"""
    try:
        # Pub/Sub sends base64-encoded message
        envelope = request.get_json()
        
        log_message(f"Received webhook: {json.dumps(envelope, indent=2)[:500]}")
        
        if not envelope:
            log_message("ERROR: Empty request body")
            return jsonify({"status": "error", "message": "Empty body"}), 400
        
        # Decode the Pub/Sub message
        if 'message' in envelope:
            message = envelope['message']
            if 'data' in message:
                # Decode base64 data
                decoded_data = base64.b64decode(message['data']).decode('utf-8')
                notification_data = json.loads(decoded_data)
                
                log_message(f"Decoded notification: {json.dumps(notification_data, indent=2)[:500]}")
                
                # Save for processing
                saved_file = save_notification({
                    'received_at': datetime.now().isoformat(),
                    'pubsub_message': message,
                    'decoded_data': notification_data
                })
                
                log_message(f"Saved notification to: {saved_file}")
                
                # TODO: Trigger email fetch via Gmail API
                # This will be implemented once OAuth is set up
                
                return jsonify({
                    "status": "success",
                    "message": "Notification received",
                    "saved_to": str(saved_file)
                }), 200
        
        # Handle subscription verification (initial setup)
        if 'subscription' in envelope:
            log_message(f"Subscription verification: {envelope['subscription']}")
            return jsonify({"status": "verified"}), 200
        
        log_message(f"Unknown message format: {envelope}")
        return jsonify({"status": "received"}), 200
        
    except Exception as e:
        log_message(f"ERROR processing webhook: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/webhook/gmail', methods=['GET'])
def gmail_webhook_verify():
    """Handle GET requests (for verification)"""
    return jsonify({"status": "ok", "message": "Gmail webhook endpoint ready"}), 200

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({"status": "healthy"}), 200

if __name__ == '__main__':
    # For development/testing
    log_message("Starting Gmail webhook server on port 8080")
    app.run(host='0.0.0.0', port=8080, debug=False)
