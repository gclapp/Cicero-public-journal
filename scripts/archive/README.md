# Scripts Archive

This directory contains archived versions of scripts that are no longer in active use. These scripts are preserved for reference, historical context, and potential future reuse.

**Policy:** Only actively used scripts should remain in the main `scripts/` directory. All old versions, experiments, and deprecated scripts belong here.

---

## Active Scripts (in main scripts/ directory)

These are the canonical versions currently in use:

### Competitor Intelligence
- **`daily-competitor-report-v3.sh`** - Main competitor intelligence report (runs 7 AM & 2 PM PT daily)
- **`competitor_intelligence_v3.py`** - RSS + web search monitoring (called by daily-competitor-report-v3.sh)
- **`competitor_email_v3.py`** - Email report generation (called by daily-competitor-report-v3.sh)
- **`linkedin_monitor.py`** - LinkedIn + job change monitoring (called by daily-competitor-report-v3.sh)

### Token Health & Authentication
- **`token_auto_refresh_v2.py`** - Active token auto-refresh system (runs every 30 min)
- **`token_health_monitor.py`** - Comprehensive token health monitoring

### Whoop Integration
- **`whoop_daily_fetch.py`** - Daily Whoop data fetch (7:30 AM PT)
- **`whoop_alerts.py`** - Whoop health alerts (every 6 hours)

### Travel Automation
- **`calendar_travel_checker.py`** - Main travel task checker (Mon/Wed/Fri 9 AM PT)
- **`travel_flight_monitor.py`** - Flight monitoring
- **`travel_car_check.py`** - Car rental checking

### Heartbeat System
- **`heartbeat_sender.py`** - Current heartbeat sender
- **`heartbeat-check.sh`** - Heartbeat checker (every 55 min)

### Calendar
- **`calendar_reader.py`** - Active calendar reader (6:55 AM PT daily)
- **`refresh_calendar_token.py`** - Calendar token refresh utility

### Progyny Intelligence
- **`progyny_intel_cron.sh`** - Progyny intelligence cron wrapper
- **`progyny_intel_cron.py`** - Progyny intelligence script

### Health Processing
- **`loseit_parser.py`** - Lose It! app data parser
- **`system_health_check.py`** - System health monitoring
- **`system_health_monitor.py`** - Health monitoring system

### Watch Search
- **`watch-hunt-cron.sh`** - Watch hunt cron wrapper (9 AM & 6 PM PT)

### Google Docs Integration
- None currently active (using direct GitHub workflow instead)

---

## Archive Categories

### competitor-intel/
Old versions of competitor intelligence scripts:
- `competitor_daily.py` - Early daily competitor check (Mar 2025)
- `competitor_email_v2.py` - Email report v2 (Apr 2025)
- `competitor_intelligence_v2.py` - Intelligence v2 (Apr 2025)
- `daily-competitor-report-v2.sh` - Shell wrapper v2 (Apr 2025)

**Note:** v3 scripts (`competitor_intelligence_v3.py`, `competitor_email_v3.py`, `linkedin_monitor.py`) were restored to main scripts/ on May 25, 2026 because they are actively called by `daily-competitor-report-v3.sh`.

**Why archived:** Older versions superseded by v3

### token-health/
Old token health monitoring scripts:
- `token_auto_refresh.py` - Original auto-refresh (Apr 2025)
- `token_daily_monitor.py` - Daily token check (Mar 2025)
- `token_health_check.py` - Original health check (Apr 2025)
- `token_health_check_v2.py` - Health check v2 (May 2025)

**Why archived:** Replaced by `token_auto_refresh_v2.py` and `token_health_monitor.py`

### whoop/
Old Whoop integration scripts:
- `whoop_auth.py` - Original auth flow (Mar 2025)
- `whoop_exchange.py` - Token exchange (Mar 2025)
- `whoop_fetch.py` - Original fetch script (Mar 2025)
- `whoop_reauth.py` - Re-authentication utility (Mar 2025)
- `fetch_whoop_daily.py` - Early daily fetch (Mar 2025)

**Why archived:** Replaced by `whoop_daily_fetch.py` and `whoop_alerts.py`

### travel/
Old travel automation versions:
- `travel_automation.py` - Original travel automation (Apr 2025)
- `travel_automation_subtasks.py` - Subtask creation (Apr 2025)
- `travel_automation_urgent.py` - Urgent travel checks (Apr 2025)
- `travel_automation_v2.py` - Travel automation v2 (May 2025)

**Why archived:** Consolidated into `calendar_travel_checker.py`

### heartbeat/
Old heartbeat system versions:
- `heartbeat_sender_backup_2026-05-24.py` - Backup from May 2026
- `heartbeat_sender_v2.py` - Heartbeat v2 (May 2026)

**Why archived:** Replaced by current `heartbeat_sender.py`

### watch-search/
Old watch search implementations:
- `watch_search.py` - Original search (Mar 2025)
- `watch_search_multi.py` - Multi-source search (Mar 2025)
- `watch_search_robust.py` - Robust search version (Mar 2025)
- `watch_search_scrapling.py` - Scrapling-based search (Mar 2025)

**Why archived:** Replaced by watch hunt system in separate repository

### gdocs/
Google Docs integration experiments:
- `gdocs_auth_exchange.py` - Auth exchange (May 2025)
- `gdocs_auth_setup.py` - Auth setup (Mar 2025)
- `gdocs_bulletproof_auth.py` - Bulletproof auth (May 2025)
- `gdocs_comments.py` - Comments integration (Mar 2025)
- `gdocs_editor.py` - Full editor (Mar 2025)
- `gdocs_simple.py` - Simple version (Mar 2025)
- `gdocs_token_refresh.py` - Token refresh (May 2025)
- `gdocs_track_changes.py` - Track changes (Mar 2025)
- `gdocs_track_changes_simple.py` - Simple track changes (Mar 2025)

**Why archived:** Moved to direct GitHub-based workflow instead of Google Docs

### calendar/
Old calendar authentication and intelligence scripts:
- `calendar_auth.py` - Original auth (Mar 2025)
- `calendar_auth_complete.py` - Auth completion (Mar 2025)
- `calendar_auth_manager.py` - Auth manager (Mar 2025)
- `calendar_auth_start.py` - Auth starter (Mar 2025)
- `calendar_intelligence.py` - Early intelligence (Mar 2025)

**Why archived:** Replaced by `calendar_reader.py` and `refresh_calendar_token.py`

### progyny/
Old Progyny intelligence scripts:
- `progyny_exec_report_strict.py` - Strict executive report (Mar 2025)
- `progyny_executive_report.py` - Executive report (Mar 2025)
- `progyny_intelligence.py` - Original intelligence (Mar 2025)
- `progyny_sentiment_monitor.py` - Sentiment monitoring (Mar 2025)

**Why archived:** Consolidated into `progyny_intel_cron.py`

### health/
Old health data processing scripts:
- `process_health_emails_v2.py` - Health email processor v2 (May 2025)
- `process_steps_email.py` - Steps email processor (May 2025)
- `process_water_email.py` - Water email processor (May 2025)
- `process_weight_email.py` - Weight email processor (May 2025)
- `weight_loss_tracker.py` - Original tracker (Mar 2025)

**Why archived:** Integrated into health agent system

### morning-email/
*(Reserved for old morning email generator versions)*

### misc/
Experimental and one-off scripts:

**Note:** `linkedin_monitor.py` was restored to main scripts/ on May 25, 2026 (actively used by competitor intelligence).
- `add_week1_*.py` - Week 1 content additions (Mar 2025)
- `chrono24_*.py` - Chrono24 scraping experiments (Mar 2025)
- `content_analytics_collector.py` - Analytics collection (Mar 2025)
- `create_blog_system_post*.py` - Blog system experiments (Mar 2025)
- `download_*.py` - Various image downloaders (Mar 2025)
- `export_to_substack.py` - Substack export (Mar 2025)
- `final_image_attempt.py` - Image processing (Mar 2025)
- `fix_week1_grammar.py` - Grammar fixes (Mar 2025)
- `flight_email_filter_demo.py` - Flight filter demo (May 2025)
- `linkedin_*.py` - LinkedIn experiments (Mar 2025)
- `reddit_*.py` - Reddit experiments (Mar 2025)
- `response_deduplicator.py` - Deduplication utility (Mar 2025)
- `scrape_watch_images.py` - Image scraper (Mar 2025)
- `screenshot_watches.py` - Screenshot tool (Mar 2025)
- `search_manager.py` - Search management (Mar 2025)
- `social_media_poster.py` - Social poster (Mar 2025)
- `twitter_browser_post.py` - Twitter experiments (Mar 2025)
- `update_watch_images.py` - Image updater (Mar 2025)
- `watch_image_*.py` - Image processing (Mar 2025)

**Why archived:** Experimental scripts that were superseded or not put into production

---

## Archive Maintenance

- **Do not execute scripts from archive/** - They may have outdated dependencies or broken paths
- **Reference only** - Use for code examples, logic reference, or historical context
- **No automatic cleanup** - Scripts are kept indefinitely unless explicitly deleted
- **Add date context** - When archiving new scripts, note the date and reason in this README

---

## Last Updated

May 25, 2026 - Initial archive organization
- Created archive structure with 12 category folders
- Archived 79 old scripts
- Restored v3 competitor intelligence scripts to active (they were incorrectly archived)
- Added progyny_intel_cron.sh symlink for crontab compatibility
