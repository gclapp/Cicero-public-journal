#!/usr/bin/env python3
"""
Spawn Vitus as a dedicated health coaching subagent.

Usage:
    python3 scripts/spawn_vitus.py [task_description]
    
Examples:
    python3 scripts/spawn_vitus.py "Analyze Geoff's HRV trend"
    python3 scripts/spawn_vitus.py "Generate morning briefing"
    python3 scripts/spawn_vitus.py "Check weight loss progress"
"""

import subprocess
import sys
import os

VITUS_AGENT_DIR = "/home/ubuntu/.openclaw/agents/vitus"

def spawn_vitus(task: str):
    """Spawn Vitus as a subagent with the given task."""
    
    # Ensure Vitus agent directory exists
    os.makedirs(VITUS_AGENT_DIR, exist_ok=True)
    
    # Build the spawn command
    cmd = [
        "openclaw", "sessions", "spawn",
        "--agent-id", "vitus",
        "--task", task,
        "--label", "vitus-health-coach",
        "--runtime", "subagent"
    ]
    
    print(f"🫀 Spawning Vitus with task: {task}")
    print(f"Command: {' '.join(cmd)}")
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode == 0:
        print("✅ Vitus spawned successfully")
        print(result.stdout)
    else:
        print("❌ Failed to spawn Vitus")
        print(result.stderr)
        return 1
    
    return 0

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 scripts/spawn_vitus.py [task_description]")
        print("\nExamples:")
        print('  python3 scripts/spawn_vitus.py "Analyze HRV trend"')
        print('  python3 scripts/spawn_vitus.py "Generate morning briefing"')
        sys.exit(1)
    
    task = " ".join(sys.argv[1:])
    sys.exit(spawn_vitus(task))
