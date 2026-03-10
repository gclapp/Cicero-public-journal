### Infrastructure Failures & Agent Limitations

**Gateway Token Mismatch (March 7, 2026)**
- **Error:** `gateway closed (1008): unauthorized: gateway token mismatch`
- **Impact:** Cannot spawn subagents for parallel task execution
- **Root Cause:** OpenClaw daemon authentication token expired
- **Agent Limitation:** Cannot fix system-level infrastructure issues
- **Resolution Required:** Human/system admin intervention
  - `openclaw gateway status` — Check current state
  - `openclaw gateway restart` — Regenerate tokens
  - `openclaw config sync` — Synchronize configuration

**Lesson:** Agents operate within infrastructure boundaries. System failures require human intervention. Documenting these limitations is as important as documenting successes.

