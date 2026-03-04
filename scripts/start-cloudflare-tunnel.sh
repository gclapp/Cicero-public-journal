#!/bin/bash
# Start Cloudflare Tunnel for Gmail webhook
# This creates a free HTTPS tunnel to localhost:8080

echo "Starting Cloudflare Tunnel..."
echo "This will give you a permanent HTTPS URL for Google Pub/Sub"
echo ""

cloudflared tunnel --url http://localhost:8080
