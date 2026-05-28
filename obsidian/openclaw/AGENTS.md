# Agent Registry

## Active Agents

### 🏛️ Cicero (Main)
- **ID:** main
- **Model:** GPT-4o (primary) → GPT-4o Mini → Kimi K2.5
- **Purpose:** General coordination, orchestration, user interface
- **Workspace:** /home/ubuntu/.openclaw/workspace

### 🫀 Vitus (Health)
- **ID:** vitus
- **Model:** GPT-4o
- **Purpose:** Health coaching, Whoop analysis, fitness guidance
- **Workspace:** /home/ubuntu/.openclaw/workspace/agents/health-agent
- **Spawn:** `sessions_spawn(task="...", agentId="vitus")`

### ✈️ Aero (Travel)
- **ID:** travel-bot
- **Model:** GPT-4o
- **Purpose:** Flight monitoring, travel intelligence, logistics
- **Workspace:** /home/ubuntu/.openclaw/workspace/agents/travel-bot
- **Spawn:** `sessions_spawn(task="...", agentId="travel-bot")`

## Agent Communication

### Delegation Pattern
```python
# From Cicero to specialized agent
sessions_spawn(
    task="Monitor flight DL123 LAX→JFK on June 15",
    agentId="travel-bot",
    taskName="monitor_dl123"
)

# From Cicero to Vitus
sessions_spawn(
    task="Analyze this week's HRV trend and recommend recovery protocol",
    agentId="vitus",
    taskName="hrv_analysis_week24"
)
```

### Results
Specialized agents report back through the session system. Results are captured in:
- Session transcripts
- Memory files (memory/YYYY-MM-DD.md)
- Agent-specific memory directories

## Agent Capabilities Matrix

| Capability | Cicero | Vitus | Aero |
|------------|--------|-------|------|
| General reasoning | ✅ | ❌ | ❌ |
| Health coaching | ❌ | ✅ | ❌ |
| Flight monitoring | ❌ | ❌ | ✅ |
| Calendar access | ✅ | ✅ | ✅ |
| Email sending | ✅ | ❌ | ❌ |
| Web search | ✅ | ✅ | ✅ |
| Whoop data | ✅ | ✅ | ❌ |
| FlightAware | ✅ | ❌ | ✅ |
