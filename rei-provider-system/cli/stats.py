#!/usr/bin/env python3
"""Show provider database statistics."""
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "data" / "providers.db"

def main():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Basic counts
    cursor.execute("SELECT COUNT(*) FROM providers")
    total = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM providers WHERE npi IS NOT NULL AND npi != ''")
    with_npi = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM providers WHERE phone IS NOT NULL AND phone != ''")
    with_phone = cursor.fetchone()[0]
    
    # By state
    cursor.execute("""
        SELECT state, COUNT(*) as count,
               SUM(CASE WHEN npi IS NOT NULL AND npi != '' THEN 1 ELSE 0 END) as with_npi
        FROM providers
        WHERE state IS NOT NULL AND state != ''
        GROUP BY state
        ORDER BY count DESC
        LIMIT 10
    """)
    by_state = cursor.fetchall()
    
    # Match methods
    cursor.execute("""
        SELECT npi_match_method, COUNT(*) 
        FROM providers 
        WHERE npi_match_method IS NOT NULL 
        GROUP BY npi_match_method
    """)
    methods = cursor.fetchall()
    
    conn.close()
    
    print("="*70)
    print("REI PROVIDER DATABASE STATISTICS")
    print("="*70)
    print()
    print(f"Total providers:     {total:,}")
    print(f"With NPI:            {with_npi:,} ({with_npi/total*100:.1f}%)")
    print(f"Without NPI:         {total-with_npi:,} ({(total-with_npi)/total*100:.1f}%)")
    print(f"With phone:          {with_phone:,}")
    print()
    print("Top 10 States:")
    for state, count, state_npi in by_state:
        pct = state_npi/count*100 if count > 0 else 0
        print(f"  {state}: {count:,} providers ({state_npi:,} with NPI, {pct:.1f}%)")
    print()
    print("Match Methods:")
    for method, count in methods:
        print(f"  {method}: {count:,}")
    print("="*70)

if __name__ == "__main__":
    main()
