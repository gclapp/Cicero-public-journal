#!/usr/bin/env python3
"""
fetch_todoist_tasks.py - Fetch and categorize Todoist tasks using actual project structure
FIXED: Better filtering to show today's tasks and upcoming priorities
"""

import subprocess
import json
import html
from datetime import datetime, timedelta

PGNY_PROJECT_ID = '6CrfqHJrvp7PW7P3'
PERSONAL_PROJECT_ID = '6CrfqHJrvJ3jFqHf'
MAX_FOCUS_TASKS = 25

# Todoist's API uses 4 for P1, 3 for P2, 2 for P3, and 1 for P4.
TODOIST_P1 = 4
TODOIST_P2 = 3

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
    children_by_parent = {}
    
    for project in projects:
        pid = project['id']
        name = project['name']
        parent_id = project.get('parentId')
        
        mapping[pid] = name
        if parent_id:
            children_by_parent.setdefault(parent_id, []).append(pid)

    def descendants(root_id):
        found = set()
        stack = [root_id]
        while stack:
            pid = stack.pop()
            if pid in found:
                continue
            found.add(pid)
            stack.extend(children_by_parent.get(pid, []))
        return found

    pgny_project_ids = descendants(PGNY_PROJECT_ID)
    personal_root_ids = descendants(PERSONAL_PROJECT_ID)
    work_project_ids.update(pgny_project_ids)
    personal_project_ids.update(personal_root_ids)
    
    for project in projects:
        pid = project['id']
        name = project['name']
        
        if pid in work_project_ids or pid in personal_project_ids:
            continue
        if 'openclaw' in name.lower() or 'from cicero' in name.lower():
            work_project_ids.add(pid)
        else:
            personal_project_ids.add(pid)
    
    return mapping, work_project_ids, personal_project_ids

def get_pgny_project_ids(project_map):
    """Return PGNY and all nested PGNY sub-project IDs."""
    projects = run_todoist_command(['projects'])
    children_by_parent = {}
    project_ids = set(project_map.keys())

    for project in projects:
        parent_id = project.get('parentId')
        if parent_id:
            children_by_parent.setdefault(parent_id, []).append(project['id'])

    found = set()
    stack = [PGNY_PROJECT_ID] if PGNY_PROJECT_ID in project_ids else []
    while stack:
        pid = stack.pop()
        if pid in found:
            continue
        found.add(pid)
        stack.extend(children_by_parent.get(pid, []))
    return found

def is_relevant_task(task):
    """
    Check if task is relevant for today's check-in:
    - P1 priority (highest)
    - P2 priority (high)
    - Due today
    - Due within next 3 days
    - Overdue (but we'll flag these separately)
    """
    priority = task.get('priority', 1)
    
    # P1 or P2 are always relevant
    if priority >= TODOIST_P2:
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

def get_priority_label(task):
    priority = task.get('priority', 1)
    if priority == TODOIST_P1:
        return "P1"
    if priority == TODOIST_P2:
        return "P2"
    return f"P{5 - priority}"

def get_priority_marker(task):
    priority = task.get('priority', 1)
    if priority == TODOIST_P1:
        return "🔴 "
    if priority == TODOIST_P2:
        return "🟠 "
    return "  "

def priority_style(task):
    priority = task.get('priority', 1)
    if priority == TODOIST_P1:
        return "color: #dc3545; font-weight: bold;"
    if priority == TODOIST_P2:
        return "color: #fd7e14;"
    return ""

def get_focus_task_selection(limit=MAX_FOCUS_TASKS):
    """Select Todoist check-in tasks: P1s first, PGNY P1s guaranteed, P2s only as filler."""
    project_map, work_ids, personal_ids = get_project_mapping()
    pgny_ids = get_pgny_project_ids(project_map)
    all_tasks = run_todoist_command(['tasks'])

    if not all_tasks:
        return {
            'tasks': [],
            'project_map': project_map,
            'work_ids': work_ids,
            'personal_ids': personal_ids,
            'pgny_ids': pgny_ids,
            'counts': {},
            'fetch_failed': True,
        }

    def task_sort_key(task):
        project_id = task.get('projectId')
        due = task.get('due', {})
        due_date = due.get('date', '9999-12-31') if due else '9999-12-31'
        is_pgny = project_id in pgny_ids
        project_name = project_map.get(project_id, 'Unknown')
        return (
            0 if is_pgny else 1,
            due_date,
            project_name.lower(),
            task.get('content', '').lower(),
        )

    p1_tasks = [task for task in all_tasks if task.get('priority') == TODOIST_P1]
    p2_tasks = [task for task in all_tasks if task.get('priority') == TODOIST_P2]
    pgny_p1 = [task for task in p1_tasks if task.get('projectId') in pgny_ids]
    other_p1 = [task for task in p1_tasks if task.get('projectId') not in pgny_ids]

    pgny_p1.sort(key=task_sort_key)
    other_p1.sort(key=task_sort_key)
    p2_tasks.sort(key=task_sort_key)

    selected = pgny_p1[:]
    if len(selected) < limit:
        selected.extend(other_p1[:limit - len(selected)])
    if len(selected) < limit:
        selected.extend(p2_tasks[:limit - len(selected)])

    counts = {
        'selected': len(selected),
        'limit': limit,
        'p1_total': len(p1_tasks),
        'p2_total': len(p2_tasks),
        'pgny_p1_total': len(pgny_p1),
        'p2_included': sum(1 for task in selected if task.get('priority') == TODOIST_P2),
        'limit_exceeded_for_pgny_p1': len(pgny_p1) > limit,
    }

    return {
        'tasks': selected,
        'project_map': project_map,
        'work_ids': work_ids,
        'personal_ids': personal_ids,
        'pgny_ids': pgny_ids,
        'counts': counts,
        'fetch_failed': False,
    }

def group_tasks_by_bucket(tasks, project_map, work_ids):
    buckets = []
    grouped = {}
    for task in tasks:
        project_id = task.get('projectId')
        bucket = 'Work' if project_id in work_ids else 'Personal'
        project_name = project_map.get(project_id, 'Unknown')
        key = (bucket, project_name)
        grouped.setdefault(key, []).append(task)

    for bucket in ('Work', 'Personal'):
        for (group_bucket, project_name), project_tasks in grouped.items():
            if group_bucket == bucket:
                buckets.append((bucket, project_name, project_tasks))
    return buckets

def get_todoist_summary():
    """Get formatted todoist summary using actual project structure"""

    selection = get_focus_task_selection()
    if selection['fetch_failed']:
        return "📋 **Tasks:** Unable to fetch tasks (check Todoist connection)\n"

    tasks = selection['tasks']
    counts = selection['counts']
    if not tasks:
        return "📋 **Tasks:** No P1/P2 priorities right now.\n"

    summary = (
        f"📋 **Todoist Priorities ({counts['selected']}/{counts['limit']} shown)**\n"
        f"P1: {counts['p1_total']} total, {counts['pgny_p1_total']} PGNY | "
        f"P2 filler shown: {counts['p2_included']}\n\n"
    )

    for bucket, project_name, project_tasks in group_tasks_by_bucket(
        tasks,
        selection['project_map'],
        selection['work_ids'],
    ):
        bucket_icon = "💼" if bucket == "Work" else "🏠"
        summary += f"{bucket_icon} **{project_name}** ({len(project_tasks)})\n"
        for task in project_tasks:
            content = task.get('content', '')[:65]
            priority_marker = get_priority_marker(task)
            priority_label = get_priority_label(task)
            due_label = get_due_date_label(task)
            summary += f"  {priority_marker}{priority_label} • {content}{due_label}\n"
        summary += "\n"

    return summary

def get_todoist_html():
    """Get HTML formatted todoist section using actual project structure"""

    selection = get_focus_task_selection()
    if selection['fetch_failed']:
        return "<h3>📋 Today's Tasks</h3><p>Unable to fetch tasks (check Todoist connection)</p>"

    tasks = selection['tasks']
    counts = selection['counts']
    if not tasks:
        return "<h3>📋 Todoist Priorities</h3><p>No P1/P2 priorities right now.</p>"

    html_out = (
        f"<h3>📋 Todoist Priorities ({counts['selected']}/{counts['limit']} shown)</h3>"
        f"<p style='margin: 4px 0 10px 0; color: #666; font-size: 13px;'>"
        f"P1: {counts['p1_total']} total, {counts['pgny_p1_total']} PGNY. "
        f"P2 filler shown: {counts['p2_included']}.</p>"
    )

    for bucket, project_name, project_tasks in group_tasks_by_bucket(
        tasks,
        selection['project_map'],
        selection['work_ids'],
    ):
        heading_color = "#007bff" if bucket == "Work" else "#fd7e14"
        html_out += (
            f"<h4 style='color: {heading_color}; margin-top: 15px; margin-bottom: 8px; "
            f"font-size: 15px;'>{html.escape(project_name)} ({len(project_tasks)})</h4>"
        )
        for task in project_tasks:
            content = html.escape(task.get('content', '')[:80])
            task_id = task.get('id', '')
            task_url = f"https://app.todoist.com/app/task/{task_id}"
            due_label = html.escape(get_due_date_label(task).strip())
            due_badge = (
                f" <span style='background: #e9ecef; padding: 2px 6px; border-radius: 4px; "
                f"font-size: 11px; color: #666;'>{due_label}</span>"
                if due_label else ""
            )
            html_out += (
                f"<div style='margin: 4px 0; margin-left: 15px; font-size: 14px; "
                f"line-height: 1.4; {priority_style(task)}'>"
                f"<a href='{task_url}' style='{priority_style(task)} text-decoration: underline;'>"
                f"{get_priority_label(task)} • {content}</a>{due_badge}</div>"
            )

    return html_out

def get_today_tomorrow_html():
    """Compatibility wrapper used by check-in emails; now uses the shared 25-item priority selector."""
    return get_todoist_html()

if __name__ == "__main__":
    print("Fetching Todoist tasks by actual project...")
    print("\n" + get_todoist_summary())
    print("\nHTML version (first 1000 chars):")
    print(get_todoist_html()[:1000] + "...")
    print("\n\nToday/Tomorrow version:")
    print(get_today_tomorrow_html())
