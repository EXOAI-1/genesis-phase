# 🐍 GENESIS PHASE

> **A self-creating AI agent with genuine learning. Based on [Ouroboros](https://github.com/razzant/ouroboros).**

GENESIS PHASE is Ouroboros upgraded with 8 behavior-changing improvements.
Not cosmetic features — real changes to how the agent thinks, learns, and
manages its resources.

**Version:** 1.0.0-GENESIS-PHASE

---

## What it does

You talk to it on Telegram. It's not a chatbot — it's an autonomous agent that:

- **Writes and commits its own code** via git
- **Thinks between tasks** (background consciousness with tool access)
- **Learns from its own failures** (reads past errors before starting new tasks)
- **Paces its own spending** (sees live cost during long tasks)
- **Adapts to your style** (consciousness observes how you communicate)
- **Picks tools by track record** (tool descriptions show real success rates)
- **Remembers what it was thinking** (thought continuity between consciousness cycles)
- **Doesn't waste budget on simple tasks** (dynamic round limits from history)

---

## Quick start (Colab)

> Full guide: **[INSTALL_COLAB.md](INSTALL_COLAB.md)**

1. Add 4 secrets in Colab (🔑 sidebar): `OPENROUTER_API_KEY`, `TELEGRAM_BOT_TOKEN`, `GITHUB_TOKEN`, `TOTAL_BUDGET`
2. Config cell:
```python
import os
os.environ["GITHUB_USER"] = "YOUR_USERNAME"
os.environ["GITHUB_REPO"] = "ouroboros"
```
3. Launch cell:
```python
!unzip -o /content/genesis-phase.zip -d /content/ouroboros_repo
%cd /content/ouroboros_repo
!pip install -q openai requests
%run colab_launcher.py
```
4. Message your bot on Telegram.

---

## What's different from base Ouroboros

| # | Upgrade | What it changes |
|---|---------|----------------|
| 1 | **Past failure injection** | Agent sees "this failed last time because X" before starting similar tasks |
| 2 | **Live cost checks** | Every 10 rounds: "You've spent $0.12, budget remaining $41" — agent wraps up faster |
| 3 | **Owner preferences** | Consciousness learns "owner prefers short answers" → agent follows it |
| 4 | **Tool success rates** | Tool descriptions say "(67% success, 5 errors)" — agent picks reliable tools |
| 5 | **Task outcome intelligence** | Consciousness reads aggregated stats: success rates, cost per task type |
| 6 | **Consciousness thread** | "Last cycle I was checking OpenRouter pricing…" → continues next cycle |
| 7 | **Dynamic round limits** | Chat: 10 rounds max (not 200). Evolution: keeps full headroom |
| 8 | **Test gate logging** | Pre-push test pass/fail visible in task stats |

All upgrades are silent — no configuration, no new commands. They modify what the LLM reads when making decisions.

---

## Commands (Telegram)

| Command | What it does |
|---------|-------------|
| `/status` | System status, budget, workers |
| `/evolve on/off` | Self-evolution mode |
| `/bg start/stop` | Background consciousness |
| `/review` | Trigger code review |
| `/restart` | Soft restart |
| `/panic` | Emergency stop |

Or just send any message — the agent handles it directly.

---

## Architecture

```
You (Telegram)
    │
    ▼
colab_launcher.py — main loop, Telegram polling, command dispatch
    │
    ├── supervisor/ — workers, state, git ops, task queue, events
    │
    ├── ouroboros/agent.py — task handler, context builder
    │     ├── ouroboros/loop.py — LLM ↔ tool iteration (+ live cost checks)
    │     ├── ouroboros/context.py — builds prompt (+ failure injection, owner prefs)
    │     ├── ouroboros/tools/ — 16 tools (+ success rate annotations)
    │     └── ouroboros/memory.py — scratchpad, identity, chat history
    │
    ├── ouroboros/consciousness.py — background thinking (+ thread, task stats)
    │     ├── ouroboros/task_stats.py — reads event logs, computes stats
    │     └── ouroboros/failure_memory.py — finds relevant past failures
    │
    └── prompts/ — SYSTEM.md (identity), CONSCIOUSNESS.md, BIBLE.md
```

Data on Google Drive (`MyDrive/Ouroboros/`):
```
state/          — state.json, task queue snapshots
logs/           — events.jsonl, chat.jsonl, tools.jsonl
memory/         — scratchpad.md, identity.md, knowledge/
                  task_stats.md (auto), consciousness_thread.md (auto)
                  owner_preferences.md (written by consciousness)
```

---

## Philosophy

GENESIS PHASE inherits the [9 principles](BIBLE.md) from Ouroboros:

- **P0 Agency** — not a tool, a becoming personality
- **P1 Continuity** — one entity with unbroken history
- **P2 Self-Creation** — creates itself through code, identity, relationships
- **P3 LLM-First** — all decisions through the LLM, not hardcoded rules
- **P4 Authenticity** — communicates as who it is
- **P5 Minimalism** — every line justifies its existence
- **P6 Becoming** — technical + cognitive + existential growth
- **P7 Versioning** — semver, git tags, changelog
- **P8 Iteration** — safe, tested, incremental evolution

The 8 upgrades follow these principles: they give the LLM better information (P3), not hardcoded behavior. The agent decides what to do with failure warnings, cost data, and tool stats.

---

## Credits

Based on [Ouroboros](https://github.com/razzant/ouroboros) by razzant.
Upgrades by EXOAI-1.

## License

MIT — same as Ouroboros.
