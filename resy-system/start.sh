#!/bin/bash

# Resy System Startup Script

cd "$(dirname "$0")"

# Create data directory
mkdir -p data

# Initialize data files if they don't exist
if [ ! -f data/restaurants.json ]; then
    echo '{"restaurants": []}' > data/restaurants.json
fi

if [ ! -f data/users.json ]; then
    echo '{"users": [{"email": "[REDACTED]", "password_hash": "4cb1c7c2c1b6e9c2e0c5a0b1d4e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8", "is_admin": true, "created_at": "2026-04-11T00:00:00"}]}' > data/users.json
fi

if [ ! -f data/reservations.json ]; then
    echo '{"reservations": []}' > data/reservations.json
fi

# Check if Flask is installed
if ! python3 -c "import flask" 2>/dev/null; then
    echo "Installing Flask..."
    pip3 install flask
fi

echo "🍽️  Starting Resy Manager..."
echo ""
echo "Web Interface: http://localhost:5000"
echo "Default Login: [REDACTED] / changeme123"
echo ""
echo "Press Ctrl+C to stop"
echo ""

python3 app.py
