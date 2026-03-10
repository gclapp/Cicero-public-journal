# OpenClaw Multi-Agent Setup & Mission Control Dashboard
## Complete Guide for Geoff

---

## PART 1: Multi-Agent Setup in OpenClaw

### Overview
OpenClaw supports multiple agents through **subagents** — child agents spawned from a parent (me) to handle parallel tasks. This lets you run many tasks simultaneously without overwhelming the main session.

### How It Works

**Parent Agent (Main Session - Me):**
- Your primary interface
- Orchestrates subagents
- Maintains main context/memory
- Handles high-level decisions

**Subagents (Child Sessions):**
- Spawned for specific tasks
- Run in isolation
- Can use cheaper models
- Report back to parent
- Auto-terminate when done

### Best Practices

#### 1. **Use Subagents for Parallel Tasks**
```
Good for subagents:
- Research tasks (multiple topics simultaneously)
- Data processing (batch jobs)
- Content generation (multiple articles)
- Monitoring (different data sources)
- Testing (multiple scenarios)

NOT for subagents:
- Tasks requiring your direct input
- Real-time conversation
- Tasks needing continuous context
```

#### 2. **Model Selection Strategy**
```yaml
Parent Agent (Me): 
  model: moonshot/kimi-k2.5 (high quality)
  
Subagents:
  model: gpt-4o-mini or kimi-k2.5 (cheaper, faster)
  # Configure via: agents.defaults.subagents.model
```

#### 3. **Clear Task Definition**
Each subagent should have:
- Specific, bounded scope
- Clear success criteria
- Defined output format
- Time limits

#### 4. **Communication Pattern**
```
Parent (Me) → Subagent: "Research X, return summary"
Subagent → Parent: Results + status
Parent → You: Consolidated report
```

### Setting Up Multiple Agents

#### Option A: Simple Subagent Spawning (Recommended for Start)

**From our main session, I can spawn subagents:**
```javascript
// Example: Spawn 3 research subagents simultaneously
sessions_spawn({
  task: "Research AI automation agencies pricing models",
  runtime: "subagent",
  mode: "run",
  model: "gpt-4o-mini"  // Cheaper model
})
```

**Configuration in `~/.openclaw/config.yaml`:**
```yaml
agents:
  defaults:
    subagents:
      model: gpt-4o-mini  # Cheaper for subagents
      maxConcurrent: 5     # Limit parallel subagents
      timeout: 300         # 5 minute timeout
```

#### Option B: Department-Based Structure (Advanced)

Create specialized agents for different functions:

```yaml
# ~/.openclaw/agents.yaml
departments:
  BUSINESS:
    - lead-gen-agent
    - content-agent
    - newsletter-agent
  
  INTEL:
    - competitor-monitor
    - market-researcher
    
  PERSONAL:
    - travel-planner
    - calendar-manager
    - health-tracker
```

Each department agent has:
- Specific tools (e.g., BUSINESS gets email, calendar)
- Specialized memory
- Different model preferences

### Monitoring Subagents

**From main session, I can:**
```bash
# List active subagents
subagents list

# Check specific subagent
subagents status <agent-id>

# Kill stuck subagent
subagents kill <agent-id>

# Send message to subagent
sessions_send <session-key> "message"
```

### Cost Optimization

| Agent Type | Model | Cost/1K tokens | Use Case |
|------------|-------|----------------|----------|
| Parent (Me) | kimi-k2.5 | ~$0.015 | Complex reasoning, orchestration |
| Subagent | gpt-4o-mini | ~$0.0006 | Research, data processing |
| Subagent | kimi-k2.5 | ~$0.003 | Tasks needing higher quality |

**Example savings:**
- 10 research tasks @ kimi-k2.5: $15
- 10 research tasks @ gpt-4o-mini: $0.60
- **Savings: 96%**

---

## PART 2: Mission Control Dashboard Setup

### What Is Mission Control?

A web-based dashboard that shows:
- Real-time agent status
- Active tasks and queues
- System resources (CPU, memory, GPU)
- Cost tracking
- Session history
- Cron job monitoring

### Free Options

#### Option 1: robsannaa/openclaw-mission-control (Recommended)

**Features:**
- 100% local (no cloud)
- Real-time agent monitoring
- Chat with agents
- Schedule jobs
- Track costs
- Manage memory
- No configuration needed

**Installation:**
```bash
# Clone the repository
git clone https://github.com/robsannaa/openclaw-mission-control.git
cd openclaw-mission-control

# Install dependencies
npm install

# Start the dashboard
npm start

# Access at http://localhost:3000
```

**What you'll see:**
- Agent status (online/offline)
- Active sessions
- Recent completions
- Cost tracking
- System health

#### Option 2: Existing Mission Control Dashboard (Already Installed!)

I found you already have this installed:
```
/home/ubuntu/.openclaw/workspace/skills/mission-control-dashboard/
```

**To start it:**
```bash
cd /home/ubuntu/.openclaw/workspace/skills/mission-control-dashboard
npm install  # If not already done
node server.js

# Access at http://localhost:3000
# Default login: admin / admin123
```

**Features:**
- 13 department structure
- System monitoring (CPU, memory, GPU)
- Task assignment
- Agent status tracking
- Beautiful cream/beige UI

### Setting Up Mission Control (Step-by-Step)

#### Step 1: Start the Dashboard

```bash
cd /home/ubuntu/.openclaw/workspace/skills/mission-control-dashboard

# Check if dependencies installed
if [ ! -d "node_modules" ]; then
  npm install
fi

# Start server
node server.js
```

#### Step 2: Configure Environment

```bash
cp .env.example .env

# Edit .env
nano .env
```

**Set these values:**
```env
PORT=3000
ADMIN_USERNAME=geoff
ADMIN_PASSWORD=your_secure_password
JWT_SECRET=random_string_here
```

#### Step 3: Access Dashboard

Open browser to: `http://localhost:3000`

Login with credentials from .env

#### Step 4: Configure Agents

Edit `agents.json` to match your setup:
```json
{
  "departments": {
    "BUSINESS": {
      "name": "Business Ventures",
      "emoji": "💼",
      "agents": [
        {
          "id": "lead-gen-agent",
          "name": "Lead Gen Agent",
          "emoji": "🎯",
          "status": "active"
        },
        {
          "id": "newsletter-agent",
          "name": "Newsletter Agent",
          "emoji": "📰",
          "status": "active"
        }
      ]
    },
    "PERSONAL": {
      "name": "Personal Assistant",
      "emoji": "🏠",
      "agents": [
        {
          "id": "cicero-main",
          "name": "Cicero (Main)",
          "emoji": "🏛️",
          "status": "online"
        }
      ]
    }
  }
}
```

#### Step 5: Set Up Auto-Start (Optional)

Using PM2:
```bash
npm install -g pm2

pm2 start server.js --name mission-control
pm2 startup
pm2 save

# Now it starts automatically on boot
```

### What You'll See in Mission Control

**Dashboard View:**
```
┌─────────────────────────────────────────┐
│  🎛️ MISSION CONTROL                    │
├─────────────────────────────────────────┤
│                                         │
│  💼 BUSINESS                            │
│    🎯 Lead Gen Agent      [ONLINE]      │
│    📰 Newsletter Agent    [ACTIVE]      │
│                                         │
│  🏠 PERSONAL                            │
│    🏛️ Cicero (Main)       [ONLINE]      │
│                                         │
│  📊 SYSTEM RESOURCES                    │
│    CPU: 23%  Memory: 45%  Disk: 60%     │
│                                         │
│  💰 COSTS TODAY: $2.34                  │
│                                         │
└─────────────────────────────────────────┘
```

**Agent Detail View:**
- Current task
- Session history
- Token usage
- Last activity
- Tools available

### Integration with OpenClaw

Mission Control reads from OpenClaw's:
- Session files
- Memory files
- Logs
- Config

**No separate database needed** — it's a window into your existing OpenClaw setup.

---

## PART 3: Recommended Setup for You

### Phase 1: Start Simple (This Week)

1. **Start Mission Control Dashboard**
   ```bash
   cd /home/ubuntu/.openclaw/workspace/skills/mission-control-dashboard
   node server.js
   ```

2. **Access at http://localhost:3000**

3. **Configure your departments:**
   - BUSINESS (lead gen, newsletter, content)
   - PERSONAL (me/Cicero, travel, health)

### Phase 2: Add Subagents (Next Week)

1. **Configure subagent defaults:**
   ```yaml
   # ~/.openclaw/config.yaml
   agents:
     defaults:
       subagents:
         model: gpt-4o-mini
         maxConcurrent: 5
   ```

2. **Start using subagents for:**
   - Research tasks
   - Data processing
   - Content generation

### Phase 3: Scale (Month 2)

1. **Create specialized agents:**
   - Lead Gen Agent (full-time)
   - Newsletter Agent (daily)
   - Research Agent (on-demand)

2. **Set up auto-spawning:**
   - Cron jobs spawn subagents
   - Mission Control monitors
   - You review results

---

## Next Steps

**Want me to:**
1. **Start Mission Control now?** (I can launch it)
2. **Create subagent templates?** (For common tasks)
3. **Set up department structure?** (Configure agents.json)
4. **Show example subagent usage?** (Spawn a test agent)

**Commands to remember:**
```bash
# Start Mission Control
cd /home/ubuntu/.openclaw/workspace/skills/mission-control-dashboard && node server.js

# List subagents
subagents list

# Spawn subagent
sessions_spawn --runtime subagent --task "research task"
```

---

*Document: multi-agent-mission-control-guide.md*  
*Created: March 7, 2026*
