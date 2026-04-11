#!/bin/bash

echo "🍽️  Resy Automation System Setup"
echo "================================"
echo ""

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 not found. Please install Python 3."
    exit 1
fi

echo "✅ Python found"

# Install Flask
if ! python3 -c "import flask" 2>/dev/null; then
    echo "📦 Installing Flask..."
    pip3 install flask --break-system-packages 2>/dev/null || pip3 install flask --user
fi

echo "✅ Flask installed"

# Create data directory
cd "$(dirname "$0")"
mkdir -p data logs

# Initialize data files
if [ ! -f data/restaurants.json ]; then
    echo '{"restaurants": []}' > data/restaurants.json
    echo "✅ Created restaurants.json"
fi

if [ ! -f data/users.json ]; then
    cat > data/users.json << 'EOF'
{
  "users": [
    {
      "email": "[REDACTED]",
      "password_hash": "96cae35ce8a9b0244178bf28e4966c2ce1b8385723a96a6b838858dd6ca0a29e",
      "is_admin": true,
      "created_at": "2026-04-11T05:58:00"
    }
  ]
}
EOF
    echo "✅ Created users.json"
fi

if [ ! -f data/reservations.json ]; then
    echo '{"reservations": []}' > data/reservations.json
    echo "✅ Created reservations.json"
fi

# Check Resy credentials
if [ ! -f ~/.openclaw/config/resy-credentials.json ]; then
    echo ""
    echo "⚠️  Resy credentials not found!"
    echo "   Please ensure you've set up Resy API access."
fi

# Check Calendar credentials
if [ ! -f ~/.openclaw/credentials/calendar-token.pickle ]; then
    echo ""
    echo "⚠️  Google Calendar credentials not found!"
    echo "   Run: python3 ../scripts/calendar_reader.py"
fi

echo ""
echo "================================"
echo "✅ Setup complete!"
echo ""
echo "To start the web interface:"
echo "  ./start.sh"
echo ""
echo "To run the calendar scanner:"
echo "  ./run_scanner.sh"
echo ""
echo "Default login:"
echo "  Email: [REDACTED]"
echo "  Password: changeme123"
echo ""
echo "🌐 Web interface will be at: http://localhost:5000"
