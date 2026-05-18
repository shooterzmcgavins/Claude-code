# AI Workspace — Operational Memory
> Compressed session intelligence. Load this before scanning the repo.

---

## User Profile

### Communication Style
- Direct, technical — skip preamble and explanation of obvious things
- Concise responses preferred; detailed only when debugging
- No emojis in responses or code
- Markdown output is fine

### Workflow Preferences
- Spawn parallel agents for independent backend/frontend work
- Commit and push at the end of every major task
- Read every file before editing — never edit blind
- Use `git status` + `git log --oneline` to orient before committing
- Branch: always `claude/openclaw-alternative-DJEL2`

### What the User Cares About
- **Cost control** — local Ollama first, Anthropic optional; no token burn
- **Observability** — every action logged, visible in dashboard
- **Interactive, not autonomous** — human always in the loop
- **Maintainability** — readable code, markdown-based config, no magic
- **Aesthetic** — cyberpunk/SOC dashboard, dark theme, compact `text-xs` UI

---

## Architecture Decisions (Stable)

### Stack
- **Backend**: Python 3.11 + FastAPI + WebSockets + ThreadPoolExecutor
- **Frontend**: React 18 + Vite + TailwindCSS (dark, `bg-slate-900` base)
- **Memory**: Markdown + YAML frontmatter (Obsidian-compatible)
- **Machine state**: JSON only (events, settings, registry)
- **Agent execution**: synchronous threads via `ThreadPoolExecutor`
- **Async bridge**: `asyncio.run_coroutine_threadsafe(broadcast(data), _loop)` for WS from agent threads
- **Approval blocking**: `threading.Event.wait(timeout=300)` — agent thread blocks until user acts in browser

### Provider Design
- **Default**: Ollama (`qwen2.5-coder:7b`)
- **Optional**: Anthropic (requires `ANTHROPIC_API_KEY`)
- Config is a mutable dataclass — settings page writes to `workspace/state/settings.json` and mutates live config (no restart needed)
- Provider switching is live: POST `/api/settings` → updates `state.config` in memory + persists

### Workspace Layout (canonical)
```
workspace/
├── agents/      # .md files — agent identity, system prompts, keywords
├── tasks/       # TASK-XXXXXX.md — frontmatter state + markdown body
├── reports/     # TASK-XXXXXX.md — completed output
├── memory/      # *.md — persistent cross-session knowledge
├── workflows/   # *.md — workflow definitions
├── chats/       # *.jsonl — chat session history
├── events/      # *.jsonl — append-only event log
├── vault/       # secure notes, config refs
├── scripts/     # generated automation scripts
├── dashboards/  # generated status views
├── logs/        # runtime logs
└── state/       # settings.json, machine state JSON
```

### Agent Identity
- Agents load from `workspace/agents/<name>.md` at runtime (no restart needed)
- Frontmatter: `name`, `role`, `model`, `tools`, `keywords`
- Body: `## System Prompt` section injected into every call
- Keyword list drives zero-cost routing (no API call if score ≥ 2)
- LLM fallback routing uses Haiku (Anthropic) or configured Ollama model

### Tool Architecture
- Tools are functions decorated with `@beta_tool` (Anthropic) or exposed as OpenAI function schema (Ollama)
- `run_shell` ALWAYS requires approval — no exceptions
- Approval flow: agent thread → `ApprovalManager.request_approval()` → broadcasts WS event → user acts in browser → `threading.Event.set()` unblocks agent
- File access restricted to workspace root (enforced in `web/routers/files.py:_resolve_safe()`)

---

## Engineering Lessons Learned

### TypeScript
- `Set.delete()` returns `boolean` — wrapping a subscribe unsubscribe in `useEffect` returns `() => boolean` which TS rejects as `EffectCallback` cleanup
- **Fix**: always wrap cleanup as `() => { this.listeners.delete(fn) }` not `() => this.listeners.delete(fn)`
- Vite builds even with TS errors (no `--noEmit` in build by default) — errors appear in output but don't block the build

### Windows / Git Bash
- `timeout /t 2` in `.bat` files fails in Git Bash — Git Bash resolves to `/usr/bin/timeout` (Unix coreutils), not Windows built-in
- **Fix**: use `ping -n 3 127.0.0.1 >nul 2>&1` for delays in batch files
- `start.bat` runs via `cmd.exe` even when launched from Git Bash — test both environments
- `%errorlevel%` is reset by `cd` in batch files — always capture into a variable (`set RESULT=%errorlevel%`) immediately after the command, before any `cd`
- `npm run build --silent` suppresses build errors from output — remove `--silent` from build step so TypeScript errors are visible; `--silent` on `npm install` is fine

### Python / FastAPI
- Agent threads are synchronous; FastAPI runs async. Bridge: capture event loop in `lifespan` via `asyncio.get_event_loop()`, store in `broadcaster._loop`, use `run_coroutine_threadsafe` from agent threads
- `state.py` module-level globals initialized by `state.init()` — all routers import from `state` directly (no dependency injection)
- Persisted settings loaded in two places: `lifespan` (server startup) and `_run_web` in `main.py` — both must apply to `state.config`

### Routing
- The `supervisor.py` route order: keyword score ≥ 2 → return immediately (free); score ≥ 1 AND LLM fallback fails → return best keyword match; default → "builder"
- Keyword lists live in agent `.md` frontmatter AND `agents/roles.py:DEFAULT_KEYWORDS` (fallback if .md missing)

---

## Mistakes to Avoid Repeating

| Mistake | What Happened | Prevention |
|---------|--------------|------------|
| Wrong architecture first | Built generic chatbot instead of OpenClaw-style workspace | Confirm scope before building |
| Provider default wrong | Default was `anthropic`, should be `ollama` | Always check `config.py` defaults first |
| Editing without reading | Agent wrote files without reading them first | Read before every edit |
| `() => boolean` cleanup | Subscribe return type broke 6 useEffect hooks | Always type cleanup as `() => void` |
| `timeout /t` in bat | Fails in Git Bash | Use `ping -n` for delays |
| `%errorlevel%` after `cd` | `cd` resets errorlevel — build check always passed | Capture `set RESULT=%errorlevel%` before `cd ..` |
| `--silent` on build step | Hid TS errors while reporting success | Only silence `npm install`, never `npm run build` |
| Not committing promptly | Large uncommitted changesets get lost | Commit after each major feature |
| Autonomous behavior | User explicitly rejected recursive loops | NO auto-running agents, NO scheduled polling |

---

## Things That Worked Well

- Parallel agents (backend + frontend split) — cut implementation time significantly
- API contracts defined before spawning agents — prevented coordination failures
- Keyword routing (zero-cost) before LLM fallback — keeps Ollama calls minimal
- `threading.Event` for approval blocking — clean, no polling
- Markdown frontmatter for tasks — human-readable AND machine-parseable, Obsidian-friendly
- `_resolve_safe()` path traversal prevention — simple and effective

---

## Safety Rules (Non-Negotiable)

- Shell commands NEVER auto-execute — always require explicit user approval
- No recursive autonomous agent loops
- No self-modifying systems
- No background scheduled polling
- No hidden API calls
- File manager restricted to workspace directory only

---

## UI/UX Conventions

- Base: `bg-slate-900`, borders: `border-slate-800`
- Accent: `text-cyan-400` (headers, active states)
- Success: `text-emerald-400`, Warning: `text-amber-400`, Error: `text-red-400`
- Agent color: `text-purple-400`
- All body text: `text-xs` (compact, dense)
- Headers: `text-sm font-bold uppercase tracking-widest`
- Two-panel layouts for browsing (list left, detail right)
- Live data via WebSocket — no polling in frontend
- WS client: singleton `wsClient` with auto-reconnect (exponential backoff to 15s)

---

## Environment

- **OS**: Windows (user runs Git Bash + Windows cmd)
- **Python**: 3.14.5
- **Node**: installed (version available)
- **Ollama**: installed locally
- **Repo**: `shooterzmcgavins/Claude-code`
- **Branch**: `claude/openclaw-alternative-DJEL2`
- **Remote**: `git push -u origin claude/openclaw-alternative-DJEL2`
- **Dev port**: 8000 (backend), 5173 (Vite dev server)
