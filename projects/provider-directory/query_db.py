#!/usr/bin/env python3
"""Query the provider database."""

import sqlite3
import json
import sys
from pathlib import Path

DB_PATH = Path(__file__).parent / "data" / "providers.db"


def get_connection():
    """Get database connection."""
    return sqlite3.connect(DB_PATH)


def list_all():
    """List all providers."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT name, specialties, city, state, source 
        FROM providers 
        WHERE source = 'healthgrades'
        ORDER BY name
    """)
    rows = cursor.fetchall()
    conn.close()
    
    print(f"\nTotal providers: {len(rows)}\n")
    for row in rows[:20]:
        name, specs, city, state, source = row
        location = f"{city}, {state}" if city and state else "Unknown"
        print(f"  {name}")
        print(f"    Location: {location}")
        print(f"    Specialties: {specs}")
        print()
    
    if len(rows) > 20:
        print(f"  ... and {len(rows) - 20} more")


def search_by_name(name_query):
    """Search providers by name."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT name, specialties, city, state 
        FROM providers 
        WHERE source = 'healthgrades' AND name LIKE ?
        ORDER BY name
    """, (f"%{name_query}%",))
    rows = cursor.fetchall()
    conn.close()
    
    print(f"\nFound {len(rows)} providers matching '{name_query}':\n")
    for row in rows:
        name, specs, city, state = row
        location = f"{city}, {state}" if city and state else "Unknown"
        print(f"  {name}")
        print(f"    Location: {location}")
        print(f"    Specialties: {specs}")
        print()


def search_by_state(state):
    """Search providers by state."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT name, specialties, city, state 
        FROM providers 
        WHERE source = 'healthgrades' AND state = ?
        ORDER BY name
    """, (state.upper(),))
    rows = cursor.fetchall()
    conn.close()
    
    print(f"\nFound {len(rows)} providers in {state.upper()}:\n")
    for row in rows:
        name, specs, city, state = row
        print(f"  {name} - {city}, {state}")


def export_to_csv(output_file):
    """Export all providers to CSV."""
    import csv
    
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT name, specialties, street, city, state, 
               zip, phone, source, scraped_at
        FROM providers 
        WHERE source = 'healthgrades'
        ORDER BY name
    """)
    rows = cursor.fetchall()
    conn.close()
    
    with open(output_file, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['Name', 'Specialties', 'Street', 'City', 'State', 'ZIP', 'Phone', 'Source', 'Created'])
        writer.writerows(rows)
    
    print(f"\nExported {len(rows)} providers to {output_file}")


def show_stats():
    """Show database statistics."""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Total by source
    cursor.execute("SELECT source, COUNT(*) FROM providers GROUP BY source")
    by_source = cursor.fetchall()
    
    # States
    cursor.execute("""
        SELECT state, COUNT(*) as count 
        FROM providers 
        WHERE source = 'healthgrades' AND state IS NOT NULL
        GROUP BY state 
        ORDER BY count DESC
    """)
    by_state = cursor.fetchall()
    
    conn.close()
    
    print("\n=== DATABASE STATISTICS ===\n")
    print("By Source:")
    for source, count in by_source:
        print(f"  {source}: {count}")
    
    print("\nBy State (Healthgrades):")
    for state, count in by_state[:10]:
        print(f"  {state}: {count}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python query_db.py list              - List all providers")
        print("  python query_db.py search <name>     - Search by name")
        print("  python query_db.py state <state>     - Filter by state (e.g., CA)")
        print("  python query_db.py export <file>     - Export to CSV")
        print("  python query_db.py stats             - Show statistics")
        sys.exit(1)
    
    cmd = sys.argv[1]
    
    if cmd == "list":
        list_all()
    elif cmd == "search":
        if len(sys.argv) < 3:
            print("Usage: python query_db.py search <name>")
            sys.exit(1)
        search_by_name(sys.argv[2])
    elif cmd == "state":
        if len(sys.argv) < 3:
            print("Usage: python query_db.py state <state_code>")
            sys.exit(1)
        search_by_state(sys.argv[2])
    elif cmd == "export":
        if len(sys.argv) < 3:
            print("Usage: python query_db.py export <output.csv>")
            sys.exit(1)
        export_to_csv(sys.argv[2])
    elif cmd == "stats":
        show_stats()
    else:
        print(f"Unknown command: {cmd}")
