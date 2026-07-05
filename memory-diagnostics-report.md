# Memory System Diagnostics Report
**Date:** 2026-07-05  
**Issue:** Memory searches failing with `openai embeddings failed: 401 { "error": { "message": "Incorrect API key provided..." } }`

---

## Executive Summary

The embedding API key is **VALID and working correctly** when tested directly. The 401 errors are likely occurring in a different context - possibly during runtime when the system attempts to generate NEW embeddings for fresh content. The existing memory index (250 chunks) is intact and functional.

---

## 1. Root Cause Analysis

### ✅ API Key Status: VALID
- **Location:** `~/.openclaw/credentials/openai-api-key.txt`
- **Key Length:** 164 characters (valid format)
- **Direct API Test:** ✅ SUCCESS - Returns 1536-dimension embeddings
- **Status Code:** 200 OK

### ✅ Memory Database Health: GOOD
- **Database:** `~/.openclaw/memory/main.sqlite` (41MB)
- **Integrity Check:** PASSED (`ok`)
- **Total Chunks:** 250
- **Vector Embeddings:** 250 (100% coverage - no orphans)
- **Embedding Cache:** 697 entries
- **Files Indexed:** 73

### ⚠️ Configuration Gap Identified

**The `memory-core` plugin has an EMPTY configuration:**
```json
"memory-core": {
  "config": {}
}
```

This means the memory system may not have explicit embedding provider configuration and could be:
1. Falling back to default behavior that uses a different API key path
2. Attempting to use environment variables that aren't set
3. Using a cached/stale credential reference

### 🔍 Key Evidence

The database meta table shows:
```
model: text-embedding-3-small
provider: openai
providerKey: cdd3dd30cf9146f3be11ef9ef4439b052882c5598f01053b63b46c51a0d1664c
```

This `providerKey` is a **hash**, not the actual API key. The system uses this to look up the actual key at runtime.

---

## 2. Likely Root Causes

### Primary Hypothesis: Runtime Key Resolution Failure
The 401 errors occur when:
1. The memory system tries to embed NEW content (not cached)
2. It looks up the API key using the `providerKey` hash
3. The key resolution fails or returns an invalid/expired key

### Secondary Hypothesis: Stale Embedding Cache
The `embedding_cache` table has 697 entries. If the cache lookup logic has a bug, it might be:
- Missing cache hits and making unnecessary API calls
- Using wrong cache keys causing repeated embedding requests

### Tertiary Hypothesis: Extension/Plugin Issue
- The `lossless-claw` extension is symlinked: `~/.openclaw/plugin-skills/lossless-claw -> /home/ubuntu/.openclaw/npm/projects/martian-engineering-lossless-claw-fde018f0ba/node_modules/@martian-engineering/lossless-claw/skills/lossless-claw`
- There's a `.bak` version in extensions: `lossless-claw.bak`
- Possible version mismatch or stale plugin state

---

## 3. Immediate Workarounds

### Option A: Force Keyword-Only Search (Bypass Embeddings)
When memory search fails, the system should fall back to FTS (Full-Text Search). The database has:
- `chunks_fts` virtual table (FTS5)
- `unicode61` tokenizer configured

**Workaround:** Modify queries to use `corpus=memory` with `memory_get` instead of `memory_search` when embeddings fail.

### Option B: Environment Variable Override
Set the OpenAI API key as an environment variable:
```bash
export OPENAI_API_KEY=$(cat ~/.openclaw/credentials/openai-api-key.txt)
```

Then restart OpenClaw.

### Option C: Re-index with Fresh Credentials
If the providerKey hash is stale, re-indexing will regenerate it:
```bash
# Backup first
cp ~/.openclaw/memory/main.sqlite ~/.openclaw/memory/main.sqlite.bak.$(date +%Y%m%d)

# Trigger re-index (via OpenClaw CLI or restart)
```

---

## 4. Recommended Permanent Fixes

### Fix 1: Configure memory-core Plugin
Add explicit embedding configuration to `~/.openclaw/openclaw.json`:

```json
"memory-core": {
  "config": {
    "embedding": {
      "provider": "openai",
      "model": "text-embedding-3-small",
      "apiKeyPath": "~/.openclaw/credentials/openai-api-key.txt"
    }
  }
}
```

### Fix 2: Add Embedding Failure Fallback
Implement graceful degradation in the memory search pipeline:
1. Try embedding-based search first
2. On 401/embedding failure, automatically fall back to FTS
3. Log the failure for monitoring

### Fix 3: Credential Refresh Mechanism
Add a cron job or heartbeat check to verify embedding API key validity:
```bash
# Add to crontab or heartbeat
python3 -c "
import requests
import sys
with open('~/.openclaw/credentials/openai-api-key.txt') as f:
    key = f.read().strip()
resp = requests.post('https://api.openai.com/v1/embeddings',
    headers={'Authorization': f'Bearer {key}'},
    json={'input': 'test', 'model': 'text-embedding-3-small'},
    timeout=10)
sys.exit(0 if resp.status_code == 200 else 1)
"
```

### Fix 4: Lossless-Claw Integration
The `lossless-claw` plugin is already configured as the `contextEngine`. Ensure it's properly handling embedding failures:
- Check `/lossless` or `/lcm` command output
- Run `/lossless doctor` for diagnostics

---

## 5. Monitoring Recommendations

### Add to Heartbeat Checks
Add embedding health check to `HEARTBEAT.md`:
```markdown
## Embedding Health Check
- [ ] Test OpenAI embeddings API
- [ ] Check memory search functionality
- [ ] Verify embedding cache hit rate
```

### Log Analysis
Monitor for these patterns:
```bash
grep -i "embedding\|401\|Incorrect API key" ~/.openclaw/logs/*.log
```

---

## 6. Files Examined

| File | Status | Notes |
|------|--------|-------|
| `~/.openclaw/openclaw.json` | ✅ Read | memory-core config is empty |
| `~/.openclaw/config/lcm.yaml` | ✅ Read | LCM config OK |
| `~/.openclaw/memory/main.sqlite` | ✅ Validated | 250 chunks, all embedded |
| `~/.openclaw/credentials/openai-api-key.txt` | ✅ Valid | API test passed |
| `~/.openclaw/plugin-skills/lossless-claw/` | ✅ Symlink valid | Skill available |

---

## 7. Next Steps

1. **Immediate:** Try Option B (environment variable) as quick fix
2. **Short-term:** Implement Fix 1 (memory-core configuration)
3. **Medium-term:** Add Fix 2 (fallback mechanism) and Fix 3 (monitoring)
4. **Verify:** Run `memory_search` test after each fix

---

## Diagnostic Commands for Future Use

```bash
# Test API key directly
python3 -c "import requests; key=open('~/.openclaw/credentials/openai-api-key.txt').read().strip(); r=requests.post('https://api.openai.com/v1/embeddings', headers={'Authorization':f'Bearer {key}'}, json={'input':'test','model':'text-embedding-3-small'}); print(f'Status: {r.status_code}')"

# Check memory DB health
sqlite3 ~/.openclaw/memory/main.sqlite "PRAGMA integrity_check;"

# Count chunks vs embeddings
sqlite3 ~/.openclaw/memory/main.sqlite "SELECT (SELECT COUNT(*) FROM chunks) as chunks, (SELECT COUNT(*) FROM chunks_vec_rowids) as vectors;"

# Check LCM status
openclaw plugin list | grep -i memory
```
