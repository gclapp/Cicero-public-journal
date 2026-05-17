"""Configuration for Cigna directory scraper."""

import json
import os
from pathlib import Path

# Base paths
WORKSPACE = Path("/home/ubuntu/.openclaw/workspace")
PROJECT_DIR = WORKSPACE / "projects" / "cigna-directory"
CREDENTIALS_DIR = Path.home() / ".openclaw" / "credentials"
DATA_DIR = PROJECT_DIR / "data"

# Ensure data directory exists
DATA_DIR.mkdir(exist_ok=True)

# Cigna URLs
CIGNA_LOGIN_URL = "https://my.cigna.com/web/secure/consumer/home"
CIGNA_DIRECTORY_URL = "https://www.cigna.com/members/health-care-providers"
CIGNA_PROVIDER_SEARCH_URL = "https://www.cigna.com/members/health-care-providers/find-a-doctor"

# Scraper settings
DEFAULT_TIMEOUT = 30000  # 30 seconds
NAVIGATION_TIMEOUT = 60000  # 60 seconds
DELAY_BETWEEN_REQUESTS = 2.5  # seconds
MAX_RETRIES = 3

# Rate limiting
REQUESTS_PER_MINUTE = 20  # Conservative to avoid detection


def load_credentials() -> dict:
    """Load Cigna credentials from secure storage."""
    creds_file = CREDENTIALS_DIR / "cigna-credentials.json"
    
    if not creds_file.exists():
        return {}
    
    with open(creds_file, 'r') as f:
        return json.load(f)


def save_credentials(username: str, password: str) -> None:
    """Save Cigna credentials securely."""
    CREDENTIALS_DIR.mkdir(parents=True, exist_ok=True)
    creds_file = CREDENTIALS_DIR / "cigna-credentials.json"
    
    creds = {
        "username": username,
        "password": password,
        "created_at": str(datetime.now().isoformat())
    }
    
    with open(creds_file, 'w') as f:
        json.dump(creds, f, indent=2)
    
    # Secure the file
    os.chmod(creds_file, 0o600)


def get_storage_state_path() -> Path:
    """Get path for Playwright storage state (cookies/session)."""
    return CREDENTIALS_DIR / "cigna-storage-state.json"
