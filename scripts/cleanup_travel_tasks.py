#!/usr/bin/env python3
"""
Clean up travel tasks - remove old flat tasks and recreate as subtasks
"""

import subprocess
from datetime import datetime

def list_travel_tasks():
    """List all travel-related tasks"""
    try:
        result = subprocess.run(["todoist", "list"], capture_output=True, text=True, timeout=30)
        if result.returncode != 0:
            return []
        
        travel_tasks = []
        for line in result.stdout.strip().split('\n'):
            if any(keyword in line.lower() for keyword in ['rover', 'pack', 'uber', 'hotel', 'flight', 'travel', 'greta', 'lax', 'jfk']):
                travel_tasks.append(line)
        return travel_tasks
    except Exception as e:
        print(f"❌ Error listing tasks: {e}")
        return []

def delete_task(task_id):
    """Delete a task by ID"""
    try:
        result = subprocess.run(["todoist", "delete", task_id], 
                              capture_output=True, text=True, timeout=30)
        return result.returncode == 0
    except Exception as e:
        print(f"❌ Error deleting task {task_id}: {e}")
        return False

def main():
    print("🧹 Travel Task Cleanup")
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print()
    
    # Find travel tasks
    print("🔍 Finding travel-related tasks...")
    travel_tasks = list_travel_tasks()
    
    if not travel_tasks:
        print("✅ No travel tasks found to clean up")
        return
    
    print(f"\n📝 Found {len(travel_tasks)} travel tasks:")
    for task in travel_tasks:
        print(f"   {task}")
    
    print("\n⚠️  This will DELETE all the above tasks and recreate them as subtasks.")
    print("   Run: python3 scripts/travel_automation_subtasks.py after cleanup")
    print()
    
    # Extract task IDs and delete
    deleted = 0
    for task in travel_tasks:
        parts = task.split()
        if parts:
            task_id = parts[0]
            task_name = ' '.join(parts[1:]) if len(parts) > 1 else task_id
            
            if delete_task(task_id):
                print(f"   ✅ Deleted: {task_name[:60]}...")
                deleted += 1
            else:
                print(f"   ❌ Failed to delete: {task_name[:60]}...")
    
    print()
    print(f"🗑️  Cleanup complete: {deleted} tasks deleted")
    print()
    print("Next steps:")
    print("   1. Run: python3 scripts/travel_automation_subtasks.py")
    print("   2. Tasks will be recreated as parent + subtasks")

if __name__ == "__main__":
    main()
