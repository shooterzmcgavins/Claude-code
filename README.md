# AI Engineering Workspace

An interactive AI operations workspace inspired by OpenClaw — built for solo operators who want role-based AI agents, task tracking, persistent memory, and a browser-based Mission Control dashboard, **without** autonomous loops, runaway costs, or hidden API calls.

**Local-first by default.** Runs on Ollama (free, private). Anthropic is optional.

---

## Architecture

```
Python backend (FastAPI)  ←→  React dashboard (Vite + Tailwind)
         ↓                              ↑
   Agent system                   WebSocket
   Tool system                  Real-time events
   Task store (markdown)
   Memory (markdown)
         ↓
   workspace/ (files on disk)
```

| Layer | Technology | Purpose |
|-------|-----------|---------|
| Runtime | Python + FastAPI | Agent execution, API, WebSockets |
| Memory | Markdown + YAML frontmatter | Tasks, agents, memory, reports |
| UI | React + Vite + Tailwind | Mission Control dashboard |

---

## Quick Start

### Option 1 — Windows

```bat
start.bat
```

Or with PowerShell:

```powershell
.\start.ps1
```

Checks Python, Node, and Ollama; installs dependencies; builds the frontend; opens the browser automatically.

### Option 2 — Direct Python

```bash
pip install -r requirements.txt

# (Optional) Build the dashboard
cd dashboard && npm install && npm run build && cd ..

# Start — opens http://localhost:8000
python main.py
```

### Option 3 — Docker

```bash
# Anthropic provider (set ANTHROPIC_API_KEY in .env first)
docker compose up

# With bundled Ollama sidecar
docker compose --profile ollama up

# After first start with Ollama, pull a model:
docker compose exec ollama ollama pull qwen2.5-coder:7b
```

---

## Ollama Setup

Ollama is the **default provider** — free, local, private.

### 1. Install Ollama

**Linux / macOS:**
```bash
curl -fsSL https://ollama.ai/install.sh | sh
```

**Windows:** Download the installer from [ollama.ai](https://ollama.ai)

### 2. Pull a model

```bash
# Recommended for coding tasks (fast, capable)
ollama pull qwen2.5-coder:7b

# General purpose with strong reasoning
ollama pull qwen3:8b

# Lightweight and fast
ollama pull llama3.2:3b
```

### 3. Start Ollama

```bash
ollama serve
```

Ollama listens on `http://localhost:11434` by default.

### 4. Verify

Open the **Health** page in the dashboard (`http://localhost:8000/health`) — it shows Ollama connectivity and model availability with fix instructions if anything is wrong.

---

## Configuration

Copy `.env.example` to `.env`:

```bash
cp .env.example .env
```

### Key environment variables

| Variable | Default | Description |
|----------|---------|-------------|
| `PROVIDER` | `ollama` | `ollama` or `anthropic` |
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Ollama API base URL |
| `OLLAMA_MODEL` | `qwen2.5-coder:7b` | Model to use with Ollama |
| `ANTHROPIC_API_KEY` | _(empty)_ | Required only if `PROVIDER=anthropic` |
| `WORKSPACE_PORT` | `8000` | Web dashboard port |

Settings can also be changed live from the **Settings** page — they persist to `workspace/state/settings.json` and survive restarts.

---

## Dashboard Pages

| Page | Path | Description |
|------|------|-------------|
| Overview | `/` | Stats, recent events, provider status |
| Chat | `/chat` | Talk to agents, create tasks from conversation |
| Tasks | `/tasks` | View, filter, cancel, retry, archive tasks |
| Agents | `/agents` | Agent cards with editable system prompts |
| Events | `/events` | Live event stream with filtering |
| Reports | `/reports` | Completed task output |
| Files | `/files` | Browse and edit workspace files |
| Memory | `/memory` | View and edit persistent memory entries |
| Models | `/models` | Provider status and model list |
| Approvals | `/approvals` | Approve or reject shell command requests |
| Health | `/health` | System health check and setup guidance |
| Settings | `/settings` | Provider, model, and runtime configuration |

---

## Agent System

Agents load their identity from markdown files in `workspace/agents/`. Edit any `.md` file — changes take effect on the next task without restarting.

### Built-in agents

| Agent | Role | Default tools |
|-------|------|--------------|
| `supervisor` | Routes incoming tasks to specialists | _(routing only)_ |
| `builder` | Code, implementation, debugging | all |
| `research` | Web search, documentation, analysis | web + files |
| `planner` | Goals, roadmaps, specifications | files + memory |
| `monitor` | Logs, health checks, diagnostics | shell + files |
| `automation` | Scripts, pipelines, CI/CD | all |

### Agent file format

```markdown
---
name: builder
role: Software Engineer
model: sonnet
tools: all
keywords: [build, code, implement, fix, debug, test]
---

# Builder

## System Prompt

You are the builder agent — a skilled software engineer...

## Responsibilities

- Write, edit, and refactor code in any language

## Operational Rules

1. Always read_file before editing — never edit blind
```

The `keywords` list drives zero-cost routing (no API call). The `## System Prompt` section is sent to the model on every task.

---

## Task System

Tasks are markdown files in `workspace/tasks/TASK-XXXXXX.md`:

```markdown
---
id: TASK-A1B2C3
title: Build a CSV parser
status: complete
agent: builder
created_at: 2025-01-15T10:30:00
---

## Description

Build a CSV parser that handles quoted fields and newlines inside fields.

## Result

Created `csv_parser.py` with full RFC 4180 support. Tests pass.
```

### Task lifecycle

```
queued → in_progress → complete
                    → failed
                    → needs_approval  (waiting for shell approval)
(any terminal state) → archived
```

### Task controls

From the Tasks page detail panel:

- **Cancel** — marks in-progress tasks as failed immediately
- **Retry** — creates a new task with the same description, routes fresh
- **Archive** — hides completed/failed tasks from the default view

---

## Approval System

Shell commands **never run automatically**. Every `run_shell` call:

1. Pauses the agent thread
2. Shows the command in the **Approvals** page
3. Waits up to 5 minutes for your decision
4. Runs (or skips) based on your choice

The agent sees the result and continues. You stay in control.

---

## Tool System

| Tool | Description | Needs Approval |
|------|-------------|---------------|
| `read_file` | Read workspace files | No |
| `write_file` | Write workspace files | No |
| `list_files` | List directory contents | No |
| `run_shell` | Execute shell commands | **Yes** |
| `web_search` | DuckDuckGo search | No |
| `fetch_url` | Fetch a URL | No |
| `write_report` | Save a task report | No |
| `read_memory` | Read persistent memory | No |
| `write_memory` | Write persistent memory | No |

---

## File Manager

The **Files** page lets you browse and edit anything in the workspace directory from the browser:

- Navigate directories
- View and edit markdown, JSON, YAML, Python, shell scripts
- Create new files or directories
- Delete with confirmation

All paths are restricted to inside the workspace directory — no traversal outside.

---

## Workspace Structure

```
workspace/
├── agents/          ← Agent identity files (edit these to change behavior)
│   ├── supervisor.md
│   ├── builder.md
│   ├── research.md
│   ├── planner.md
│   ├── monitor.md
│   └── automation.md
├── tasks/           ← Task files (TASK-XXXXXX.md)
├── reports/         ← Completed task reports (TASK-XXXXXX.md)
├── memory/          ← Persistent cross-session knowledge (*.md)
├── workflows/       ← Workflow definitions (*.md)
├── chats/           ← Chat session history (*.jsonl)
├── events/          ← Append-only event log (*.jsonl)
├── vault/           ← Config references, secure notes
├── scripts/         ← Generated automation scripts
├── dashboards/      ← Generated status views
├── logs/            ← Runtime logs
└── state/           ← Machine state (settings.json, etc.)
```

This layout is **Obsidian-compatible** — open `workspace/` as a vault for rich editing, backlinks, and graph view.

---

## Windows Setup

### Prerequisites

| Tool | Where | Notes |
|------|-------|-------|
| Python 3.11+ | [python.org](https://python.org) | Add to PATH during install |
| Node.js 18+ | [nodejs.org](https://nodejs.org) | For frontend build |
| Ollama | [ollama.ai](https://ollama.ai) | Or use `PROVIDER=anthropic` |

### First run

```bat
start.bat
```

Handles everything automatically.

### Subsequent runs

```bat
start.bat
```

Or if dependencies are already installed:

```bat
python main.py
```

---

## EXE Packaging

Package as a standalone Windows executable:

```bash
pip install pyinstaller

# Build frontend first
cd dashboard && npm install && npm run build && cd ..

# Package
pyinstaller pyinstaller.spec
```

Output: `dist/AI-Workspace/AI-Workspace.exe`

The EXE bundles the Python runtime and pre-built frontend. Distribute the full `dist/AI-Workspace/` folder. The workspace directory is created next to the EXE on first run.

---

## Troubleshooting

### "Cannot connect to Ollama"

1. Check Ollama is installed: `ollama --version`
2. Start it: `ollama serve` (or check the system tray on Windows)
3. Verify the URL in Settings matches where Ollama is listening
4. Open the **Health** page for a detailed diagnostic

### "Model not found"

```bash
ollama pull qwen2.5-coder:7b
ollama list  # see what's available
```

### "ANTHROPIC_API_KEY not set"

Either add the key to `.env`, or switch to Ollama (Settings page or `PROVIDER=ollama` in `.env`).

### Frontend not loading

If `dashboard/dist/` is missing:

```bash
cd dashboard && npm install && npm run build
```

For development with hot-reload (separate terminal):

```bash
cd dashboard && npm run dev
# Access at http://localhost:5173
```

### WebSocket shows "disconnected"

The backend process has stopped. Restart `python main.py` and refresh the browser.

### Resetting the workspace

The workspace is plain files — delete whatever you need:

```bash
rm -rf workspace/       # full reset
rm workspace/tasks/*.md # clear tasks only
```

The workspace is recreated on next startup.

---

## Recovery

If something goes wrong:

1. **Check the Events page** — all agent actions are logged
2. **Check the Health page** — provider and model status
3. **Browse Files** — inspect task files and agent configs directly
4. **Edit agent .md files** — fix broken agent behavior without restarting
5. **Archive stuck tasks** — Tasks → detail → Archive

---

## Safety Design

This workspace is built for **human-in-the-loop operation**:

- Shell commands require explicit approval every time
- No recursive autonomous loops
- No self-modifying agent behavior
- No background scheduled agents
- All API calls visible in Events log
- All tool calls logged in real-time
- File access restricted to workspace directory

---

## Development

### Backend only

```bash
pip install -r requirements.txt
python main.py --web --port 8000
```

### Frontend dev server

```bash
cd dashboard
npm install
npm run dev  # http://localhost:5173 (proxies to :8000)
```

### Project layout

```
main.py              Entry point (defaults to web mode)
config.py            Configuration dataclass
core/
  markdown.py        Frontmatter parser (zero dependencies)
  task.py            Task model + markdown store
  events.py          Append-only event log
  workspace.py       Workspace directory layout
agents/
  base.py            Agent base class (Anthropic client)
  loader.py          Loads agent config from .md files
  roles.py           Default keywords for routing
  supervisor.py      Task routing logic
  specialist.py      Task execution (Anthropic + Ollama paths)
tools/
  shell.py           Shell execution + approval gate
  files.py           File read/write tools
  web.py             Web search + URL fetch
  workspace_tools.py Report, memory, init tools
web/
  server.py          FastAPI app + lifespan
  state.py           Shared singletons (config, store, etc.)
  broadcaster.py     Thread-safe WebSocket broadcast
  approval.py        Approval request manager
  chat_history.py    Chat session persistence (JSONL)
  ws.py              WebSocket endpoint
  routers/
    tasks.py         Task CRUD + cancel/retry/archive
    agents.py        Agent listing
    chat.py          Chat + session management
    events.py        Event log API
    reports.py       Report listing + content
    memory.py        Memory read/write
    models_api.py    Provider + model info
    approvals.py     Approval queue management
    health.py        System health check
    settings.py      Runtime settings persistence
    files.py         File manager (browse/edit/delete)
dashboard/
  src/
    pages/           React page components
    components/      Shared UI (Layout, Sidebar, etc.)
    api.ts           Typed API client
    ws.ts            WebSocket auto-reconnect client
    types.ts         TypeScript interfaces
```

---

## License

MIT
