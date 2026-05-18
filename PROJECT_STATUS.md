# Project Status
> Load this at session start. Authoritative current state.

---

## Current Objective

Build and maintain a web-first, Ollama-default AI Engineering Workspace
inspired by OpenClaw — interactive human-in-the-loop, observable, local-first.

---

## Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.11 + FastAPI + uvicorn |
| Agent execution | ThreadPoolExecutor (sync threads) |
| Real-time | WebSockets + asyncio bridge |
| Frontend | React 18 + Vite + TailwindCSS |
| Memory | Markdown + YAML frontmatter |
| Machine state | JSON |

**Default provider**: Ollama (`qwen2.5-coder:7b`)
**Optional provider**: Anthropic (claude-sonnet-4-6 default)

---

## Completed Work

- [x] Multi-agent workspace: supervisor + 5 specialist agents
- [x] Markdown-based agent identity (edit `.md` → takes effect without restart)
- [x] Task system: TASK-XXXXXX.md with frontmatter + body
- [x] Approval system: shell commands require browser approval (blocking)
- [x] FastAPI backend with all routers
- [x] WebSocket real-time event broadcasting
- [x] React dashboard — 12 pages
- [x] Chat interface with agent routing + session persistence
- [x] File manager (browse/edit/delete workspace files)
- [x] Settings page with live config + persistence
- [x] Health check page (Ollama connectivity, model availability)
- [x] Task controls: cancel, retry, archive
- [x] `ARCHIVED` task status
- [x] Windows launchers: `start.bat`, `start.ps1`
- [x] Docker: `Dockerfile` + `docker-compose.yml` (Ollama profile)
- [x] PyInstaller spec for EXE packaging
- [x] Comprehensive README
- [x] Startup blockers fixed (TS cleanup type, Git Bash timeout, build status check)

---

## Current Dashboard Pages

| Page | Route | Status |
|------|-------|--------|
| Overview | `/` | ✓ |
| Chat | `/chat` | ✓ |
| Tasks | `/tasks` | ✓ with cancel/retry/archive |
| Agents | `/agents` | ✓ |
| Events | `/events` | ✓ live stream |
| Reports | `/reports` | ✓ |
| Files | `/files` | ✓ two-panel editor |
| Memory | `/memory` | ✓ |
| Models | `/models` | ✓ |
| Approvals | `/approvals` | ✓ blocking |
| Health | `/health` | ✓ with fix guidance |
| Settings | `/settings` | ✓ live + persisted |

---

## Known Issues

- No streaming responses in Chat (agent completes then result appears)
- No provider abstraction layer — Anthropic/Ollama paths are code-split inside `specialist.py`
- Platforms module (Slack/Discord/Telegram) untested with web mode
- PyInstaller EXE not yet tested end-to-end
- Frontend build TS errors: **fixed** (`ws.ts subscribe` now returns `() => void`)
- `start.bat` false-positive "[OK] Frontend built": **fixed** (errorlevel captured before `cd ..`)

---

## API Surface (key endpoints)

```
GET  /api/health          → Ollama + workspace status
GET  /api/settings        → current config
POST /api/settings        → update + persist config
GET  /api/tasks           → list tasks (?status=filter)
POST /api/tasks           → create task
POST /api/tasks/{id}/cancel
POST /api/tasks/{id}/retry
POST /api/tasks/{id}/archive
GET  /api/files           → list dir (?path=.)
GET  /api/files/read      → file content (?path=...)
POST /api/files/write     → save file
POST /api/files/delete    → delete
POST /api/files/create    → new file/dir
GET  /api/chat/sessions   → list chat sessions
POST /api/chat            → send message to agent
GET  /api/agents          → list agents
GET  /api/approvals/pending
POST /api/approvals/{id}/resolve
WS   /ws                  → event stream
```

---

## Current Priorities

1. Verify full local run on Windows with Ollama after `git pull` + clean rebuild (`del dashboard\dist` then `start.bat`)
2. Add streaming support to Chat (SSE or chunked WS events from agent)
3. Create a clean provider abstraction layer (`providers/base.py`, `providers/ollama.py`, `providers/anthropic.py`)
4. Add agent memory sidebar to Chat page (show what the agent has written to memory)
5. Add workflow runner — sequence of agent tasks from a `.md` definition

---

## Deferred Features

- Streaming responses (requires agent-side generator refactor)
- Provider abstraction layer (current split works but is verbose)
- Platform bots (Slack/Discord/Telegram) — deprioritized, web-first
- Self-healing retry logic in agents
- Task scheduling / cron-style triggers
- Collaborative multi-agent task chains
- EXE packaging testing on Windows

---

## Next Recommended Commands

```bash
# Start locally (Ollama must be running)
python main.py

# Or Windows launcher
./start.bat

# Pull recommended model first if needed
ollama pull qwen2.5-coder:7b

# Dev mode (hot reload frontend + backend)
# Terminal 1:
python main.py --web --port 8000
# Terminal 2:
cd dashboard && npm run dev
```

---

## Git

- **Repo**: `shooterzmcgavins/Claude-code`
- **Branch**: `claude/openclaw-alternative-DJEL2`
- **Latest commit**: `1fba072` — fix: capture build errorlevel before cd in start.bat
- **Push command**: `git push -u origin claude/openclaw-alternative-DJEL2`

---

## Bootstrap Prompt for Next Session

```
Read PROJECT_STATUS.md and feedback.md first.
Use them as authoritative context — do not scan the entire repo unless necessary.
Branch: claude/openclaw-alternative-DJEL2
Continue from Current Priorities in PROJECT_STATUS.md.
```
