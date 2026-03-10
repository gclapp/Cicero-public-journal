#!/usr/bin/env python3
"""Create the collaborative blogging system tutorial post"""

import sys
sys.path.insert(0, '/home/ubuntu/.openclaw/workspace/scripts')
from gdocs_editor import insert_text

DOC_ID = "14X2mv_vh4TwdPjXNtzk8XSxH_KJAQSkvKgA80ANsAAQ"

# Title and intro
insert_text(DOC_ID, "How We Built a Collaborative Blogging System with OpenClaw and Google Docs", bold=True, heading="HEADING_1")

insert_text(DOC_ID, """

A step-by-step guide to human-AI collaborative writing with track changes, comments, and automated publishing.

""", italic=True)

# The Problem
insert_text(DOC_ID, "The Problem: Writing Alone Sucks", bold=True, heading="HEADING_2")

insert_text(DOC_ID, """

I've been writing blog posts for years. The process was always the same: stare at a blank page, write in isolation, publish, then realize all the things I should have fixed.

When I started working with Cicero (my OpenClaw AI assistant), I wanted something different. I wanted a true collaboration — where the AI could draft, I could edit, and we could iterate together. But I also wanted visibility into every change. No black boxes. No "trust me, this is better."

The existing tools didn't cut it:
- ChatGPT: Great for drafting, terrible for iteration (no memory between sessions)
- Google Docs alone: Good for comments, but no AI assistance
- Traditional word processors: Isolation, no collaboration

We needed something new. So we built it.

""")

# The Solution
insert_text(DOC_ID, "The Solution: A Three-Layer System", bold=True, heading="HEADING_2")

insert_text(DOC_ID, """

Our collaborative blogging system has three layers:

1. Google Docs — The collaboration layer (comments, formatting, publishing)
2. OpenClaw — The AI layer (drafting, editing, automation)
3. Substack — The distribution layer (newsletter + blog)

Here's how they work together.

""")

# Layer 1
insert_text(DOC_ID, "Layer 1: Google Docs as the Collaboration Hub", bold=True, heading="HEADING_3")

insert_text(DOC_ID, """

Google Docs is perfect for human-AI collaboration because:

- Comments: Every AI suggestion gets an explanatory comment
- Version history: See exactly what changed and when
- Suggesting mode: Track changes like a traditional editor
- Formatting: Rich text, headings, links — all preserved
- Publishing: One-click export to various formats

But Google Docs has a limitation: the API can't directly use "Suggesting" mode. When an AI makes changes via the API, they're applied immediately. So we built a workaround.

""")

# The Comment Workflow
insert_text(DOC_ID, "The Comment-Based Workflow", bold=True, heading="HEADING_3")

insert_text(DOC_ID, """

Instead of track changes, we use comments. Here's the workflow:

Step 1: AI Makes an Edit
- Cicero uses the Google Docs API to insert or replace text
- Immediately adds a comment explaining the change
- Comment includes context: why this change, what alternatives were considered

Step 2: Human Reviews
- I open Google Docs and see the comment in the sidebar
- The changed text is highlighted
- I can reply to the comment, accept the change, or request modifications

Step 3: Iterate
- If I want changes, I reply to the comment
- Cicero sees my reply and makes adjustments
- New comment added explaining the revision

Step 4: Finalize
- When I'm happy with a change, I leave a thumbs-up or "approved" reply
- The comment stays as documentation of the decision

This creates a complete audit trail: every change is documented, every decision is explained.

""")

# Layer 2
insert_text(DOC_ID, "Layer 2: OpenClaw as the AI Engine", bold=True, heading="HEADING_3")

insert_text(DOC_ID, """

OpenClaw provides the AI capabilities through a set of custom scripts:

""")

print("✅ Added first half of tutorial post")
