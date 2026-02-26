# TOOLS.md - Local Notes

## TTS Configuration
- **Provider:** ElevenLabs
- **Default Voice:** George (ID: JBFqnCBsd6RMkjVDRZzb)
- **Voice Description:** Warm, captivating storyteller
- **API Key:** ✅ Configured (ELEVENLABS_API_KEY environment variable)
- **Script:** /home/ubuntu/.openclaw/workspace/scripts/elevenlabs_tts.py

## ElevenLabs Voice Settings
- **Model:** eleven_multilingual_v2
- **Stability:** 0.5
- **Similarity Boost:** 0.75

## Usage
```bash
python3 scripts/elevenlabs_tts.py "Your text here"
```

---

## Cameras
- (Add camera names/locations as needed)

## SSH
- (Add SSH hosts/aliases as needed)

## Skill Status

### ✅ Ready
- **voice-call** — ✅ Twilio configured (+1 650 600 0919), tested and working
- **blogwatcher** — Installed, needs RSS feeds configured
- **weather** — Ready
- **whoop** — Installed and configured
- **SAG (TTS)** — ✅ ElevenLabs API configured, tested and working
- **opentable** — Built and ready (needs API credentials to activate)
  - Search restaurants by location, cuisine, price, time
  - Make/cancel/view reservations
  - Find nearby restaurants
  - Share reservations (WhatsApp, SMS, Email, OpenTable)

### ⏳ Pending Setup
- **Whoop OAuth** — Need Geoff to create dev app
- **Blogwatcher** — RSS feeds to configure
- **OpenTable API** — Need credentials to activate:
  ```bash
  mkdir -p ~/.openclaw/config
  echo '{"api_key": "YOUR_KEY"}' > ~/.openclaw/config/opentable.json
  ```

---

Add whatever helps you do your job. This is your cheat sheet.