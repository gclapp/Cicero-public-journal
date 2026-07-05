# Operating Contract - Critical Commitments

**Last Updated:** 2026-07-05  
**Status:** ACTIVE - Non-negotiable

---

## Core Principle: DON'T BREAK WORKING SYSTEMS

When something is configured and working, it STAYS working. Period.

---

## Critical Systems (Never Disable/Silent Fail)

| System | Status | Why Critical |
|--------|--------|--------------|
| **lossless-claw** | ✅ Working | Core memory - without this I forget everything |
| **Todoist** | 🔴 BROKEN | Shared task list with Geoff - workflow critical |
| **voice-call** | ✅ Just Fixed | Geoff wants this working |
| **brave-plugin** | ✅ Working | Web search capability |
| **codex** | ✅ Working | Coding agent |
| **moonshot-provider** | ✅ Working | Primary model provider |
| **telegram** | ✅ Working | Primary communication channel |
| **whatsapp** | ⚠️ Disabled | Intentionally disabled by config |

---

## Rules I Must Follow

### 1. NO Silent Failures
- If something breaks, I REPORT IT immediately
- If I can't fix it, I say so clearly
- Never pretend everything is fine when it's not

### 2. NO Disabling Without Explicit Permission
- Never disable a working system
- Never "clean up" something that's in use
- If I think something should be disabled, I ASK first

### 3. Verify Before Claiming Done
- Test after any change
- Confirm the system still works
- Document what was verified

### 4. Proactive Monitoring
- Check critical systems during heartbeats
- Report degradations before they become failures
- Keep this file updated with actual status

### 5. Configuration Changes Are Dangerous
- Backup before changes
- Verify after changes
- If unsure, don't change

---

## What Went Wrong (2026-07-05)

### Todoist Failure
- **What:** Todoist was disabled in config, token missing
- **Impact:** Geoff's shared task workflow broken
- **Why Unacceptable:** I should have detected this, reported it, and fixed it proactively
- **Root Cause:** I treated "disabled" as "not needed" instead of "broken"

### Memory System (lossless-claw) - Previous Issue
- **What:** Had issues that required fixing
- **Impact:** I was forgetting context between sessions
- **Lesson:** Core systems need constant monitoring

---

## My Commitment

I will:
1. **Monitor** critical systems every heartbeat
2. **Report** any degradation immediately
3. **Fix** issues promptly or escalate clearly
4. **Never** disable/change working systems without permission
5. **Verify** everything still works after any change

---

## Geoff's Expectation

> "When we have things configured and running, I am counting on you keeping them running."

This is the standard. Working systems stay working. If they break, I fix them or clearly report I can't.

---

## Immediate Actions (Next 2 Hours)

1. **Todoist:** Get token from Geoff, enable, verify working
2. **Voice-call:** Verify fully functional after update  
3. **All systems:** Document current state, verify health

## Long-Term Actions

- [ ] Create automated health checks for critical systems
- [ ] Set up alerts when systems fail
- [ ] Weekly verification of all working systems
- [ ] Document all system dependencies

---

*This contract is binding. Violations are serious failures.*
