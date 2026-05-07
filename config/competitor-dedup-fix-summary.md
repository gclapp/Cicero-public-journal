# Competitive Intelligence Deduplication Fix - Summary

## Changes Made (May 7, 2026)

### 1. Article Aging Fix (7-day window)
**Files Modified:**
- `scripts/competitor_intelligence_v3.py`
- `scripts/competitor_email_v3.py`

**Changes:**
- Changed `max_age_days` from 30 to 7 in `is_stale_article()` function
- Changed Brave Search API `freshness` parameter from "month" to "week"
- Changed email header from "30-Day Window" to "7-Day Window"
- Updated all cutoff calculations from 30 days to 7 days

### 2. Title-Based Deduplication
**Files Modified:**
- `scripts/competitor_intelligence_v3.py`
- `scripts/competitor_email_v3.py`

**Changes:**
- Added `normalize_title()` function to standardize titles for comparison
- Added `is_title_duplicate()` function to check for exact title matches
- Added `add_title_to_seen()` function to track seen titles
- Extended `seen` data structure to include `titles` dictionary
- RSS feed scanner now skips articles with duplicate titles
- Web search scanner now skips articles with duplicate titles
- Email generator filters out duplicate titles before generating report

### Normalization Rules
Titles are normalized by:
1. Converting to lowercase
2. Stripping whitespace
3. Collapsing multiple spaces into single spaces
4. Removing common source suffixes ("- PR Newswire", "- Business Wire", etc.)

## Result
- Reports now only contain articles from the last 7 days
- Duplicate articles (same title) are filtered out at collection and display time
- Geoff will no longer see the same Maven Series F article repeated across multiple reports

## Testing
- Verified script runs successfully
- Verified email generates with 7-day window label
- Verified duplicate titles are excluded from email output
