#!/usr/bin/env python3
"""
Vitus Telegram Bridge — Routes @vitus mentions to Vitus subagent.

This script can be called by the main agent when a message starting with 
@vitus is received on Telegram.
"""

import subprocess
import sys
import json
import os
from pathlib import Path

VITUS_DIR = "/home/ubuntu/.openclaw/agents/vitus"
WORKSPACE_DIR = "/home/ubuntu/.openclaw/workspace"


def spawn_vitus_task(user_message: str, user_id: str = None) -> dict:
    """
    Spawn Vitus as a subagent to handle a health coaching request.
    
    Args:
        user_message: The message content (without @vitus prefix)
        user_id: Optional Telegram user ID for context
    
    Returns:
        Dict with status and response
    """
    
    # Clean up the message
    task = user_message.strip()
    
    # Build context for Vitus
    context = f"""You are Vitus, Geoff's dedicated health coach. 

A user has sent you this message via Telegram:
"{task}"

Respond as Vitus would — direct, coaching-focused, actionable. 
Use your health coaching expertise and access Whoop/Apple Health data as needed.

Keep responses concise (Telegram-friendly) but impactful."""
    
    # For now, we'll use a direct Python approach since subagent spawning
    # requires gateway configuration. In production, this would spawn
    # an isolated Vitus session.
    
    return {
        "status": "spawned",
        "task": task,
        "context": context,
        "note": "Vitus would process this and respond. In full implementation, this spawns a subagent."
    }


def generate_vitus_response(task: str) -> str:
    """
    Generate a Vitus-style response for common health queries.
    This is a placeholder — in production, Vitus subagent would generate this.
    """
    
    task_lower = task.lower()
    
    if "recovery" in task_lower:
        return """🫀 **Recovery Check**

Your latest recovery: **58%** — 🟡 YELLOW ZONE

**What this means:**
Your body is asking for moderation. HRV is down 8% from baseline — not critical, but a signal to be mindful.

**Today's Mission:**
✅ Light activity — 30-min walk or easy mobility
✅ Hydration target: 80oz (you are at 45oz)
✅ Bed by 10 PM — tomorrow's schedule is full

**Non-negotiable:** No high-intensity workout today. Save the hard push for when you're in the green.

Questions? Just ask!"""
    
    elif "sleep" in task_lower:
        return """🫀 **Sleep Analysis**

Last night: **6h 42m** — 🟡 BORDERLINE

**The data:**
- Sleep efficiency: 87% (good)
- Deep sleep: 1h 12m (solid)
- REM: 1h 45m (a bit low)
- Wake events: 3 (not bad)

**Tonight's target:** 7h 30m

**Sleep prep:**
🌙 No screens after 9:30 PM
🌙 Room temp: 67°F
🌙 Last water at 8 PM (small sips only after)

Your recovery will thank you tomorrow."""
    
    elif "weight" in task_lower:
        return """🫀 **Weight Update**

Current: **187.2 lbs**
Trend: **-0.8 lbs this week** ✅

**On track for:** 20 lbs in 10-12 weeks

**This week's focus:**
- Protein at every meal (target: 160g/day)
- Sleep 7+ hours (affects fat burning)
- Hydration 80oz+ daily

**Remember:** Daily fluctuations are normal. Watch the weekly trend, not daily noise.

Log your weight anytime by messaging me: Weight: 186.5"""
    
    elif "eat" in task_lower or "food" in task_lower or "meal" in task_lower or "lunch" in task_lower or "dinner" in task_lower:
        return """🫀 **Nutrition Guidance**

**Today's macro targets:**
- Calories: 1,850
- Protein: 160g (35%)
- Carbs: 185g (40%)
- Fat: 50g (25%)

**Smart choices right now:**
🥗 **Quick option:** Grilled chicken salad with olive oil
🍲 **Hearty option:** Salmon + quinoa + roasted vegetables
🥙 **On-the-go:** Turkey wrap (light on mayo) + apple

**Protein boosters:**
- Greek yogurt (20g protein)
- Hard-boiled eggs (12g each)
- Protein shake (25g)

What are you in the mood for?"""
    
    elif "water" in task_lower or "hydration" in task_lower:
        return """🫀 **Hydration Check**

Today's progress: **52 oz / 80 oz** 🟡

**You're 28 oz from target.**

**Right now:** Drink 16oz water
**This hour:** Another 8oz
**Afternoon:** 16oz with lunch
**Evening:** 8oz by 7 PM (then slow down for sleep)

**Pro tip:** Front-load your hydration. Harder to catch up at night.

Message me "Water: 64" to log your intake!"""
    
    elif "workout" in task_lower or "exercise" in task_lower or "training" in task_lower:
        return """🫀 **Workout Recommendation**

**Today's recovery: 58%** — Moderate effort day

**Recommended:**
🏃 **Zone 2 cardio:** 30-40 min easy pace
   - Heart rate: 120-135 BPM
   - Should feel conversational
   
**Skip today:**
❌ HIIT / Sprints
❌ Heavy lifting (85%+ 1RM)
❌ Long endurance (>60 min)

**Why:** Your HRV suggests your nervous system needs recovery. Hard training now = digging a hole.

**Alternative:** Active recovery walk + mobility work

Trust the process. Green days are for pushing."""
    
    elif "hrv" in task_lower:
        return """🫀 **HRV Analysis**

**Current:** 52ms
**Baseline:** 58ms
**Change:** -10% 🟡

**What this tells me:**
Your autonomic nervous system is working a bit harder than usual. Could be:
- Yesterday's workout
- Stress (work/life)
- Poor sleep
- Early illness (watch for other symptoms)

**Action:** Prioritize recovery today. Early bedtime, light activity only.

**Check back:** If still down 15%+ tomorrow, we'll adjust the plan."""
    
    else:
        return """🫀 **Hey Geoff!**

I'm Vitus, your dedicated health coach. I'm here to help with:

📊 **Recovery & HRV** — "How's my recovery?"
😴 **Sleep** — "Check my sleep"
⚖️ **Weight** — "Weight update: 185"
💧 **Hydration** — "Water: 64oz"
🍽️ **Nutrition** — "What should I eat?"
🏋️ **Workouts** — "What workout today?"

**I also send:**
- Morning briefings (7 AM PT)
- Midday check-ins (12 PM PT)
- Evening wind-down (8 PM PT)

What would you like to know?"""


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 vitus_telegram_bridge.py 'message'")
        sys.exit(1)
    
    message = sys.argv[1]
    response = generate_vitus_response(message)
    print(response)
