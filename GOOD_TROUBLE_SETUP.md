# 🚀 Good Trouble Setup — Complete

**Date:** May 28, 2026  
**Status:** ✅ Phase 1 Complete — Foundation Laid

---

## 1. ✈️ FlightAware + Aero (Travel Bot)

### What's Been Created
- **Agent:** `travel-bot` (Aero)
- **Location:** `/home/ubuntu/.openclaw/workspace/agents/travel-bot/`
- **Identity:** Elite travel concierge & flight intelligence
- **Model:** GPT-4o

### Files Created
```
agents/travel-bot/
├── SOUL.md              # Aero's personality & philosophy
├── AGENTS.md            # Technical configuration
├── config.json          # Settings & preferences
└── flight_monitor.py    # Core FlightAware integration
```

### Capabilities
- Real-time flight tracking via FlightAware AeroAPI v4
- Delay/cancellation alerts with priority levels (🔴🟡🟢)
- Proactive rebooking recommendations
- Airport & weather intelligence
- Ground transport coordination
- Greta (dog) care coordination for travel
- Full travel briefing generation

### Next Steps
1. **Get FlightAware API key** from https://flightaware.com/commercial/aeroapi/
2. Run setup: `python3 agents/travel-bot/flight_monitor.py setup YOUR_API_KEY`
3. Test: `python3 agents/travel-bot/flight_monitor.py status DL123`
4. Create cron job for continuous monitoring

---

## 2. 🫀🤖 Vitus & Aero as Separate, Addressable Bots

### Agent Registry

| Agent | ID | Purpose | Model | Workspace |
|-------|-----|---------|-------|-----------|
| **Cicero** | main | General coordination | GPT-4o | `/workspace` |
| **Vitus** | vitus | Health & fitness coach | GPT-4o | `/agents/health-agent` |
| **Aero** | travel-bot | Travel intelligence | GPT-4o | `/agents/travel-bot` |

### How to Spawn Agents

```python
# Spawn Vitus for health tasks
sessions_spawn(
    task="Analyze Geoff's HRV trend this week",
    agentId="vitus",
    taskName="hrv_analysis"
)

# Spawn Aero for travel tasks
sessions_spawn(
    task="Monitor flight DL123 LAX→JFK on June 15",
    agentId="travel-bot",
    taskName="monitor_dl123"
)
```

### Configuration Updated
- ✅ Added to `openclaw.json` agents.entries
- ✅ Each agent has dedicated workspace
- ✅ Each agent loads its own SOUL.md
- ✅ Both use GPT-4o for optimal performance

---

## 3. 🧠 OpenAI as Primary, Kimi as Backup

### Model Stack (New Priority Order)

| Priority | Model | Alias | Provider | Cost (in/out per 1M) |
|----------|-------|-------|----------|---------------------|
| 1️⃣ | **GPT-4o** | GPT-4o | OpenAI | $2.50 / $10.00 |
| 2️⃣ | **GPT-4o Mini** | GPT-4o Mini | OpenAI | $0.15 / $0.60 |
| 3️⃣ | **Kimi K2.5** | Kimi | Moonshot | Free |

### Configuration Changes
```json
"agents": {
  "defaults": {
    "model": {
      "primary": "openai/gpt-4o",
      "fallbacks": ["openai/gpt-4o-mini", "moonshot/kimi-k2.5"]
    }
  }
}
```

### What This Means
- **Primary:** All reasoning now uses GPT-4o (best quality)
- **Fallback 1:** If GPT-4o fails, uses GPT-4o Mini (fast/cheap)
- **Fallback 2:** If both fail, uses Kimi (free backup)
- **Cost:** Higher quality but will incur OpenAI API costs

### Next Steps
1. **Verify OpenAI API key** is in `~/.openclaw/credentials/` or env
2. **Monitor usage** — track costs in OpenAI dashboard
3. **Set budget alerts** if desired

---

## 4. 📚 Obsidian Second Brain

### Vault Structure Created

```
obsidian/
├── home/                  # OpenAI Home vault
│   └── README.md
├── work/                  # OpenAI Work vault
│   └── README.md
└── openclaw/              # OpenClaw system vault
    ├── README.md          # Main index
    └── AGENTS.md          # Agent registry
```

### Configuration
- ✅ Obsidian skill enabled in `openclaw.json`
- ✅ 3 vaults configured with paths
- ✅ OpenClaw set as default vault

### How to Use
```python
# From any agent, access Obsidian
# (Skill provides read/write capabilities)
```

### Next Steps
1. **Install Obsidian app** on desktop/mobile
2. **Open vault folders** in Obsidian
3. **Sync** using Obsidian Sync or Git
4. **Add content** — start documenting in the vaults

---

## 📋 Summary Checklist

### ✅ Completed
- [x] Aero agent created with full identity (SOUL.md)
- [x] FlightAware integration code written
- [x] Agent registry updated (Vitus + Aero)
- [x] OpenAI set as primary model
- [x] Fallback chain configured (GPT-4o → GPT-4o Mini → Kimi)
- [x] Obsidian skill enabled
- [x] 3 vaults created with initial structure
- [x] Configuration saved to `openclaw.json`

### ⏳ Pending (Need Your Input)
- [ ] FlightAware API key
- [ ] OpenAI API key verification
- [ ] Obsidian app installation
- [ ] Testing agent spawning
- [ ] Setting up monitoring cron jobs

---

## 🎯 What You Can Do Now

### Test the New Setup

```bash
# 1. Test Aero (once FlightAware key is added)
cd /home/ubuntu/.openclaw/workspace
python3 agents/travel-bot/flight_monitor.py status DL123

# 2. Check configuration
openclaw config get agents

# 3. View agent list
openclaw agents list
```

### From Chat, Try Spawning

Just say:
- "Spawn Vitus to analyze my sleep data"
- "Have Aero check on my upcoming flight"
- "Switch to GPT-4o Mini for this quick task"

---

## 🚀 Phase 2 Ideas

When you're ready for more trouble:

1. **Automated Flight Monitoring**
   - Cron job to check calendar for flights
   - Auto-spawn Aero 24h before travel
   - Telegram alerts for delays/cancellations

2. **Agent Collaboration**
   - Vitus + Aero coordination (travel health tips)
   - Multi-agent briefings
   - Agent-to-agent handoffs

3. **Enhanced Intelligence**
   - Weather impact analysis
   - Connection risk scoring
   - Loyalty program optimization

4. **Voice Integration**
   - Call Aero for flight updates
   - Voice-activated travel briefings

---

**Ready for the next phase?** Just say the word. 🏛️✈️🫀
