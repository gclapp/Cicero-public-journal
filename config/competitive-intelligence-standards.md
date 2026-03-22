# Competitive Intelligence Report Standards
## LOCKED IN — March 22, 2026

**Status:** ✅ APPROVED BY GEOFF — This is the permanent format

---

## Report Structure (MUST FOLLOW)

### 1. Header
- Title: "🏛️ Competitive Intelligence Report"
- Date (full format: Sunday, March 22, 2026)
- Stats summary box with signal counts

### 2. Theme Section (REQUIRED)
- Identify the week's dominant theme
- 2-3 sentence insight box with background color
- Example: "🤖 AI Theme: All Competitors Launching AI Features"

### 3. Competitor Sections
- Group by competitor (Maven, Carrot, KindBody, WIN, etc.)
- Priority badges: 🔴 Critical / 🟠 High / 🟡 Medium
- Category tags: AI Launch, Partnership, Executive, etc.

### 4. Article Format
```
[BADGE] [BADGE]
[Linked Title]
[Date | Source]
[Summary with <strong> key points]
[Signal: One-line strategic takeaway]
```

### 5. Strategic Summary Section (REQUIRED)
- "🔥 Key Developments This Week" — bullet list
- "⚠️ Implications for Progyny" — strategic analysis

### 6. Footer
- Generation credit
- Sources list
- Next update time

---

## Content Standards

### Signal Classification
| Priority | Trigger Words | Response Time |
|----------|---------------|---------------|
| 🔴 Critical | Acquisition, IPO, $100M+ funding, merger | Immediate alert |
| 🟠 High | AI launch, partnership, executive hire, government | Same day report |
| 🟡 Medium | Profile, expansion, general news | Include in daily |

### Required Elements Per Article
1. **Linked title** (never raw URL)
2. **Date + source**
3. **Bold key facts** in summary
4. **Signal line** — what this means strategically
5. **Category badge**

### Analysis Requirements
- **Theme identification** — what's the pattern?
- **Implications** — so what for Progyny?
- **Trend context** — how does this fit the bigger picture?

---

## Data Sources (Priority Order)

1. **Web Search** (Brave API) — Real-time news
2. **RSS Feeds** — Google Alerts, industry publications
3. **LinkedIn** — Executive posts, job changes (when implemented)
4. **Job Boards** — Hiring signals (when implemented)

---

## Visual Standards

### Colors
- Critical: `#dc2626` (red)
- High: `#ea580c` (orange)
- Medium: `#ca8a04` (yellow)
- AI/Theme: `#7c3aed` (purple)
- Header: `#1a365d` (navy)

### Badges
- Priority badges first
- Category badges second
- All caps, bold, rounded corners

---

## Deduplication Rules

1. **Max age:** 7 days (skip older articles)
2. **Max sends:** 2 times per article
3. **Seen tracking:** Store in `competitor-seen-v2.json`
4. **Freshness check:** Always verify article date

---

## LinkedIn Integration (TODO)

When implemented, add:
- Executive post tracking
- Job change alerts
- Company announcement monitoring

Format same as news articles with "LinkedIn" source badge.

---

## History

- **2026-03-22:** Format approved by Geoff
- **Report sent:** Maven AI launch, Carrot HHS summit, Kindbody partnerships
- **Status:** LOCKED IN — Do not change structure without approval

---

**THIS DOCUMENT IS THE SOURCE OF TRUTH FOR COMPETITIVE INTELLIGENCE FORMAT.**
