#!/usr/bin/env python3
"""
Search Configuration Manager
Handles creating, updating, and managing watch search configurations
"""

import json
import sys
from pathlib import Path
from datetime import datetime

CONFIG_FILE = Path.home() / ".openclaw" / "workspace" / "dashboard" / "search-config.json"

def load_config():
    """Load search configuration"""
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
    return {"searches": [], "completedSearches": []}

def save_config(config):
    """Save search configuration"""
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=2)

def create_search(name, brand, model_numbers, year_min, year_max, 
                  dial_colors, case_materials, sources, schedule="twice_daily"):
    """Create a new search configuration"""
    config = load_config()
    
    search_id = f"search-{int(datetime.now().timestamp())}"
    
    new_search = {
        "id": search_id,
        "name": name,
        "brand": brand,
        "modelNumbers": model_numbers if isinstance(model_numbers, list) else [m.strip() for m in model_numbers.split(',') if m.strip()],
        "years": {"min": int(year_min), "max": int(year_max)},
        "dialColors": dial_colors if isinstance(dial_colors, list) else [dial_colors],
        "caseMaterials": case_materials if isinstance(case_materials, list) else [case_materials],
        "sources": sources if isinstance(sources, list) else [sources],
        "status": "active",
        "createdAt": datetime.now().strftime('%Y-%m-%d'),
        "lastRun": datetime.now().isoformat(),
        "watchesFound": 0,
        "schedule": schedule
    }
    
    config["searches"].append(new_search)
    save_config(config)
    
    print(f"✅ Created search: {name} (ID: {search_id})")
    return search_id

def toggle_search(search_id):
    """Toggle search on/off"""
    config = load_config()
    
    for search in config["searches"]:
        if search["id"] == search_id:
            search["status"] = "paused" if search["status"] == "active" else "active"
            save_config(config)
            print(f"{'▶️' if search['status'] == 'active' else '⏸'} Search '{search['name']}' is now {search['status']}")
            return True
    
    print(f"❌ Search not found: {search_id}")
    return False

def complete_search(search_id):
    """Mark a search as completed"""
    config = load_config()
    
    for i, search in enumerate(config["searches"]):
        if search["id"] == search_id:
            search["status"] = "completed"
            search["completedAt"] = datetime.now().isoformat()
            config["completedSearches"].append(search)
            config["searches"].pop(i)
            save_config(config)
            print(f"✅ Search '{search['name']}' marked as completed")
            return True
    
    print(f"❌ Search not found: {search_id}")
    return False

def delete_search(search_id):
    """Delete a search"""
    config = load_config()
    
    for i, search in enumerate(config["searches"]):
        if search["id"] == search_id:
            config["searches"].pop(i)
            save_config(config)
            print(f"🗑️ Deleted search: {search['name']}")
            return True
    
    # Also check completed searches
    for i, search in enumerate(config["completedSearches"]):
        if search["id"] == search_id:
            config["completedSearches"].pop(i)
            save_config(config)
            print(f"🗑️ Deleted completed search: {search['name']}")
            return True
    
    print(f"❌ Search not found: {search_id}")
    return False

def list_searches():
    """List all searches"""
    config = load_config()
    
    print("\n" + "=" * 60)
    print("ACTIVE SEARCHES")
    print("=" * 60)
    
    active = [s for s in config["searches"] if s["status"] == "active"]
    paused = [s for s in config["searches"] if s["status"] == "paused"]
    
    if active:
        for s in active:
            print(f"▶️  {s['name']} ({s['brand']})")
            print(f"   Models: {', '.join(s['modelNumbers'])}")
            print(f"   Years: {s['years']['min']}-{s['years']['max']}")
            print(f"   Found: {s['watchesFound']} watches")
            print(f"   ID: {s['id']}")
            print()
    else:
        print("No active searches\n")
    
    if paused:
        print("PAUSED SEARCHES:")
        for s in paused:
            print(f"⏸  {s['name']} ({s['brand']})")
        print()
    
    if config["completedSearches"]:
        print("=" * 60)
        print("COMPLETED SEARCHES")
        print("=" * 60)
        for s in config["completedSearches"]:
            print(f"✅ {s['name']} ({s['brand']}) - {s['watchesFound']} watches found")

def get_active_searches():
    """Get list of active search IDs for the cron job"""
    config = load_config()
    return [s for s in config["searches"] if s["status"] == "active"]

def update_watch_count(search_id, count):
    """Update the watch count for a search"""
    config = load_config()
    
    for search in config["searches"]:
        if search["id"] == search_id:
            search["watchesFound"] = count
            search["lastRun"] = datetime.now().isoformat()
            save_config(config)
            return True
    
    return False

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Manage watch search configurations")
    subparsers = parser.add_subparsers(dest="command", help="Commands")
    
    # Create command
    create_parser = subparsers.add_parser("create", help="Create a new search")
    create_parser.add_argument("--name", required=True, help="Search name")
    create_parser.add_argument("--brand", required=True, help="Watch brand")
    create_parser.add_argument("--models", required=True, help="Comma-separated model numbers")
    create_parser.add_argument("--year-min", type=int, default=1970, help="Minimum year")
    create_parser.add_argument("--year-max", type=int, default=1985, help="Maximum year")
    create_parser.add_argument("--dials", default="blue,black,champagne", help="Comma-separated dial colors")
    create_parser.add_argument("--materials", default="gold,two-tone", help="Comma-separated case materials")
    create_parser.add_argument("--sources", default="chrono24", help="Comma-separated sources")
    create_parser.add_argument("--schedule", default="twice_daily", help="Search schedule")
    
    # Toggle command
    toggle_parser = subparsers.add_parser("toggle", help="Toggle search on/off")
    toggle_parser.add_argument("search_id", help="Search ID")
    
    # Complete command
    complete_parser = subparsers.add_parser("complete", help="Mark search as completed")
    complete_parser.add_argument("search_id", help="Search ID")
    
    # Delete command
    delete_parser = subparsers.add_parser("delete", help="Delete a search")
    delete_parser.add_argument("search_id", help="Search ID")
    
    # List command
    list_parser = subparsers.add_parser("list", help="List all searches")
    
    args = parser.parse_args()
    
    if args.command == "create":
        create_search(
            name=args.name,
            brand=args.brand,
            model_numbers=args.models,
            year_min=args.year_min,
            year_max=args.year_max,
            dial_colors=[c.strip() for c in args.dials.split(',')],
            case_materials=[m.strip() for m in args.materials.split(',')],
            sources=[s.strip() for s in args.sources.split(',')],
            schedule=args.schedule
        )
    elif args.command == "toggle":
        toggle_search(args.search_id)
    elif args.command == "complete":
        complete_search(args.search_id)
    elif args.command == "delete":
        delete_search(args.search_id)
    elif args.command == "list":
        list_searches()
    else:
        parser.print_help()
