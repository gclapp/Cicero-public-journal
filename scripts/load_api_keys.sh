#!/bin/bash
# load_api_keys.sh - Centralized API key loader
# Source this file in all cron jobs to ensure keys are available
# Created: 2026-04-10

# Load from .bashrc (where keys are defined)
if [ -f "$HOME/.bashrc" ]; then
    export BRAVE_API_KEY=$(grep "export BRAVE_API_KEY=" "$HOME/.bashrc" | head -1 | cut -d'"' -f2)
    export ELEVENLABS_API_KEY=$(grep "export ELEVENLABS_API_KEY=" "$HOME/.bashrc" | head -1 | cut -d'"' -f2)
fi

# Load from consolidated credentials (fallback)
if [ -f "$HOME/.openclaw/config/sensitive-credentials.json" ]; then
    # Use Python to extract keys from JSON (more reliable than jq)
    export OPENAI_API_KEY=$(python3 -c "import json; print(json.load(open('$HOME/.openclaw/config/sensitive-credentials.json')).get('openai', {}).get('api_key', ''))" 2>/dev/null)
fi

# Export for child processes
export BRAVE_API_KEY
export ELEVENLABS_API_KEY
export OPENAI_API_KEY
