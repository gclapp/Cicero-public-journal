#!/usr/bin/env python3
"""
fetch_todoist_tasks.py - Fetch and categorize Todoist tasks using actual project structure
FIXED: Better filtering to show today's tasks and upcoming priorities
"""

import subprocess
import json
from pathlib import Path
from datetime import datetime, timedelta

def run_todoist_command(args):
    """Run todoist CLI command and return JSON output"""
    try:
        # Add --json flag for JSON output
        if '--json' not in args:
            args = args + ['--json']
        
        # Use full path to todoist to ensure it works in cron jobs
        todoist_path = '/home/ubuntu/.npm-global/bin/todoist'
        
        result = subprocess.run(
            [todoist_path] + args,
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

def is_relevant_task(task):
    """
    Check if task is relevant for today's check-in:
    - P1 priority (highest)
    - P2 priority (high)
    - Due today
    - Due within next 3 days
    - Overdue (but we'll flag these separately)
    """
    priority = task.get('priority', 4)
    
    # P1 or P2 are always relevant
    if priority <= 2:
        return True
    
    # Check due date
    due = task.get('due')
    if due:
        due_date = due.get('date', '')
        if due_date:
            today = datetime.now().strftime('%Y-%m-%d')
            
            # Due today
            if due_date == today:
                return True
            
            # Due within next 3 days
            try:
                due_dt = datetime.strptime(due_date, '%Y-%m-%d')
                today_dt = datetime.now()
                days_diff = (due_dt - today_dt).days
                if 0 <= days_diff <= 3:
                    return True
            except:
                pass
    
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

def get_due_date_label(task):
    """Get a friendly label for due date"""
    due = task.get('due')
    if not due:
        return ""
    
    due_date = due.get('date', '')
    if not due_date:
        return ""
    
    today = datetime.now().strftime('%Y-%m-%d')
    tomorrow = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
    
    if due_date == today:
        return " 📅 Today"
    elif due_date == tomorrow:
        return " 📅 Tomorrow"
    else:
        try:
            due_dt = datetime.strptime(due_date, '%Y-%m-%d')
            return f" 📅 {due_dt.strftime('%b %d')}"
        except:
            return f" 📅 {due_date}"

def get_todoist_summary():
    """Get formatted todoist summary using actual project structure"""
    
    # Get project mapping
    project_map, work_ids, personal_ids = get_project_mapping()
    
    # Get all tasks
    all_tasks = run_todoist_command(['tasks'])
    
    if not all_tasks:
        return "📋 **Tasks:** Unable to fetch tasks (check Todoist connection)\n"
    
    # Separate into categories
    relevant_tasks = []
    overdue_tasks = []
    
    for task in all_tasks:
        if is_overdue(task):
            overdue_tasks.append(task)
        elif is_relevant_task(task):
            relevant_tasks.append(task)
    
    # Categorize by actual project
    work_tasks = []
    personal_tasks = []
    
    for task in relevant_tasks:
        project_id = task.get('projectId')
        
        if project_id in work_ids:
            work_tasks.append(task)
        elif project_id in personal_ids:
            personal_tasks.append(task)
        else:
            # Default to personal if unknown
            personal_tasks.append(task)
    
    # Sort tasks: P1 first, then P2, then by due date, then by project name
    def task_sort_key(task):
        priority = task.get('priority', 4)
        due = task.get('due', {})
        due_date = due.get('date', '9999-12-31') if due else '9999-12-31'
        project_name = project_map.get(task.get('projectId'), 'Unknown')
        return (priority, due_date, project_name.lower())
    
    work_tasks.sort(key=task_sort_key)
    personal_tasks.sort(key=task_sort_key)
    
    total = len(work_tasks) + len(personal_tasks)
    
    if total == 0 and not overdue_tasks:
        return "📋 **Tasks:** No urgent tasks for today! 🎉\n"
    
    summary = f"📋 **Today's Focus ({total} tasks)**\n\n"
    
    # Overdue tasks section (if any)
    if overdue_tasks:
        summary += f"⚠️ **Overdue ({len(overdue_tasks)})**\n"
        for task in overdue_tasks[:5]:
            content = task.get('content', '')[:50]
            summary += f"  • {content}...\n"
        if len(overdue_tasks) > 5:
            summary += f"  ... and {len(overdue_tasks) - 5} more overdue\n"
        summary += "\n"
    
    # Work tasks grouped by project
    if work_tasks:
        summary += f"💼 **Work** ({len(work_tasks)})\n"
        
        # Group by project
        current_project = None
        for task in work_tasks[:20]:  # Top 20 work tasks
            project_id = task.get('projectId')
            project_name = project_map.get(project_id, 'Unknown')
            
            # Show project name when it changes
            if project_name != current_project:
                summary += f"  📁 {project_name}\n"
                current_project = project_name
            
            content = task.get('content', '')[:55]
            priority_marker = "🔴 " if task.get('priority') == 1 else "🟠 " if task.get('priority') == 2 else "  "
            due_label = get_due_date_label(task)
            summary += f"    {priority_marker}• {content}{due_label}\n"
        
        if len(work_tasks) > 20:
            summary += f"    ... and {len(work_tasks) - 20} more\n"
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
            priority_marker = "🔴 " if task.get('priority') == 1 else "🟠 " if task.get('priority') == 2 else "  "
            due_label = get_due_date_label(task)
            summary += f"    {priority_marker}• {content}{due_label}\n"
        
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
    
    if not all_tasks:
        return "<h3>📋 Today's Tasks</h3><p>Unable to fetch tasks (check Todoist connection)</p>"
    
    # Separate into categories
    relevant_tasks = []
    overdue_tasks = []
    
    for task in all_tasks:
        if is_overdue(task):
            overdue_tasks.append(task)
        elif is_relevant_task(task):
            relevant_tasks.append(task)
    
    # Categorize
    work_tasks = []
    personal_tasks = []
    
    for task in relevant_tasks:
        project_id = task.get('projectId')
        
        if project_id in work_ids:
            work_tasks.append(task)
        elif project_id in personal_ids:
            personal_tasks.append(task)
        else:
            personal_tasks.append(task)
    
    # Sort tasks
    def task_sort_key(task):
        priority = task.get('priority', 4)
        due = task.get('due', {})
        due_date = due.get('date', '9999-12-31') if due else '9999-12-31'
        project_name = project_map.get(task.get('projectId'), 'Unknown')
        return (priority, due_date, project_name.lower())
    
    work_tasks.sort(key=task_sort_key)
    personal_tasks.sort(key=task_sort_key)
    
    total = len(work_tasks) + len(personal_tasks)
    
    if total == 0 and not overdue_tasks:
        return "<h3>📋 Today's Tasks</h3><p>No urgent tasks for today! 🎉</p>"
    
    html = f"<h3>📋 Today's Focus ({total} tasks)</h3>"
    
    # Overdue tasks
    if overdue_tasks:
        html += f"<h4 style='color: #dc3545; margin-top: 15px; margin-bottom: 8px; font-size: 15px;'>⚠️ Overdue ({len(overdue_tasks)})</h4>"
        for task in overdue_tasks[:5]:
            content = task.get('content', '')[:60]
            html += f"<div style='margin: 3px 0; margin-left: 15px; font-size: 14px; color: #dc3545;'>• {content}</div>"
        if len(overdue_tasks) > 5:
            html += f"<div style='color: #666; font-style: italic; margin-left: 15px;'>... and {len(overdue_tasks) - 5} more overdue</div>"
    
    # Work tasks
    if work_tasks:
        html += f"<h4 style='color: #007bff; margin-top: 15px; margin-bottom: 8px; font-size: 15px;'>💼 Work ({len(work_tasks)})</h4>"
        
        current_project = None
        for task in work_tasks[:20]:
            project_id = task.get('projectId')
            project_name = project_map.get(project_id, 'Unknown')
            
            if project_name != current_project:
                html += f"<div style='font-weight: bold; color: #666; margin-top: 10px; margin-bottom: 5px; font-size: 13px;'>📁 {project_name}</div>"
                current_project = project_name
            
            content = task.get('content', '')[:65]
            priority = task.get('priority', 4)
            due = task.get('due', {})
            due_date = due.get('date', '') if due else ''
            
            priority_style = "color: #dc3545; font-weight: bold;" if priority == 1 else "color: #fd7e14;" if priority == 2 else ""
            due_badge = f" <span style='background: #e9ecef; padding: 2px 6px; border-radius: 4px; font-size: 11px; color: #666;'>Due {due_date}</span>" if due_date and due_date != datetime.now().strftime('%Y-%m-%d') else ""
            
            html += f"<div style='margin: 3px 0; margin-left: 15px; font-size: 14px; {priority_style}'>• {content}{due_badge}</div>"
        
        if len(work_tasks) > 20:
            html += f"<div style='color: #666; font-style: italic; margin-left: 15px;'>... and {len(work_tasks) - 20} more</div>"
    
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
            priority = task.get('priority', 4)
            due = task.get('due', {})
            due_date = due.get('date', '') if due else ''
            
            priority_style = "color: #dc3545; font-weight: bold;" if priority == 1 else "color: #fd7e14;" if priority == 2 else ""
            due_badge = f" <span style='background: #e9ecef; padding: 2px 6px; border-radius: 4px; font-size: 11px; color: #666;'>Due {due_date}</span>" if due_date and due_date != datetime.now().strftime('%Y-%m-%d') else ""
            
            html += f"<div style='margin: 3px 0; margin-left: 15px; font-size: 14px; {priority_style}'>• {content}{due_badge}</div>"
        
        if len(personal_tasks) > 15:
            html += f"<div style='color: #666; font-style: italic; margin-left: 15px;'>... and {len(personal_tasks) - 15} more</div>"
    
    return html

def get_today_tomorrow_html():
    """Get HTML for tasks due today and tomorrow only, sorted by day then priority"""
    from datetime import datetime, timedelta
    
    # Get all tasks
    all_tasks = run_todoist_command(['tasks'])
    
    if not all_tasks:
        return "<h3>📋 Today's Priorities</h3><p>Unable to fetch tasks</p>"
    
    today_str = datetime.now().strftime('%Y-%m-%d')
    tomorrow_str = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
    
    # Filter for today and tomorrow only
    today_tasks = []
    tomorrow_tasks = []
    
    for task in all_tasks:
        due = task.get('due')
        if due:
            due_date = due.get('date', '')
            if due_date == today_str:
                today_tasks.append(task)
            elif due_date == tomorrow_str:
                tomorrow_tasks.append(task)
    
    # Sort by priority (lower number = higher priority)
    today_tasks.sort(key=lambda t: t.get('priority', 4))
    tomorrow_tasks.sort(key=lambda t: t.get('priority', 4))
    
    if not today_tasks and not tomorrow_tasks:
        return "<h3>📋 Today's Priorities</h3><p>No tasks due today or tomorrow! 🎉</p>"
    
    html = "<h3>📋 Today's Priorities</h3><div style='display: block; width: 100%;'>"
    
    # Today section
    if today_tasks:
        html += f"<h4 style='color: #dc3545; margin: 10px 0 5px 0;'>📅 Today ({len(today_tasks)})</h4>"
        for task in today_tasks:
            task_id = task.get('id', '')
            content = task.get('content', '')
            priority = task.get('priority', 4)
            
            # Priority colors
            if priority == 1:
                color = "#dc3545"  # Red
                weight = "font-weight: bold;"
            elif priority == 2:
                color = "#fd7e14"  # Orange
                weight = ""
            elif priority == 3:
                color = "#ffc107"  # Yellow
                weight = ""
            else:
                color = "#333"  # Default
                weight = ""
            
            task_url = f"https://app.todoist.com/app/task/{task_id}"
            html += f"<div style='display: block; margin: 4px 0; margin-left: 15px; font-size: 14px; line-height: 1.4;'><a href='{task_url}' style='color: {color}; {weight}text-decoration: underline;'>{content}</a></div>"
    
    # Tomorrow section
    if tomorrow_tasks:
        html += f"<h4 style='color: #007bff; margin: 15px 0 5px 0;'>📅 Tomorrow ({len(tomorrow_tasks)})</h4>"
        for task in tomorrow_tasks:
            task_id = task.get('id', '')
            content = task.get('content', '')
            priority = task.get('priority', 4)
            
            if priority == 1:
                color = "#dc3545"
                weight = "font-weight: bold;"
            elif priority == 2:
                color = "#fd7e14"
                weight = ""
            elif priority == 3:
                color = "#ffc107"
                weight = ""
            else:
                color = "#333"
                weight = ""
            
            task_url = f"https://app.todoist.com/app/task/{task_id}"
            html += f"<div style='display: block; margin: 4px 0; margin-left: 15px; font-size: 14px; line-height: 1.4;'><a href='{task_url}' style='color: {color}; {weight}text-decoration: underline;'>{content}</a></div>"
    
    html += "</div>"
    return html

if __name__ == "__main__":
    print("Fetching Todoist tasks by actual project...")
    print("\n" + get_todoist_summary())
    print("\nHTML version (first 1000 chars):")
    print(get_todoist_html()[:1000] + "...")
    print("\n\nToday/Tomorrow version:")
    print(get_today_tomorrow_html())
