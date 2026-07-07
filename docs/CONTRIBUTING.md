# JAWCOM — Contributing Guide for AI Models

## Mandatory Workflow

Every sprint implementation MUST follow this exact sequence. Never skip steps.

### Step 1: Read Documentation

Before making any changes, read every file in `/docs`:

```
/docs/AI_CONTEXT.md         → Quick project summary (1-2 pages)
/docs/architecture.md       → Complete system architecture
/docs/engineering_rules.md  → Permanent project laws (MUST NOT violate)
/docs/roadmap.md            → Sprint roadmap (completed/planned)
/docs/sprint_status.md      → Current sprint, blockers, tech debt
/docs/api_contract.md       → All API endpoints
/docs/coding_rules.md       → Python/React coding standards
/docs/module_dependencies.md → Dependency graph & rules
/docs/decisions.md          → Architecture Decision Records
/docs/CHANGELOG.md          → Sprint history
/docs/KNOWN_ISSUES.md       → Technical debt & limitations
/docs/TESTING.md            → QA processes
```

### Step 2: Understand Before Implementing

- Study the architecture diagram in `architecture.md`
- Check `engineering_rules.md` for what is prohibited
- Check `module_dependencies.md` for allowed imports
- Check `decisions.md` for why specific patterns were chosen
- Check `KNOWN_ISSUES.md` for existing debt to avoid

### Step 3: Implement Only the Requested Sprint

- Do NOT implement features from future sprints
- Do NOT redesign existing UI
- Do NOT change database schema
- Do NOT change Journey architecture
- Do NOT change Execution Engine architecture
- Do NOT introduce external API integrations unless requested

### Step 4: Check Engineering Rules

After implementation, verify:
- [ ] Engine does not contain node business logic
- [ ] Executors contain only single-node logic
- [ ] Validation does not execute nodes
- [ ] No direct provider instantiation (use factory)
- [ ] No database schema changes
- [ ] No UI redesigns
- [ ] All config stored in `node.config` inside Flow JSON
- [ ] Variable resolution uses `renderer.render()`, not `resolver.resolve()`
- [ ] Routes do not contain business logic
- [ ] Services are the only layer calling repositories

### Step 5: Build & Verify

```bash
# Backend syntax check
cd backend
python -m py_compile app/path/to/changed/files.py

# Frontend build
cd frontend
npm run build
```

### Step 6: Update Documentation

After implementation, update ALL affected documentation:

1. **`CHANGELOG.md`** — Add sprint entry with date, files changed, architecture changes, breaking changes
2. **`roadmap.md`** — Mark sprint as completed
3. **`sprint_status.md`** — Update current sprint, record blockers
4. **`architecture.md`** — Update diagrams and data flows if new modules added
5. **`KNOWN_ISSUES.md`** — Add any new technical debt introduced
6. **`api_contract.md`** — Add any new endpoints
7. **`decisions.md`** — Add ADR if a new architectural decision was made
8. **`engineering_rules.md`** — Add new rules if warranted
9. **`module_dependencies.md`** — Update dependency graph if new modules added
10. **`AI_CONTEXT.md`** — Update summary if architecture changed

### Step 7: Return Implementation Summary

After completion, return a structured summary containing:

```
## Sprint X — <Title>

### Files Changed
| File | Change |
|---|---|

### Architecture Changes
- ...

### Breaking Changes
- ... (or None)

### QA Steps
1. ...
```

## Rules for AI Models

1. **Model change protocol**: When switching AI models (Qwen → Claude → Gemini → DeepSeek), the new model MUST read `/docs/AI_CONTEXT.md` and `/docs/architecture.md` before implementing anything.

2. **Never assume**: If you're unsure about an architectural decision, check `/docs/decisions.md`. If still unsure, check the code. If truly unknown, ask the user.

3. **Never override**: Do not override existing patterns. If the project uses a factory pattern, don't introduce a singleton. If it uses async/await, don't use sync calls.

4. **Minimal changes**: Modify the minimum number of files. Prefer editing existing files over creating new ones.

5. **No dead code**: Remove or flag dead code. Don't leave commented-out code.

6. **Documentation is permanent**: Every doc file in `/docs` is the single source of truth. Keep them accurate.

## What Each File Means for You

| File | How to use it |
|---|---|
| `AI_CONTEXT.md` | Quick context injection when switching models |
| `architecture.md` | Understand the system before coding |
| `engineering_rules.md` | Check violations before submitting |
| `roadmap.md` | Know what's done and what's planned |
| `sprint_status.md` | Know the current state |
| `api_contract.md` | Reference for API endpoints |
| `coding_rules.md` | Follow style and patterns |
| `module_dependencies.md` | Know what you can import |
| `decisions.md` | Understand WHY patterns were chosen |
| `CHANGELOG.md` | Update after every sprint |
| `KNOWN_ISSUES.md` | Avoid introducing known problems |
| `TESTING.md` | QA reference |
| `CONTRIBUTING.md` | This file — the workflow you're reading now |
