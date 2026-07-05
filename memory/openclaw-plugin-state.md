# OpenClaw Plugin State

Last updated: 2026-07-05 (voice-call updated to 2026.6.11 and enabled)

## Pinned Plugin Versions

| Plugin | Version | Install Path | Integrity | Notes |
|--------|---------|--------------|-----------|-------|
| brave-plugin | 2026.6.11 | `npm/projects/openclaw-brave-plugin-...-f5bcc31fbe` | ✅ `sha512-FclcOH2g4E4Lt9fEViJgnjDRG4JVnG9yODjalj0/+qtMdCSKDWxlkrpS5kakDGzwhqy9+CiioczZQW0AtoWdOA==` | Web search provider |
| codex | 2026.6.10-beta.2 | `npm/projects/openclaw-codex-...-6c4cfad2cd` | ✅ `sha512-waT6Lgff2H5y378GCftY1D8mWA8krwgGeM0mgbXsisqGlqgrF6UBdYvjOXjwPqTIyYtpq7GgchA2ybiOqlwOYw==` | Coding agent harness |
| moonshot-provider | 2026.6.11 | `npm/projects/openclaw-moonshot-provider-4617b6c201` | ✅ `sha512-Ct6yzxIqhsW1+YssdYYAoE8OqyaQ+7tUvH9VJ0SyT6hxa+1eirZ9kZpZcFOKZsdcCS2KlrnxzBNgSLPXhXSJaQ==` | Kimi model provider |
| voice-call | 2026.6.11 | `npm/projects/openclaw-voice-call-d0fedeaf18` | ✅ `sha512-fB2sMqBtBskmVZIgnLgquOiz7KwDiSzfT6lce7dinMh...` | Voice calling (ENABLED) |
| whatsapp | 2026.6.11 | `npm/projects/openclaw-whatsapp-...-8e295eb8d8` | ✅ Pinned | WhatsApp channel |
| lossless-claw | 0.11.2 | `plugin-skills/lossless-claw` (symlink) | ✅ `sha256:270338058a774f33` | Context/memory plugin |

## Plugin Configuration (openclaw.json)

```json
{
  "brave": { "enabled": true },
  "codex": { "enabled": true },
  "moonshot": { "enabled": true },
  "voice-call": { "enabled": true },
  "whatsapp": { "enabled": false },
  "lossless-claw": { "enabled": true, "config": { ... } }
}
```

## Cleanup History

### 2026-07-05: Plugin Metadata Cleanup
- **Removed**: Broken codex install `openclaw-codex-8902d781d4` (version 2026.6.9, empty node_modules)
- **Archived**: Old extensions backup `extensions/lossless-claw.bak/` to `archive/extensions/`
- **Status**: All remaining plugins verified healthy with npm integrity hashes

### 2026-07-05: Voice-Call Update
- **Updated**: voice-call 2026.5.20 → 2026.6.11
- **Enabled**: voice-call plugin and skill in openclaw.json
- **Integrity**: `sha512-fB2sMqBtBskmVZIgnLgquOiz7KwDiSzfT6lce7dinMh...`
- **Backup**: `~/.openclaw/config/backups/openclaw.json.voice-call-enable.20260705-184415`

## Action Items

1. ~~voice-call~~: ✅ Updated to 2026.6.11 and enabled
2. **codex**: Consider updating from beta.2 to stable 2026.6.10+ when available
3. **Regular audit**: Check for plugin updates quarterly

## Verification Commands

```bash
# Check plugin health
for dir in ~/.openclaw/npm/projects/*/; do
  cd "$dir" && npm ls 2>/dev/null | head -2
done

# Check integrity hashes
cat package-lock.json | jq '.packages["node_modules/@openclaw/<plugin>"].integrity'
```
