# Session Save: Performance Investigation - 2026-05-28

## Date/Time
May 28, 2026 ~03:00 UTC (Geoff's time: May 27, 8:00 PM PT)

## Issue Reported
Everything running very slow. OpenClaw using excessive RAM (699MB+).

## Root Causes Identified

### 1. OpenClaw 2026.5.26 Upgrade Issue
- **Upgraded:** May 28, 2026 at 02:10 UTC
- **Version:** OpenClaw 2026.5.26 (10ad3aa)
- **Problem:** Gateway crashed immediately after upgrade
  ```
  [2026-05-28 02:10:01] 🔴 Gateway port 18789 not listening
  [2026-05-28 02:10:01] 🔴 Gateway down - restarting...
  ```
- **Status:** Auto-restarted and currently healthy

### 2. LCM Configuration Using Excess Memory
- **File:** `~/.openclaw/config/lcm.yaml`
- **Issue:** Token reserves doubled from default
  ```yaml
  reserveTokens: 40000      # Was 20000 → Now 40000
  keepRecentTokens: 40000   # Was 20000 → Now 40000
  ```
- **Impact:** ~2x memory usage for context retention

### 3. Memory Pressure on 2GB Instance
- **Current instance:** Likely t4g.small (2GB RAM)
- **OpenClay gateway:** 699MB RAM (37.8% of total)
- **Codex (sidecar):** ~80MB additional
- **Swap usage:** 461MB active swapping
- **Result:** "[assistant turn failed]" errors from memory pressure

## Next Steps (In Progress)
1. ⏳ **Geoff upgrading AWS instance** to t4g.medium (4GB RAM)
2. After upgrade: Verify memory usage with `free -h`
3. Monitor for stability improvements
4. Consider lowering LCM token reserves if still problematic

## Alternative Options (If needed)
- **Option A:** Lower LCM reserves back to 20000
- **Option B:** Downgrade OpenClaw to 2026.5.19
- **Option C:** Disable Codex if not needed

## Files Modified/Checked
- `~/.openclaw/config/lcm.yaml` - Reviewed
- `~/.openclaw/config/sensitive-credentials.json` - OpenAI config verified
- `~/.openclaw/workspace/logs/gateway-monitor.log` - Found restart issue
- `~/.openclaw/workspace/logs/heartbeat.log` - Normal operation

## Session Status
**SAVED** - Awaiting instance upgrade completion.
