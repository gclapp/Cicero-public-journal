#!/usr/bin/env python3
"""Create second half of the blogging system tutorial"""

import sys
sys.path.insert(0, '/home/ubuntu/.openclaw/workspace/scripts')
from gdocs_editor import insert_text

DOC_ID = "14X2mv_vh4TwdPjXNtzk8XSxH_KJAQSkvKgA80ANsAAQ"

# Scripts table
insert_text(DOC_ID, """
| Script | Purpose |
|--------|---------|
| gdocs_editor.py | Create documents, insert text, replace text, formatting |
| gdocs_comments.py | Add comments, list comments, resolve comments |
| gdocs_track_changes_simple.py | Save snapshots, compare versions |
| gdocs_auth_setup.py | One-time OAuth authentication |

Each script is a thin wrapper around the Google Docs API, designed for human-AI collaboration.

Example: Adding a Comment

When Cicero wants to suggest a change, he runs:

python3 scripts/gdocs_comments.py add \\
  --doc-id DOCUMENT_ID \\
  --anchor "text to comment on" \\
  --text "PROPOSED CHANGE: Explanation here"

This creates a comment attached to specific text, with a clear explanation of what changed and why.

""")

# Layer 3
insert_text(DOC_ID, "Layer 3: Substack for Distribution", bold=True, heading="HEADING_3")

insert_text(DOC_ID, """

Once the post is finalized in Google Docs, we export to Substack:

1. Copy final text from Google Docs
2. Paste into Substack editor
3. Format with Substack's tools
4. Schedule or publish

Substack was chosen because:
- Built-in newsletter (posts go to email automatically)
- Discovery through recommendation engine
- Zero maintenance (no hosting, no updates)
- Easy monetization if we ever want paid subscriptions
- Comments and community features

""")

# The Workflow in Practice
insert_text(DOC_ID, "The Workflow in Practice: A Real Example", bold=True, heading="HEADING_2")

insert_text(DOC_ID, """

Here's how we wrote this very post:

1. I (Geoff) asked Cicero to create a tutorial about our blogging system
2. Cicero created the Google Doc and started drafting sections
3. For each section, Cicero added content and commented on key decisions
4. I reviewed in Google Docs, replying to comments with feedback
5. Cicero made adjustments based on my replies
6. We iterated until the post felt complete
7. Final export to Substack for publishing

Total time: About 30 minutes of active collaboration.

Compare this to traditional writing:
- Draft alone: 2-3 hours
- Self-edit: 1 hour
- Publish and hope it's good

Or vs. ChatGPT:
- Generate draft: 5 minutes
- Realize it needs changes
- Start new chat, lose context
- Repeat 3-4 times

Our system preserves context, documents decisions, and creates a true collaboration.

""")

# Technical Setup
insert_text(DOC_ID, "Technical Setup: How to Build This Yourself", bold=True, heading="HEADING_2")

insert_text(DOC_ID, """

Prerequisites:
- OpenClaw installed and configured
- Google Cloud project with Docs API enabled
- OAuth credentials downloaded

Step 1: Authentication

Run the setup script once:

python3 scripts/gdocs_auth_setup.py

This opens a browser for OAuth approval. After authorization, tokens are saved locally.

Step 2: Create Your First Document

python3 scripts/gdocs_editor.py create \\
  --title "My Blog Post" \\
  --text "Initial content here"

Step 3: Add a Comment

python3 scripts/gdocs_comments.py add \\
  --doc-id YOUR_DOC_ID \\
  --anchor "Initial content here" \\
  --text "Consider expanding this section with examples"

Step 4: Check for Changes

python3 scripts/gdocs_track_changes_simple.py compare \\
  --doc-id YOUR_DOC_ID

This shows what's changed since the last snapshot.

""")

# The Code
insert_text(DOC_ID, "The Code", bold=True, heading="HEADING_2")

insert_text(DOC_ID, """

All scripts are open source and available on GitHub:

https://github.com/gclapp/cicero-backup/tree/main/scripts

Key files:
- gdocs_editor.py — Main editing functions
- gdocs_comments.py — Comment management
- gdocs_track_changes_simple.py — Version comparison
- gdocs_auth_setup.py — OAuth setup

Feel free to adapt these for your own workflow.

""")

# Lessons Learned
insert_text(DOC_ID, "Lessons Learned", bold=True, heading="HEADING_2")

insert_text(DOC_ID, """

After using this system for several posts:

Comments > Track Changes
API-based track changes don't work well in Google Docs. Comments are actually better — they force explanation and create documentation.

Snapshots Matter
Before any major editing session, save a snapshot. When something goes wrong, you can compare and recover.

Iterate Fast
The best posts come from rapid iteration. Don't aim for perfect on the first draft. Get something down, then refine through comments.

Human Has Final Say
The AI can suggest, but the human decides. This keeps the voice authentic and the content aligned with intent.

""")

# Conclusion
insert_text(DOC_ID, "Conclusion", bold=True, heading="HEADING_2")

insert_text(DOC_ID, """

This post was written using the exact system it describes. Meta, right?

The key insight: AI isn't replacing human creativity — it's amplifying it. By handling the mechanical aspects (formatting, version tracking, basic drafting), the AI frees the human to focus on what matters: ideas, voice, and judgment.

If you try this system, let me know how it goes. I'm @geoffclapp on Twitter/X and the full journey is documented at github.com/gclapp/Cicero-public-journal.

Happy writing.

---

Built with OpenClaw 🦞

""")

print("✅ Tutorial post complete!")
