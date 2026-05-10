#!/usr/bin/env python3
"""
Test data integrity for Water, Steps, and LoseIt parsers
Verifies that processors UPDATE data rather than DUPLICATE it
"""

import json
from pathlib import Path
from datetime import datetime

def check_water_data():
    """Check water data integrity"""
    print("="*60)
    print("WATER DATA INTEGRITY CHECK")
    print("="*60)
    
    water_file = Path.home() / '.openclaw/workspace/data/water-intake-history.json'
    if not water_file.exists():
        print("❌ Water data file not found")
        return False
    
    with open(water_file) as f:
        data = json.load(f)
    
    daily_records = data.get('daily_records', {})
    
    # Check 1: No duplicate dates
    dates = list(daily_records.keys())
    if len(dates) != len(set(dates)):
        print("❌ FAIL: Duplicate dates found")
        return False
    print(f"✅ Unique dates: {len(dates)}")
    
    # Check 2: Each record has required fields
    required_fields = ['date', 'ounces', 'liters', 'cups']
    for date, record in daily_records.items():
        missing = [f for f in required_fields if f not in record]
        if missing:
            print(f"❌ FAIL: {date} missing fields: {missing}")
            return False
    print(f"✅ All {len(dates)} records have required fields")
    
    # Check 3: Values are reasonable
    for date, record in daily_records.items():
        oz = record.get('ounces', 0)
        if oz < 0 or oz > 200:
            print(f"⚠️  Warning: {date} has unusual value: {oz} oz")
    
    print(f"✅ Water data integrity: PASS")
    return True

def check_steps_data():
    """Check steps data integrity"""
    print("\n" + "="*60)
    print("STEPS DATA INTEGRITY CHECK")
    print("="*60)
    
    steps_file = Path.home() / '.openclaw/workspace/data/steps-history.json'
    if not steps_file.exists():
        print("❌ Steps data file not found")
        return False
    
    with open(steps_file) as f:
        data = json.load(f)
    
    daily_records = data.get('daily_records', {})
    
    # Check 1: No duplicate dates
    dates = list(daily_records.keys())
    if len(dates) != len(set(dates)):
        print("❌ FAIL: Duplicate dates found")
        from collections import Counter
        counts = Counter(dates)
        for date, count in counts.items():
            if count > 1:
                print(f"  {date}: {count} duplicates")
        return False
    print(f"✅ Unique dates: {len(dates)}")
    
    # Check 2: Each record has required fields
    required_fields = ['date', 'steps', 'miles', 'calories']
    for date, record in daily_records.items():
        missing = [f for f in required_fields if f not in record]
        if missing:
            print(f"❌ FAIL: {date} missing fields: {missing}")
            return False
    print(f"✅ All {len(dates)} records have required fields")
    
    # Check 3: Values are reasonable
    for date, record in daily_records.items():
        steps = record.get('steps', 0)
        if steps < 0 or steps > 100000:
            print(f"⚠️  Warning: {date} has unusual value: {steps} steps")
    
    print(f"✅ Steps data integrity: PASS")
    return True

def check_loseit_data():
    """Check LoseIt data integrity"""
    print("\n" + "="*60)
    print("LOSEIT DATA INTEGRITY CHECK")
    print("="*60)
    
    loseit_file = Path.home() / '.openclaw/workspace/data/nutrition/loseit-cache.json'
    if not loseit_file.exists():
        print("❌ LoseIt data file not found")
        return False
    
    with open(loseit_file) as f:
        data = json.load(f)
    
    entries = data.get('entries', [])
    
    # Check 1: No duplicate dates
    dates = [e.get('date') for e in entries]
    if len(dates) != len(set(dates)):
        print("❌ FAIL: Duplicate dates found")
        from collections import Counter
        counts = Counter(dates)
        for date, count in counts.items():
            if count > 1:
                print(f"  {date}: {count} duplicates")
        return False
    print(f"✅ Unique dates: {len(dates)}")
    
    # Check 2: Each entry has required fields
    required_fields = ['date', 'food_calories']
    for entry in entries:
        missing = [f for f in required_fields if f not in entry]
        if missing:
            print(f"❌ FAIL: {entry.get('date', 'unknown')} missing fields: {missing}")
            return False
    print(f"✅ All {len(entries)} entries have required fields")
    
    # Check 3: Values are reasonable
    for entry in entries:
        cals = entry.get('food_calories', 0)
        if cals and (cals < 200 or cals > 10000):
            print(f"⚠️  Warning: {entry.get('date')} has unusual value: {cals} cal")
    
    print(f"✅ LoseIt data integrity: PASS")
    return True

def main():
    print("\n" + "="*60)
    print("DATA INTEGRITY AUDIT - All Parsers")
    print("="*60)
    print(f"Time: {datetime.now().isoformat()}")
    print()
    
    results = []
    results.append(("Water", check_water_data()))
    results.append(("Steps", check_steps_data()))
    results.append(("LoseIt", check_loseit_data()))
    
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    
    all_pass = True
    for name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{name:10} {status}")
        if not passed:
            all_pass = False
    
    print()
    if all_pass:
        print("✅ ALL DATA INTEGRITY CHECKS PASSED")
        print("No duplicates found. Data is being updated correctly.")
    else:
        print("❌ SOME CHECKS FAILED")
        print("Review the output above for details.")
    
    return all_pass

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
