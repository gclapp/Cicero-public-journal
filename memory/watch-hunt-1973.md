# Watch Hunt Log — Geoff's 1973 Rolex Search

**Last Updated:** February 28, 2026
**Dashboard:** https://gclapp.github.io/geoff-watch-hunt/
**Repo:** https://github.com/gclapp/geoff-watch-hunt
**Preferences:** Blue and black dials (favorites) > Champagne/linen > Silver/white (avoid)
**Criteria:** 1973 Rolex Datejust, gold or two-tone, 36mm+, Sigma dial preferred

## 🤖 Automation Schedule

**Automated Search:** Twice daily via cron
- **Morning:** 9:00 AM Pacific (17:00 UTC)
- **Evening:** 6:00 PM Pacific (02:00 UTC next day)

**Current Status:**
✅ **Script Fixed (March 4, 2026)** — IndentationError resolved, searches now running  
✅ **Calendar Integration (March 4, 2026)** — Google Calendar connected, morning updates now include travel/events  
⚠️ **Limited by anti-scraping protections** — Most watch sites (Chrono24, Bob's Watches, Bulang & Sons) block automated scraping with 403 Forbidden errors.

**What works:**
✅ Script runs on schedule (9 AM & 6 PM PT daily)  
✅ Checks if existing listings are still active  
✅ Updates timestamps and pushes to GitHub  
✅ Logs activity for manual review  

**Limitations:**
❌ Cannot auto-scrape Chrono24 (403 Forbidden)  
❌ Cannot auto-scrape Bob's Watches (403 Forbidden)  
❌ Cannot auto-scrape Bulang & Sons (403 Forbidden)  

**Scripts:**
- `/home/ubuntu/.openclaw/workspace/scripts/watch-hunt-cron.sh` — Main cron script
- `/home/ubuntu/.openclaw/workspace/scripts/watch_search.py` — Search logic (scraping limited but functional)
- `/home/ubuntu/.openclaw/workspace/logs/watch-hunt.log` — Activity log

## 🔍 Alternative Approaches

Since sites block scraping, here are better options:

### Option 1: Saved Search Alerts (Recommended)
Set up alerts on each site — they'll email you when new watches match:
- **Chrono24:** Create account → Save search → Enable alerts
- **Bob's Watches:** Email alerts for new arrivals
- **Bezel:** App notifications for saved searches
- **eBay:** Saved searches with email alerts

### Option 2: Manual + Assisted Tracking
1. **You browse** the sites when convenient
2. **Send me links** to watches you find interesting
3. **I add them** to the dashboard with full details
4. **I track them** — check if sold, price changes, etc.

### Option 3: Browser Automation (Future)
Could use Selenium/Playwright to control a real browser:
- Bypasses most anti-scraping
- More complex setup
- Higher resource usage
- Can break when sites change

### Option 4: API Integration (If Available)
Some sites offer APIs for dealers/affiliates:
- Chrono24: Has API (requires partnership)
- Others: Check if they have public APIs

---

## 📋 ACTIVE LISTINGS (Under Review)

### 🔵 BLUE DIALS

| # | Year | Ref | Dial | Case | Price | Source | Link | Status | Notes |
|---|------|-----|------|------|-------|--------|------|--------|-------|
| 1 | 1978 | 16013 | Blue w/ gold markers | Two-tone (YG/steel) | TBD | Bob's Watches | https://www.bobswatches.com/rolex-datejust-16013-blue-dial-two-tone-jubilee.html | **PENDING REVIEW** | Jubilee bracelet, cal 3035, tritium patina |
| 2 | 1979 | 16013 | Blue (faded to purple) | Two-tone (YG/steel) | TBD | Bulang & Sons | https://bulangandsons.com/products/rolex-datejust-steel-and-gold-16013-blue-dial-w1415 | **PENDING REVIEW** | Desirable patina, Jubilee, serial 590xxxx |
| 3 | 1973 | 1601 | Blue Sigma | Steel | $6,027 | Chrono24 (Australia) | https://www.chrono24.com/rolex/rolex-datejust-36--id43520266.htm | **PENDING REVIEW** | Sigma dial (gold markers), all steel |
| 4 | 1973 | 1601 | Deep blue | Steel | $8,235 | Chrono24 (Switzerland) | https://www.chrono24.com/rolex/datejust-36--id43563233.htm | **PENDING REVIEW** | "Immaculate" condition, rare deep blue |

### ⚫ BLACK DIALS

| # | Year | Ref | Dial | Case | Price | Source | Link | Status | Notes |
|---|------|-----|------|------|-------|--------|------|--------|-------|
| 5 | 1973 | 1601 | Black | Unknown | $6,176 + shipping | Chrono24 (Poland) | Search "1601 Black dial 1973 Jubilee" | **PENDING REVIEW** | Need to verify if two-tone or steel |

---

## ✅ SOLD / NO LONGER AVAILABLE

| # | Year | Ref | Dial | Case | Price | Source | Date Sold | Notes |
|---|------|-----|------|------|-------|--------|-----------|-------|
| — | — | — | — | — | — | — | — | No records yet |

---

## 🗣️ GEOFF'S FEEDBACK LOG

### February 28, 2026
- **General preference:** Likes all dial colors except silver/white
- **Top picks:** Blue and black are favorites
- **Secondary:** Champagne/linen acceptable
- **Avoid:** Silver/white dials

### [To be filled as Geoff provides feedback on specific watches]

---

## 🎯 LEARNINGS / PATTERNS

- Blue dials in 1973 Datejusts are rarer than champagne but highly desirable
- Two-tone 16013s (post-1977) have quickset date (cal 3035) vs 1601s (no quickset)
- Most black dial 1601s from this era are all-steel; two-tone black dials are uncommon
- Sigma dials (σ T SWISS T σ) indicate solid gold markers/hands — preferred by collectors
- "Faded to purple" blue dials are considered desirable patina, not damage

---

## 📍 SOURCES MONITORED

- [x] Bob's Watches
- [x] Chrono24
- [x] Bulang & Sons
- [ ] Bezel (pending check)
- [ ] eBay (pending check)
- [ ] Craft & Tailored
- [ ] Paul's Watch Repair
- [ ] Vintage Watch Collective

---

## 🔔 ALERT THRESHOLDS

- Immediate alert for: Any 1973 two-tone Datejust with blue or black dial under $7,000
- Daily monitoring: All sources above
- Price drops: Track any watched listings for 10%+ price reductions

---

**Next Action:** Geoff to review listings #1-4 and provide feedback on which to pursue or eliminate.