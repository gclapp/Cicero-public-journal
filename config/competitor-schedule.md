# Competitive Intelligence Report Schedule

## Current Setup (As of March 3, 2026)

### Automation
- **Schedule:** Daily at 6:00 AM PT (14:00 UTC)
- **Destination:** geoffrey.clapp@progyny.com
- **Script:** `scripts/daily-competitor-report.sh`
- **Condition:** Only sends if there are new articles worth reporting

### Active Feeds (6 Total)
| Priority | Entity | Type |
|----------|--------|------|
| 🔷 **Primary** | **Progyny (PGNY)** | Self-monitoring |
| 🔴 High | Maven | Competitor |
| 🔴 High | Carrot | Competitor |
| 🔴 High | KindBody | Competitor |
| 🔴 High | WIN Fertility | Competitor |
| 🔴 High | Pomelo Health | Competitor |

**Important:** PGNY is treated as a primary entity alongside competitors. All PGNY news (positive, negative, partnerships, funding, etc.) appears prominently in reports alongside competitor news.

### Report Structure
1. **🔷 Progyny (PGNY) Section** - Featured at top
2. **🔴 High Priority Competitors** - Funding, acquisitions, major news
3. **🟡 Medium Priority Competitors** - Partnerships, launches, exec changes
4. **⚪ General News** - Other mentions

### Next Report
**Tomorrow (March 4, 2026) at 6:00 AM PT** — scanning all 6 feeds for new articles.

### To Add More Feeds
Edit: `config/competitor-feeds.json`

Recommended additional feeds:
- Kate Ryder (Maven CEO) personal mentions
- Menopause competitors: Midi, Geneev, Evernow
- Fertility tech news sources

### Manual Check
```bash
cd ~/.openclaw/workspace
python3 scripts/competitor_monitor.py
python3 scripts/competitor_email.py
```

### Key Feature
PGNY news appears **alongside** competitors — not separate. You'll see:
- Progyny funding news next to Maven funding news
- Progyny partnerships next to competitor partnerships
- All signal types treated equally for full context
