Update `feedback.md` and `PROJECT_STATUS.md` with compressed intelligence from the current session, then commit and push. Do not summarize the conversation — extract durable, actionable engineering context.

## Step 1 — Read current files

Read these files before updating them:
- `feedback.md`
- `PROJECT_STATUS.md`
- `git log --oneline -10` (to understand what changed)
- `git status` (to see any uncommitted work)

## Step 2 — Update `feedback.md`

Merge new session intelligence into the existing file. Do not rewrite from scratch — preserve stable context, add/update only what changed.

Extract and update:
- New user corrections or redirections
- New architectural decisions made
- New lessons learned (bugs fixed, patterns discovered)
- New things to avoid repeating
- New environment details discovered
- Any changes to communication or workflow preferences
- Any new UI/UX conventions established

Remove or condense:
- Anything that was resolved or is no longer relevant
- Redundant entries now covered by newer knowledge

Keep:
- All stable, long-term architectural decisions
- All "mistakes to avoid" entries
- All environment details
- Safety rules (non-negotiable)

## Step 3 — Update `PROJECT_STATUS.md`

Update the following sections to reflect current state:

- **Completed Work**: mark newly finished items with [x], add new ones
- **Known Issues**: add new issues discovered, remove fixed ones
- **Current Priorities**: reflect what was worked on and what's next
- **Deferred Features**: add anything explicitly punted
- **Git**: update latest commit hash and message
- **Next Recommended Commands**: update if workflows changed

Do not change the stack section unless the stack actually changed.

## Step 4 — Commit and push

```bash
git add feedback.md PROJECT_STATUS.md
git commit -m "session handoff update"
git push -u origin claude/openclaw-alternative-DJEL2
```

## Step 5 — Print bootstrap prompt

After committing, print exactly this block so the user can paste it to start the next session:

---

**Next session bootstrap:**

```
Read PROJECT_STATUS.md and feedback.md first.
Use them as authoritative context — do not scan the entire repo unless necessary.
Branch: claude/openclaw-alternative-DJEL2
Continue from Current Priorities in PROJECT_STATUS.md.
```
