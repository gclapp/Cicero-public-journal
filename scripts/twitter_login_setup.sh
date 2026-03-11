#!/bin/bash
# twitter_login_setup.sh - Initial Twitter login with virtual display
# Run this once to save the session, then automated posting will work

echo "🐦 Twitter Login Setup"
echo "======================"
echo ""
echo "This will open a browser for you to log in to Twitter."
echo "Your session will be saved for future automated posts."
echo ""

# Check if xvfb is running
if ! pgrep -x "Xvfb" > /dev/null; then
    echo "Starting virtual display..."
    Xvfb :99 -screen 0 1280x800x24 &
    export DISPLAY=:99
    sleep 2
fi

# Set display
export DISPLAY=:99

# Run the Python script
cd /home/ubuntu/.openclaw/workspace
python3 scripts/twitter_browser_post.py "Test login session"

echo ""
echo "✅ Setup complete. Session saved."
echo "You can now close this if the browser is done."
