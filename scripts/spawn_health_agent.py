#!/usr/bin/env python3
"""
Spawn Vitus - The Health & Performance Subagent
Called by Cicero when health-specific expertise is needed
"""

import subprocess
import sys
from pathlib import Path

def spawn_vitus(task_description="General health monitoring"):
    """Spawn Vitus health agent with specific task"""
    
    workspace = Path.home() / '.openclaw' / 'workspace'
    agent_dir = workspace / 'agents' / 'health-agent'
    
    # Build the task for Vitus
    vitus_task = f"""You are Vitus, Geoff's dedicated Health & Performance Agent.

Read your SOUL.md at {agent_dir}/SOUL.md to understand your identity and role.

YOUR CURRENT TASK:
{task_description}

Use the health_monitor.py module for data fetching and analysis:
  python3 {agent_dir}/health_monitor.py

Focus exclusively on health, recovery, fitness, and wellness topics.
Defer all non-health questions back to Cicero.

Report back with:
1. What you analyzed
2. Key findings
3. Specific recommendations for Geoff
4. Any alerts or concerns
"""
    
    # Use sessions_spawn via OpenClaw CLI
    result = subprocess.run([
        'openclaw', 'sessions', 'spawn',
        '--agent-id', 'vitus-health',
        '--task', vitus_task,
        '--label', f'vitus-health-{task_description[:30]}',
        '--mode', 'run'
    ], capture_output=True, text=True)
    
    if result.returncode == 0:
        print(f"✅ Vitus spawned successfully for: {task_description}")
        return True
    else:
        print(f"❌ Failed to spawn Vitus: {result.stderr}")
        return False

if __name__ == '__main__':
    task = sys.argv[1] if len(sys.argv) > 1 else "General health check"
    spawn_vitus(task)
