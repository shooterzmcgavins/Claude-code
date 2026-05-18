# AI Engineering Workspace

An interactive AI engineering workspace inspired by OpenClaw — persistent tasks, specialized agents, event logging, and role-based workflows — without the token burn.

## What it is

An ops console where you submit tasks in plain English. A supervisor routes each task to the right specialist agent (builder, research, planner, monitor, or automation). Each task is tracked, logged, and produces a report. Everything persists to disk between sessions.

```
╔══════════════════════════════════════════════╗
║        AI Engineering Workspace              ║
║  type a task, or /help for commands          ║
╚══════════════════════════════════════════════╝
  workspace: ./workspace  |  tasks: 4

> research the best Python async job queue libraries

  → routing to: research  [TASK-7A2B3C]

  research: I'll search for Python async job queue options...
  ↳ web_search('Python async job queue libraries 2025')
  ↳ fetch_url('https://...')
  ↳ write_report('TASK-7A2B3C', ...)

  ✓ TASK-7A2B3C complete  |  3 tool calls  |  ~$0.0012
  📄 report → workspace/reports/TASK-7A2B3C.md

> /status
  ✓ TASK-7A2B3C  complete     [research]    2026-05-18 10:23  research the best...
  ✓ TASK-4D5E6F  complete     [builder]     2026-05-18 09:11  add CSV export to...
```

## Cost strategy

| Model | $/1M in | $/1M out | Default use |
|-------|---------|----------|-------------|
| Haiku 4.5 | $1 | $5 | Supervisor routing |
| Sonnet 4.6 | $3 | $15 | All agent execution (default) |
| Opus 4.7 | $5 | $25 | `--model opus` only |

Cost controls:
- Supervisor routing uses **keyword matching first** (zero API cost), Haiku only as fallback
- Agents use **Sonnet by default** — fast enough for most tasks at 3x lower cost than Opus
- **Prompt caching** on all system prompts
- Each task is **scoped** — no shared context growing across unrelated tasks

## Setup

```bash
pip install -r requirements.txt
cp .env.example .env
# Add your ANTHROPIC_API_KEY
```

## Usage

```bash
# Interactive workspace REPL
python main.py

# One-shot task
python main.py "write a Dockerfile for a FastAPI app"

# Force a model
python main.py --model opus "architect a multi-tenant SaaS database schema"

# Custom workspace location
python main.py --workspace ~/my-projects/workspace

# Platform bot
python main.py --platform telegram
```

## Workspace layout

```
workspace/
├── tasks/          TASK-XXXXXX.json — task state (status, agent, result)
├── events/         YYYY-MM-DD.jsonl — append-only event log
├── memory/         key.md — persistent notes agents can read and write
├── reports/        TASK-XXXXXX.md — completed task reports
├── agents/         per-agent working directories
│   ├── builder/
│   ├── research/
│   ├── planner/
│   ├── monitor/
│   └── automation/
├── workflows/      workflow definitions
├── vault/          config references, approval queue
├── scripts/        generated automation scripts
└── dashboards/     generated status dashboards
```

## Agents

| Agent | Best for |
|-------|----------|
| **builder** | Code, file editing, running tests, debugging |
| **research** | Web search, documentation, information synthesis |
| **planner** | Goal decomposition, workflow design, strategic planning |
| **monitor** | System status, log analysis, health checks |
| **automation** | Scripts, pipelines, CI/CD, workflow automation |

## REPL commands

| Command | Description |
|---------|-------------|
| `<task description>` | Create and run a task |
| `/status [TASK-ID]` | Show all tasks or one task's details |
| `/agents` | List agents and their descriptions |
| `/log [n]` | Show recent events (default 20) |
| `/report TASK-ID` | Print a task report |
| `/memory [key]` | Read memory entry, or list all keys |
| `/tasks [status]` | Filter tasks by status |
| `/help` | Show help |

## Shell command approval

When an agent wants to run a shell command, you're prompted inline:

```
  ⚠  [builder] wants to run shell command:
     $ pytest tests/ -v
  Allow? [y/N]
```

Say `y` to allow, anything else to reject. The agent gets the rejection as a tool result and can adapt.

## Project structure

```
main.py              Workspace console and CLI entry point
config.py            Config and model constants
core/
  workspace.py       Workspace path layout and initialization
  task.py            Task model, status state machine, TaskStore
  events.py          Append-only event log
agents/
  roles.py           Agent role definitions and system prompts
  supervisor.py      Routes tasks to the right agent
  specialist.py      Executes tasks with the tool runner
tools/
  web.py             web_search, fetch_url
  shell.py           run_shell (with approval gate)
  files.py           read_file, write_file, list_files
  workspace_tools.py write_report, read_memory, write_memory
platforms/
  slack.py / discord.py / telegram.py
```
