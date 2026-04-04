# Security & Status Audit Report
**Date:** April 4, 2026  
**Time:** 5:37 PM UTC / 10:37 AM PT

---

## 🔐 Token Health Status

| Service | Status | Age | Action Needed |
|---------|--------|-----|---------------|
| Google Calendar | ✅ Healthy | 6 days | None |
| Google Docs | ⚠️ Warning | 7 days | Re-auth soon |
| Whoop API | 🔴 **EXPIRED** | — | **RE-AUTH REQUIRED** |
| Whoop Refresh | ✅ Healthy | 0 days | None |
| Gmail SMTP | ⚠️ Warning | 39 days | Monitor |

### Critical Issues:
1. **Whoop API token expired** — Health data not syncing
2. **Google Docs token aging** — Will need re-auth in ~1 day
3. **Gmail SMTP over 30 days** — Functional but aging

---

## 🖥️ EC2 Instance Security

### Firewall (UFW): ✅ ACTIVE
```
Status: active
Allowed ports:
- 22/tcp   (SSH)        ✓
- 80/tcp   (HTTP)       ✓
- 3000/tcp (Node.js)    ✓
- 8900/tcp (ClawMetry)  ✓
```

### Open Ports:
- Port 22 (SSH) — Secured, key-based auth only
- Port 80 (HTTP) — OpenClaw gateway
- Internal ports 18789-18792 (OpenClaw services)

### System Resources:
- **Disk:** 73% used (14G/19G) — ⚠️ Getting full
- **Memory:** 42% used (763M/1.8G) — ✅ Healthy
- **Swap:** 21% used — ✅ Normal

### SSH Security:
- No recent failed password attempts detected
- Key-based authentication enforced
- Root login disabled

---

## 🤖 OpenClaw Gateway Status

| Component | Status |
|-----------|--------|
| Gateway Service | ✅ Running (PID 475577) |
| RPC Probe | ✅ OK |
| Dashboard | ✅ http://127.0.0.1:18789/ |
| LCM Plugin | ✅ Loaded |

### Warnings:
- **Telegram group policy** set to "allowlist" but no IDs configured
  - Fix: Add sender IDs to `channels.telegram.groupAllowFrom`
- **Plugins.allow** is empty — non-bundled plugins may auto-load
  - Fix: Set explicit trusted plugin IDs

---

## 🛠️ Installed Skills (22 Total)

### Core Skills:
| Skill | Status | Security |
|-------|--------|----------|
| gog (Google Workspace) | ✅ Active | OAuth tokens secured |
| todoist | ✅ Active | Token secured |
| weather | ✅ Active | No auth required |
| whoop | ⚠️ Token expired | Needs re-auth |
| gws-docs-write | ⚠️ Token aging | Monitor |
| reddit-search-but-free | ✅ Active | No auth required |
| flight-tracker | ✅ Active | No auth required |
| linkedin-content | ✅ Active | No auth required |
| skill-vetter | ✅ Active | No auth required |
| sag (TTS) | ✅ Active | API key secured |
| openai-image-gen | ✅ Active | API key secured |
| opentable | ✅ Active | Needs API key |
| healthcheck | ✅ Active | No auth required |
| proactive-agent-skill | ✅ Active | No auth required |
| capability-evolver | ✅ Active | No auth required |
| clawdbites | ✅ Active | No auth required |
| linkedin-writer | ✅ Active | No auth required |
| flight-search | ✅ Active | No auth required |
| mission-control-dashboard | ✅ Active | No auth required |

---

## 📁 Credential File Permissions

### Fixed ✅
- `~/.whoop_token` — 600 (was 664)
- `~/.whoop_refresh_token` — 600 (was 664)
- `~/.openclaw/credentials/calendar-token.pickle` — 600 (was 664)
- `~/.openclaw/credentials/gdocs-token.pickle` — 600 (was 664)

### Already Secure ✅
- All OAuth credential files — 600
- All API key files — 600
- All pairing tokens — 600

---

## 🚨 Action Items

### Immediate (Today):
1. **Re-authorize Whoop** — Health data not syncing
   - Visit: https://developer.whoop.com/
   - Create app → Get client ID/secret
   - Run: `python3 scripts/whoop_oauth.py --config config/whoop-config.json`

### This Week:
2. **Re-authorize Google Docs** — Token expires soon
3. **Clean up disk space** — 73% full, needs attention
4. **Configure Telegram group policy** — Add allowed sender IDs

### Monitor:
5. **Gmail SMTP** — Over 30 days, may need refresh soon
6. **Calendar token** — At 6 days, refresh in ~1 day

---

## ✅ Security Posture: GOOD

- Firewall active with minimal open ports
- All credentials properly secured (600 permissions)
- No secrets in Git repository
- SSH key-based auth only
- Automatic token health monitoring enabled
- Daily backups to GitHub

**Overall Status:** Systems operational, 3 tokens need attention
