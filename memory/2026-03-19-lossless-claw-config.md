# Lossless-Claw (LCM) Configuration — March 19, 2026

## Overview
Upgraded context engine from legacy to **lossless-claw** for improved memory retention and context management.

## Environment Variables Set

```bash
export LCM_FRESH_TAIL_COUNT=32        # Keep 32 recent messages uncompressed
export LCM_INCREMENTAL_MAX_DEPTH=-1   # Unlimited condensation depth  
export LCM_CONTEXT_THRESHOLD=0.75     # Compact at 75% of context window
```

**Location:** Added to `~/.bashrc` for persistence across sessions.

---

## What Lossless-Claw Provides

### Core Features
- **Hierarchical summarization** — Messages → Leaf summaries → Condensed summaries (depth 1, 2, 3+)
- **Fresh tail protection** — Last 32 messages always kept in raw form
- **DAG-based storage** — Summaries form a directed acyclic graph for efficient retrieval
- **Expansion tools** — `lcm_grep`, `lcm_describe`, `lcm_expand`, `lcm_expand_query`
- **Large file handling** — Files >25k tokens stored separately with exploration summaries
- **Crash recovery** — Bootstrap reconciliation between JSONL and database

### Data Model
- **Conversations** — keyed by session ID
- **Messages** — seq, role, content, tokenCount, createdAt
- **Summaries** — `sum_` + 16 hex chars, depth, time range, descendant count
- **Context items** — Ordered list of what the model sees

---

## Testing Checklist

### Basic Functionality
- [ ] Long conversation (50+ messages) without crashes
- [ ] Verify last 32 messages remain raw
- [ ] Confirm older messages get summarized

### Context Retention
- [ ] Reference something from 20+ messages ago
- [ ] Ask for expansion on summarized topics
- [ ] Test `lcm_expand_query` tool

### Database Verification
```bash
# Count conversations
sqlite3 ~/.openclaw/lcm.db "SELECT COUNT(*) FROM conversations;"

# Summary depth distribution  
sqlite3 ~/.openclaw/lcm.db "SELECT depth, COUNT(*) FROM summaries GROUP BY depth;"

# Recent context items
sqlite3 ~/.openclaw/lcm.db "SELECT * FROM context_items ORDER BY ordinal DESC LIMIT 10;"
```

### Compaction Verification
- [ ] Run `/compact` manually
- [ ] Check summaries created at depths 0, 1, 2+
- [ ] Monitor token savings

### LCM Tools to Test
- `lcm_grep` — Search history
- `lcm_describe` — Lookup summary by ID
- `lcm_expand` — Expand summary children
- `lcm_expand_query` — Deep search with sub-agent

---

## Monitoring

```bash
# Watch compaction logs
tail -f ~/.openclaw/logs/lcm.log

# Database size
ls -lh ~/.openclaw/lcm.db

# Summary statistics
sqlite3 ~/.openclaw/lcm.db "
  SELECT 
    COUNT(*) as total_summaries,
    AVG(token_count) as avg_tokens,
    MAX(depth) as max_depth
  FROM summaries;
"
```

---

## Potential Issues to Watch

| Issue | Symptom | Fix |
|-------|---------|-----|
| Database locked | SQLite lock errors | Check concurrent access |
| Summarization failures | Empty/oversized summaries | Check LLM connectivity |
| Context overflow | Model context exceeded | Lower `LCM_CONTEXT_THRESHOLD` |
| Missing recent context | Forget recent conversation | Increase `LCM_FRESH_TAIL_COUNT` |

---

## Documentation References

- Architecture: `~/.openclaw/extensions/lossless-claw/docs/architecture.md`
- Configuration: `~/.openclaw/extensions/lossless-claw/docs/configuration.md`
- Agent Tools: `~/.openclaw/extensions/lossless-claw/docs/agent-tools.md`

---

## Status

**Date:** March 19, 2026  
**Configured by:** User via OpenClaw Control UI  
**Database status:** Not yet created (will be created on first session)  
**Next review:** After 1 week of usage

---

*Lossless-claw provides "infinite" context through intelligent summarization while preserving the ability to drill into details when needed.*
