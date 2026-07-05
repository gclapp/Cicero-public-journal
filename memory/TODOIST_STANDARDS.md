# Todoist Standards - How Cicero Creates Tasks

**Established:** May 14, 2026  
**Purpose:** Consistent, useful task structure for all future Todoist entries

---

## Required Structure (Geoff's Standard)

### 1. Nested Hierarchy

**Always use this 3-level structure:**

```
🏛️ Project Name (main parent in OpenClaw To-Do)
│
├── 💻 Phase 1: Name
│   ├── 🔧 Task 1
│   ├── 💎 Task 2
│   └── 📥 Task 3
│
├── 📱 Phase 2: Name
│   ├── 📲 Task 1
│   └── 📂 Task 2
│
└── 🚀 Phase 3: Name
    ├── 📝 Task 1
    └── ✅ Task 2
```

**Rules:**
- Main parent task lives in "OpenClaw To-Do" project
- Phases are subtasks of the main parent
- Individual tasks are subtasks of phases
- NEVER flat lists — always nested

**Phase emojis to use:**
- Phase 1: 💻 🏗️ 📝
- Phase 2: 📱 🔧 ⚙️
- Phase 3: 🚀 ✅ 🎯
- Phase 4+: 🎨 📊 🔮

### 2. Subtasks

Each phase parent has **actionable subtasks**:

```
💻 Phase 1: Work PC Setup
  ├─ Install Git on Work PC (Windows)
  ├─ Install Obsidian on Work PC
  ├─ Clone shared-inbox repo on Work PC
  └─ ...
```

**Subtask rules:**
- Start with verb (Install, Configure, Test, Create)
- Include URLs when relevant
- Keep under 60 characters
- One action per task

### 3. Emojis

**Use emojis consistently:**

| Context | Emoji |
|---------|-------|
| Work/PC | 💻 |
| Mobile | 📱 |
| Setup/Config | 🔧 |
| Testing | 🧪 |
| Documentation | 📝 |
| Completion | ✅ |
| Launch | 🚀 |
| Research | 🔍 |
| Meeting | 🤝 |
| Travel | ✈️ |
| Health | 🫀 |
| Learning | 📚 |

### 4. Descriptions

**Parent tasks MUST include:**

```markdown
Phase X: [Brief description of phase goal]

Files:
• [Relevant file/link 1]
• [Relevant file/link 2]

[ASCII art if helpful]

Resources:
• [URL 1]
• [URL 2]
```

### 5. ASCII Art (REQUIRED - Geoff's Preference)

**ALWAYS include ASCII art showing subtask structure in parent descriptions.**

**This is the exact format Geoff prefers:**

```
🏛️ Obsidian Setup
│
├── 💻 Phase 1: Work PC
│   ├── 🔧 Install Git
│   ├── 💎 Install Obsidian
│   ├── 📥 Clone shared-inbox repo
│   ├── 🔐 Configure Git auth
│   ├── 🔌 Install Obsidian Git plugin
│   └── 🧪 Test sync
│
├── 📱 Phase 2: Mobile
│   ├── 📲 Install Working Copy
│   ├── 📂 Clone repo
│   ├── 📂 Open vault in Obsidian
│   └── 🧪 Test sync
│
└── 🚀 Phase 3: Go Live
    ├── 📝 Capture first transcript
    ├── ✅ Verify Cicero responds
    ├── 📋 Create meeting template
    └── 💡 Create ideas template
```

**ASCII art rules:**
- Use tree structure with ├── and └──
- Indent subtasks with 4 spaces
- Show full hierarchy: Project → Phases → Tasks
- Include emojis in the tree
- Keep it clean and scannable
- ALWAYS show this in the top-level parent description

---

## Example: Complete Project

```
📁 Obsidian Setup (Project)
│
├─ 💻 Phase 1: Work PC Setup (P1)
│  ├─ Install Git on Work PC
│  ├─ Install Obsidian on Work PC
│  ├─ Clone shared-inbox repo
│  └─ Test sync
│
├─ 📱 Phase 2: Mobile Setup (P2)
│  ├─ Install Working Copy
│  └─ Test mobile sync
│
└─ 🚀 Phase 3: Go Live (P3)
   └─ Capture first transcript
```

---

## Monitoring Progress

**Cicero will:**

1. **Check Todoist daily** during check-ins
2. **Report progress** on phase completion
3. **Nudge on stalled phases** (>3 days no progress)
4. **Celebrate completions** 🎉

**Progress tracking:**
- Phase not started: ⚪
- Phase in progress: 🟡
- Phase complete: 🟢

---

## Priority Guidelines

| Priority | Use For | Emoji |
|----------|---------|-------|
| P1 | Blocking, this week | 🔴 |
| P2 | Important, next week | 🟠 |
| P3 | Nice to have | 🔵 |
| P4 | Backlog | ⚪ |

---

## Labels to Use

When relevant, add labels:
- `@work` - Work-related
- `@personal` - Personal tasks
- `@waiting` - Blocked on external
- `@quick` - < 15 min task
- `@deep` - Requires focus time

---

## What to Avoid

❌ Flat lists without phases  
❌ Vague task names  
❌ Missing descriptions on parents  
❌ No links to relevant files  
❌ Inconsistent emoji use  
❌ Tasks > 60 characters  

---

**Geoff's Preference Summary:**

| Element | Requirement |
|---------|-------------|
| **Structure** | Nested: Parent → Phases → Tasks |
| **Location** | "OpenClaw To-Do" project |
| **ASCII Art** | Tree view showing full hierarchy |
| **Emojis** | Every task gets an emoji |
| **Descriptions** | Step-by-step instructions + links |
| **Parent Desc** | Must show ASCII tree of all subtasks |

**This structure is non-negotiable for all future Todoist work.**

---

*Last updated: May 14, 2026*  
*Established by: Geoffrey Clapp*  
*Applies to: All future Todoist task creation*
