#!/usr/bin/env python3
"""
Credential Manager - Unified API for accessing all API keys and tokens
Reads from consolidated sensitive-credentials.json
"""

import json
import os
from pathlib import Path

CREDENTIALS_FILE = Path.home() / ".openclaw" / "config" / "sensitive-credentials.json"

def load_credentials():
    """Load all credentials from consolidated file"""
    if not CREDENTIALS_FILE.exists():
        raise FileNotFoundError(f"Credentials file not found: {CREDENTIALS_FILE}")
    
    with open(CREDENTIALS_FILE) as f:
        return json.load(f)

def get_api_key(service):
    """Get API key for a service"""
    creds = load_credentials()
    
    service_config = creds.get(service.lower())
    if not service_config:
        raise KeyError(f"Service '{service}' not found in credentials")
    
    return service_config.get("api_key") or service_config.get("client_secret")

def get_token_status(service):
    """Get token status for a service"""
    creds = load_credentials()
    
    service_config = creds.get(service.lower())
    if not service_config:
        return None
    
    return {
        "status": service_config.get("status"),
        "last_verified": service_config.get("last_verified"),
        "age_days": service_config.get("token_age_days") or service_config.get("config_age_days"),
        "alert_threshold": service_config.get("alert_threshold_days"),
        "critical_threshold": service_config.get("critical_threshold_days")
    }

def update_token_age(service, age_days):
    """Update token age in credentials file"""
    creds = load_credentials()
    
    if service.lower() in creds:
        if "token_age_days" in creds[service.lower()]:
            creds[service.lower()]["token_age_days"] = age_days
        elif "config_age_days" in creds[service.lower()]:
            creds[service.lower()]["config_age_days"] = age_days
        
        with open(CREDENTIALS_FILE, 'w') as f:
            json.dump(creds, f, indent=2)

def list_all_services():
    """List all configured services"""
    creds = load_credentials()
    services = []
    
    for key, value in creds.items():
        if key.startswith("_"):
            continue
        services.append({
            "name": key,
            "status": value.get("status", "unknown"),
            "type": "api_key" if "api_key" in value else "oauth" if "token_file" in value else "config"
        })
    
    return services

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: credential_manager.py <command> [args]")
        print("Commands:")
        print("  get <service>     - Get API key for service")
        print("  status <service>  - Get token status")
        print("  list              - List all services")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "get" and len(sys.argv) >= 3:
        service = sys.argv[2]
        try:
            key = get_api_key(service)
            print(f"{service}: {key[:20]}...")
        except Exception as e:
            print(f"Error: {e}")
            sys.exit(1)
    
    elif command == "status" and len(sys.argv) >= 3:
        service = sys.argv[2]
        try:
            status = get_token_status(service)
            if status:
                print(f"{service}:")
                for k, v in status.items():
                    print(f"  {k}: {v}")
            else:
                print(f"Service '{service}' not found")
        except Exception as e:
            print(f"Error: {e}")
            sys.exit(1)
    
    elif command == "list":
        services = list_all_services()
        print("Configured Services:")
        for svc in services:
            print(f"  {svc['name']}: {svc['status']} ({svc['type']})")
    
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)