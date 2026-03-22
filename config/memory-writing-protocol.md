# Memory Writing Protocol
## For Cicero — March 22, 2026

**Purpose:** Ensure critical insights, decisions, and context are never lost to LCM compaction.

---

## TRIGGER: Write to Memory IMMEDIATELY When:

### 1. User States Preferences or Standards
- "I want reports to look like this going forward"
- "Always do X instead of Y"
- "This is the format I want"
- **Action:** Update `config/*-standards.md` or `MEMORY.md`

### 2. User Shares Personal Data
- Weight, health metrics, recovery data
- Travel plans, calendar updates
- Family information
- **Action:** Write to `memory/YYYY-MM-DD.md` AND update relevant tracker files

### 3. User Corrects or Clarifies
- "No, that's wrong..."
- "Actually, I meant..."
- "Don't forget that..."
- **Action:** Update relevant files immediately, document the correction

### 4. Analysis or Insights Generated
- Whoop data analysis
- Competitive intelligence findings
- Calendar pattern insights
- **Action:** Write to `memory/YYYY-MM-DD.md` with full context

### 5. Decisions Made
- "Let's do X twice a day"
- "Send emails as HTML"
- "Add this to the report"
- **Action:** Document in `memory/YYYY-MM-DD.md` AND update relevant config

---

## WRITE LOCATIONS (Priority Order)

### 1. Daily Log (HIGHEST PRIORITY)
**File:** `memory/YYYY-MM-DD.md`

**Include:**
- Raw data shared by user
- Analysis performed
- Insights discovered
- Decisions made
- Action items

**Format:**
```markdown
# 2026-03-22 — Sunday

## Health Data
- Weight: 237.0 lbs (new low)
- Whoop recovery: 60%
- Sleep: 8h 33m

## Analysis
[Cortisol analysis details]

## Decisions
- [ ] Lose 2.4 lbs by Saturday 5 PM
- [ ] Competitive intel format locked in

## Files Updated
- `config/competitive-intelligence-standards.md`
- `config/weight-loss-email.html`
```

### 2. Standards & Configuration
**Files:**
- `config/*-standards.md` — Format rules, preferences
- `config/*-config.json` — System configuration
- `MEMORY.md` — Long-term memory, critical rules

**When to update:**
- User approves a format → Save to standards file
- New integration working → Document in MEMORY.md
- Critical rule established → Add to MEMORY.md

### 3. Trackers & Plans
**Files:**
- `memory/weight-loss-2026.md`
- `memory/python-learning-2026.md`
- `memory/friend-profiles/*.md`

**When to update:**
- New data point (weight, lesson completed)
- Profile information added
- Milestone reached

---

## ANTI-PATTERNS (NEVER DO)

❌ **Don't rely on LCM for recent context**
- LCM compacts aggressively
- Recent messages may be summarized away
- Always write important data to files

❌ **Don't wait for "end of conversation"**
- Write insights as they happen
- User may not return for hours
- Better to have duplicate info than lost info

❌ **Don't trust "I'll remember that"**
- Each session starts fresh
- Files are the only persistent memory
- When in doubt, write it down

---

## VERIFICATION CHECKLIST

After ANY significant interaction:
- [ ] Did user share data that should persist? → Write to daily log
- [ ] Did user state a preference? → Update standards
- [ ] Did I generate analysis? → Document in daily log
- [ ] Was a decision made? → Record in daily log + update relevant files
- [ ] Did user correct me? → Update files + document correction

---

## EXAMPLE WORKFLOW

**User says:** "I want competitive reports to look like this going forward"

**Immediate actions:**
1. ✅ Acknowledge receipt
2. ✅ Create `config/competitive-intelligence-standards.md`
3. ✅ Document in `memory/2026-03-22.md`
4. ✅ Reference in future reports

**User shares:** "My Whoop recovery was 8% on March 15"

**Immediate actions:**
1. ✅ Add to `memory/2026-03-22.md`
2. ✅ Update `memory/weight-loss-2026.md` with recovery data
3. ✅ Include in analysis/cortisol discussion

---

## REMEMBER

**Text > Brain > LCM**

1. **Text (files)** — Permanent, searchable, reliable
2. **Brain (context)** — Temporary, session-bound
3. **LCM (summaries)** — Compressed, lossy, for old context only

**When something matters: WRITE IT TO A FILE IMMEDIATELY**

---

**Created:** March 22, 2026
**Applies to:** All sessions going forward
