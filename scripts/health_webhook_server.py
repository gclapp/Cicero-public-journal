#!/usr/bin/env python3
"""
Health Data Webhook Server
Receives weight and steps via HTTP POST from iPhone Shortcuts
"""

from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import urllib.parse
from datetime import datetime
from pathlib import Path

HEALTH_DATA_FILE = Path.home() / ".openclaw" / "workspace" / "data" / "health-webhook-data.json"

class HealthHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        if self.path != '/health':
            self.send_error(404)
            return
        
        content_length = int(self.headers.get('Content-Length', 0))
        post_data = self.rfile.read(content_length).decode('utf-8')
        
        try:
            # Try JSON first
            data = json.loads(post_data)
        except json.JSONDecodeError:
            # Try form data
            data = urllib.parse.parse_qs(post_data)
            data = {k: v[0] if len(v) == 1 else v for k, v in data.items()}
        
        # Validate and store
        result = self.store_health_data(data)
        
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(result).encode())
    
    def store_health_data(self, data):
        """Store health data to JSON file"""
        HEALTH_DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
        
        # Load existing
        all_data = []
        if HEALTH_DATA_FILE.exists():
            with open(HEALTH_DATA_FILE, 'r') as f:
                all_data = json.load(f)
        
        # Format entry
        entry = {
            "weight": float(data.get('weight', 0)) if data.get('weight') else None,
            "steps": int(data.get('steps', 0)) if data.get('steps') else None,
            "date": data.get('date', datetime.now().strftime('%Y-%m-%d')),
            "timestamp": datetime.now().isoformat(),
            "source": "webhook"
        }
        
        all_data.append(entry)
        
        # Save
        with open(HEALTH_DATA_FILE, 'w') as f:
            json.dump(all_data, f, indent=2)
        
        return {
            "status": "success",
            "message": f"Recorded weight={entry['weight']}, steps={entry['steps']}",
            "total_entries": len(all_data)
        }
    
    def log_message(self, format, *args):
        # Suppress default logging
        pass

def run_server(port=8080):
    server = HTTPServer(('0.0.0.0', port), HealthHandler)
    print(f"Health webhook server running on port {port}")
    print(f"Endpoint: http://YOUR_IP:{port}/health")
    print("\nTest with:")
    print(f"curl -X POST http://localhost:{port}/health \\")
    print("  -H 'Content-Type: application/json' \\")
    print('  -d \'{"weight": 238.5, "steps": 8432}\'')
    server.serve_forever()

if __name__ == "__main__":
    run_server()
