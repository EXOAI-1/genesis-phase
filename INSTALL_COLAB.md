# GENESIS PHASE — Colab Installation

> 5 minutes. 4 secrets. 2 cells. Done.

---

## Step 1: Add secrets (one time)

Click the **🔑 key icon** in Colab's left sidebar. Add these 4 secrets and toggle each ON:

| Secret | Where to get it |
|--------|----------------|
| `OPENROUTER_API_KEY` | openrouter.ai/keys (add $5+ credit) |
| `TELEGRAM_BOT_TOKEN` | Telegram → @BotFather → /newbot |
| `GITHUB_TOKEN` | github.com/settings/tokens (scope: repo) |
| `TOTAL_BUDGET` | Type `50` (or whatever max USD you want) |

---

## Step 2: Config cell (run once per notebook)

```python
import os

# ═══════════════════════════════════════════════════
# YOUR CONFIG — edit these
# ═══════════════════════════════════════════════════
os.environ["GITHUB_USER"] = "EXOAI-1"      # ← your GitHub username
os.environ["GITHUB_REPO"] = "ouroboros"     # ← your fork name

# Optional: customize models (defaults are good)
# os.environ["OUROBOROS_MODEL"]       = "anthropic/claude-sonnet-4-6"
# os.environ["OUROBOROS_MODEL_CODE"]  = "anthropic/claude-sonnet-4-6"
# os.environ["OUROBOROS_MODEL_LIGHT"] = "google/gemini-3-pro-preview"
# os.environ["OUROBOROS_MAX_WORKERS"] = "5"
```

---

## Step 3: Launch cell (run every time)

### Option A: From your GitHub fork (recommended for self-evolution)

```python
%run colab_bootstrap_shim.py
```

This clones your fork, checks out the ouroboros branch, and runs the launcher.

### Option B: From uploaded ZIP (for testing upgrades)

Upload `genesis-phase.zip` to Colab (drag into Files sidebar), then:

```python
!unzip -o /content/genesis-phase.zip -d /content/ouroboros_repo 2>/dev/null
%cd /content/ouroboros_repo
!pip install -q openai requests
%run colab_launcher.py
```

---

## Step 4: Open Telegram

Find your bot. Send any message. Ouroboros registers you as owner and responds.

---

## Commands

| Command | What it does |
|---------|-------------|
| `/status` | System status, budget, workers |
| `/evolve on` | Enable self-evolution mode |
| `/evolve off` | Disable self-evolution |
| `/bg start` | Start background consciousness |
| `/bg stop` | Stop consciousness |
| `/review` | Trigger code review |
| `/restart` | Soft restart |
| `/panic` | Emergency stop everything |

Or just send any message — Ouroboros handles it directly.

---

## What the upgrades do (silently, no config needed)

Once you start chatting, the 8 upgrades activate automatically:

1. **Task stats** — after ~10 tasks, consciousness reads your success/failure patterns
2. **Failure injection** — if a task type failed recently, the agent sees a warning and adjusts
3. **Cost checks** — on long tasks, the agent sees its spending and wraps up if simple
4. **Dynamic rounds** — simple chats cap at 10 rounds instead of 200
5. **Thought thread** — consciousness remembers what it was thinking between cycles
6. **Owner preferences** — consciousness learns how you like to communicate
7. **Tool stats** — tool descriptions show real success rates
8. **Test gate** — evolution commits blocked if tests fail

Check `memory/` directory on Drive after a few hours to see the new files:
- `task_stats.md` — performance summary
- `consciousness_thread.md` — last thought
- `owner_preferences.md` — observed preferences (written by consciousness)

---

## Pushing upgrades to your fork

To make the upgrades permanent in your fork (so they survive Colab restarts):

1. Upload the ZIP to Colab
2. Extract over your repo:
```python
!unzip -o /content/genesis-phase.zip -d /content/ouroboros_repo
%cd /content/ouroboros_repo
!git add -A
!git commit -m "Upgrades: task intelligence, failure memory, cost checks, dynamic rounds, owner prefs, tool stats"
!git push origin ouroboros
```

Done. Next time you run the bootstrap shim, the upgrades are included.

---

## Troubleshooting

| Problem | Solution |
|---------|---------|
| "Missing required secret" | Check 🔑 sidebar — all 4 secrets must be toggled ON |
| "GITHUB_USER not set" | Add `os.environ["GITHUB_USER"] = "..."` in config cell |
| Colab disconnects | Re-run both cells. State is on Drive, nothing is lost |
| Agent not responding | Check budget — `/status` shows remaining. Add more credit to OpenRouter |
| High cost on simple messages | Dynamic rounds need ~10 tasks of history to kick in. Give it time |
