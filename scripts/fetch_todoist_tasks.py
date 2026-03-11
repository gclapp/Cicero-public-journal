#!/usr/bin/env python3
"""
fetch_todoist_tasks.py - Fetch and categorize Todoist tasks using actual project structure
"""

import subprocess
import json
from pathlib import Path
from datetime import datetime

def run_todoist_command(args):
    """Run todoist CLI command and return JSON output"""
    try:
        # Add --json flag for JSON output
        if '--json' not in args:
            args = args + ['--json']
        
        result = subprocess.run(
            ['todoist'] + args,
            capture_output=True,
            text=True,
            timeout=30
        )
        if result.returncode == 0:
            return json.loads(result.stdout)
        return []
    except Exception as e:
        print(f"Error running todoist: {e}")
        return []

def get_project_mapping():
    """Get mapping of project IDs to project names and categories"""
    projects = run_todoist_command(['projects'])
    
    mapping = {}
    work_project_ids = set()
    personal_project_ids = set()
    
    # Define work project IDs (PGNY and all sub-projects)
    work_root = '6CrfqHJrvp7PW7P3'  # PGNY
    
    for project in projects:
        pid = project['id']
        name = project['name']
        parent_id = project.get('parentId')
        
        mapping[pid] = name
        
        # Categorize as work if it's PGNY or has PGNY as parent
        if pid == work_root or parent_id == work_root:
            work_project_ids.add(pid)
        # Categorize as personal if it's Personal or has Personal as parent
        elif parent_id == '6CrfqHJrvJ3jFqHf' or pid == '6CrfqHJrvJ3jFqHf':
            personal_project_ids.add(pid)
        # OpenClaw projects are work
        elif 'openclaw' in name.lower() or 'from cicero' in name.lower():
            work_project_ids.add(pid)
        # Everything else defaults to personal
        else:
            personal_project_ids.add(pid)
    
    return mapping, work_project_ids, personal_project_ids

def is_due_today_or_p1(task):
    """Check if task is due today or is P1 priority"""
    # Check priority (1 is highest in Todoist)
    if task.get('priority') == 1:
        return True
    
    # Check due date
    due = task.get('due')
    if due:
        due_date = due.get('date', '')
        today = datetime.now().strftime('%Y-%m-%d')
        if due_date == today:
            return True
    
    return False

def is_overdue(task):
    """Check if task is overdue"""
    due = task.get('due')
    if due:
        due_date = due.get('date', '')
        if due_date:
            today = datetime.now().strftime('%Y-%m-%d')
            return due_date < today
    return False

def get_todoist_summary():
    """Get formatted todoist summary using actual project structure"""
    
    # Get project mapping
    project_map, work_ids, personal_ids = get_project_mapping()
    
    # Get all tasks
    all_tasks = run_todoist_command(['tasks'])
    
    # Filter to P1 or due today, exclude overdue
    filtered_tasks = []
    for task in all_tasks:
        if is_due_today_or_p1(task) and not is_overdue(task):
            filtered_tasks.append(task)
    
    # Categorize by actual project
    work_tasks = []
    personal_tasks = []
    
    for task in filtered_tasks:
        project_id = task.get('projectId')
        
        if project_id in work_ids:
            work_tasks.append(task)
        elif project_id in personal_ids:
            personal_tasks.append(task)
        else:
            # Default to personal if unknown
            personal_tasks.append(task)
    
    # Sort work tasks: P1 first, then by project name, then by content
    def work_sort_key(task):
        is_p1 = task.get('priority') == 1
        project_name = project_map.get(task.get('projectId'), 'Unknown')
        return (0 if is_p1 else 1, project_name.lower(), task.get('content', '').lower())
    
    work_tasks.sort(key=work_sort_key)
    
    # Build summary
    total = len(work_tasks) + len(personal_tasks)
    
    if total == 0:
        return "📋 **Tasks:** No P1 or due-today tasks\n"
    
    summary = f"📋 **Today's Tasks ({total} total)**\n\n"
    
    # Work tasks grouped by project
    if work_tasks:
        summary += f"💼 **Work** ({len(work_tasks)})\n"
        
        # Group by project
        current_project = None
        for task in work_tasks[:15]:  # Top 15 work tasks
            project_id = task.get('projectId')
            project_name = project_map.get(project_id, 'Unknown')
            
            # Show project name when it changes
            if project_name != current_project:
                summary += f"  📁 {project_name}\n"
                current_project = project_name
            
            content = task.get('content', '')[:55]
            priority_marker = "🔴 " if task.get('priority') == 1 else "  "
            summary += f"    {priority_marker}• {content}\n"
        
        if len(work_tasks) > 15:
            summary += f"    ... and {len(work_tasks) - 15} more\n"
        summary += "\n"
    
    # Personal tasks grouped by project
    if personal_tasks:
        summary += f"🏠 **Personal** ({len(personal_tasks)})\n"
        
        # Group by project
        current_project = None
        for task in personal_tasks[:15]:  # Top 15 personal tasks
            project_id = task.get('projectId')
            project_name = project_map.get(project_id, 'Unknown')
            
            # Show project name when it changes
            if project_name != current_project:
                summary += f"  📁 {project_name}\n"
                current_project = project_name
            
            content = task.get('content', '')[:55]
            priority_marker = "🔴 " if task.get('priority') == 1 else "  "
            summary += f"    {priority_marker}• {content}\n"
        
        if len(personal_tasks) > 15:
            summary += f"    ... and {len(personal_tasks) - 15} more\n"
        summary += "\n"
    
    return summary

def get_todoist_html():
    """Get HTML formatted todoist section using actual project structure"""
    
    # Get project mapping
    project_map, work_ids, personal_ids = get_project_mapping()
    
    # Get all tasks
    all_tasks = run_todoist_command(['tasks'])
    
    # Filter to P1 or due today, exclude overdue
    filtered_tasks = []
    for task in all_tasks:
        if is_due_today_or_p1(task) and not is_overdue(task):
            filtered_tasks.append(task)
    
    # Categorize
    work_tasks = []
    personal_tasks = []
    
    for task in filtered_tasks:
        project_id = task.get('projectId')
        
        if project_id in work_ids:
            work_tasks.append(task)
        elif project_id in personal_ids:
            personal_tasks.append(task)
        else:
            personal_tasks.append(task)
    
    # Sort work tasks
    def work_sort_key(task):
        is_p1 = task.get('priority') == 1
        project_name = project_map.get(task.get('projectId'), 'Unknown')
        return (0 if is_p1 else 1, project_name.lower(), task.get('content', '').lower())
    
    work_tasks.sort(key=work_sort_key)
    
    total = len(work_tasks) + len(personal_tasks)
    
    if total == 0:
        return "<h3>📋 Today's Tasks</h3><p>No P1 or due-today tasks</p>"
    
    html = f"<h3>📋 Today's Tasks ({total} total)</h3>"
    
    # Work tasks
    if work_tasks:
        html += f"<h4 style='color: #007bff; margin-top: 15px; margin-bottom: 8px; font-size: 15px;'>💼 Work ({len(work_tasks)})</h4>"
        
        current_project = None
        for task in work_tasks[:15]:
            project_id = task.get('projectId')
            project_name = project_map.get(project_id, 'Unknown')
            
            if project_name != current_project:
                html += f"<div style='font-weight: bold; color: #666; margin-top: 10px; margin-bottom: 5px; font-size: 13px;'>📁 {project_name}</div>"
                current_project = project_name
            
            content = task.get('content', '')[:65]
            priority_style = "color: #dc3545; font-weight: bold;" if task.get('priority') == 1 else ""
            html += f"<div style='margin: 3px 0; margin-left: 15px; font-size: 14px; {priority_style}'>• {content}</div>"
        
        if len(work_tasks) > 15:
            html += f"<div style='color: #666; font-style: italic; margin-left: 15px;'>... and {len(work_tasks) - 15} more</div>"
    
    # Personal tasks
    if personal_tasks:
        html += f"<h4 style='color: #fd7e14; margin-top: 15px; margin-bottom: 8px; font-size: 15px;'>🏠 Personal ({len(personal_tasks)})</h4>"
        
        current_project = None
        for task in personal_tasks[:15]:
            project_id = task.get('projectId')
            project_name = project_map.get(project_id, 'Unknown')
            
            if project_name != current_project:
                html += f"<div style='font-weight: bold; color: #666; margin-top: 10px; margin-bottom: 5px; font-size: 13px;'>📁 {project_name}</div>"
                current_project = project_name
            
            content = task.get('content', '')[:65]
            priority_style = "color: #dc3545; font-weight: bold;" if task.get('priority') == 1 else ""
            html += f"<div style='margin: 3px 0; margin-left: 15px; font-size: 14px; {priority_style}'>• {content}</div>"
        
        if len(personal_tasks) > 15:
            html += f"<div style='color: #666; font-style: italic; margin-left: 15px;'>... and {len(personal_tasks) - 15} more</div>"
    
    return html

if __name__ == "__main__":
    print("Fetching Todoist tasks by actual project...")
    print("\n" + get_todoist_summary())
    print("\nHTML version (first 800 chars):")
    print(get_todoist_html()[:800] + "...")
