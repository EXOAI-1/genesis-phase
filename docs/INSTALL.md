# PHASE — Installation Guide

> Complete step-by-step guide. Estimated time: 15 minutes.
> No Python experience needed beyond copy-paste.

---

## What You Need

| Item | Where to get it | Cost |
|------|----------------|------|
| Google account (for Colab) | accounts.google.com | Free |
| Telegram account | telegram.org | Free |
| OpenRouter API key | openrouter.ai/keys | Pay-per-use (~$0.001/call) |
| GitHub account | github.com/signup | Free |
| GitHub Personal Access Token | github.com/settings/tokens | Free |

---

## Step 1: Get an OpenRouter API Key

OpenRouter gives you access to every AI model (Claude, Gemini, GPT, Llama) through a single API key.

1. Go to **https://openrouter.ai** and create an account
2. Click **Keys** in the left sidebar (or go to openrouter.ai/keys)
3. Click **Create Key**
4. Name it `PHASE` and click **Create**
5. Copy the key — it starts with `sk-or-v1-...`
6. Add credit: go to **Credits** → add at least $5 to start (this is your AI budget)

**Save this key.** You'll paste it into Colab in Step 4.

---

## Step 2: Create a Telegram Bot

1. Open Telegram and search for **@BotFather**
2. Send `/newbot`
3. Choose a display name: `PHASE Bot` (or anything you like)
4. Choose a username: must end in `bot`, e.g. `my_phase_bot`
5. BotFather replies with your **bot token** — it looks like `7123456789:AAH...`

**Save this token.** You'll paste it into Colab in Step 4.

---

## Step 3: Get a GitHub Personal Access Token

PHASE uses GitHub for self-evolution — PLASMA commits improvements to its own code.

1. Go to **https://github.com/settings/tokens**
2. Click **Generate new token (classic)**
3. Name: `PHASE`
4. Expiration: 90 days (or No expiration)
5. Select scopes: check **repo** (full control of private repositories)
6. Click **Generate token**
7. Copy the token — it starts with `ghp_...`

**Save this token.** You'll paste it into Colab in Step 4.

---

## Step 4: Set Up Google Colab

1. Go to **https://colab.research.google.com**
2. Create a **New Notebook**
3. Click the **🔑 key icon** in the left sidebar (Secrets)
4. Add these 4 secrets:

| Secret Name | Value | Example |
|------------|-------|---------|
| `OPENROUTER_API_KEY` | Your OpenRouter key | `sk-or-v1-abc123...` |
| `TELEGRAM_BOT_TOKEN` | Your bot token from BotFather | `7123456789:AAH...` |
| `GITHUB_TOKEN` | Your GitHub PAT | `ghp_abc123...` |
| `TOTAL_BUDGET` | Max spend in USD | `50` |

5. **Enable notebook access** for each secret (toggle the switch)

---

## Step 5: Run PHASE

Paste this into a Colab cell and press **Shift+Enter**:

```python
from google.colab import userdata
import os

# Load secrets
os.environ["OPENROUTER_API_KEY"] = userdata.get("OPENROUTER_API_KEY")
os.environ["TELEGRAM_BOT_TOKEN"] = userdata.get("TELEGRAM_BOT_TOKEN")
os.environ["GITHUB_TOKEN"]       = userdata.get("GITHUB_TOKEN")
os.environ["TOTAL_BUDGET"]       = userdata.get("TOTAL_BUDGET")

# Clone and run
token = userdata.get("GITHUB_TOKEN")
!git clone https://{token}@github.com/EXOAI-1/phase /content/phase 2>/dev/null || echo "Already cloned"
%cd /content/phase
!git pull origin main
!pip install -q aiohttp pyyaml python-telegram-bot
%run bootstrap.py
```

You should see:

```
========================================================
  ⚡ PHASE — bootstrapping
========================================================
✅ All secrets loaded
✅ Config loaded — PLASMA strategic: anthropic/claude-opus-4-6
✅ Budget initialised: $50
✅ 3 core FLUX nodes ready
✅ Telegram bot connected

========================================================
  ⚡ PHASE is online
  PLASMA v1.0.0
  3 FLUX nodes active
  3 SOLID validators active
  Budget: $50
========================================================

Open Telegram and send any message to your bot.
The first message registers you as the creator.
```

---

## Step 6: Talk to PHASE

1. Open **Telegram**
2. Search for your bot by its username
3. Send any message — this registers you as the creator
4. Now send a goal:

```
Build me a Python script that scrapes Hacker News top stories
and saves them to a JSON file
```

PHASE will:
- Decompose your goal into tasks
- Assign each task to the right FLUX node
- Have each result validated by SOLID (3 models vote)
- Synthesise a final answer and send it back

---

## Commands Reference

Once PHASE is running, you can use these commands in Telegram:

| Command | What it does |
|---------|-------------|
| `/phase status` | Shows budget, active nodes, task counts, SOLID approval rate |
| `/phase nodes` | Lists all FLUX nodes with their model, status, and spend |
| `/phase tasks` | Shows active and recently completed tasks |
| `/phase history 20` | Shows last 20 events (goal received, task done, votes, etc.) |
| `/phase senate` | Shows last 10 SOLID votes with approve/reject |
| `/phase evolve` | Triggers PLASMA to propose a self-improvement |
| `/phase config` | Shows current model configuration |
| `/phase plugin list` | Shows loaded plugins |
| `/phase plugin load translator` | Loads a plugin at runtime |

---

## Troubleshooting

**"OPENROUTER_API_KEY not set"**
→ You forgot to add the secret in Colab. Click the 🔑 key icon and add it. Make sure the toggle is ON.

**"Module not found: aiohttp"**
→ Run `!pip install aiohttp pyyaml python-telegram-bot` in a cell above.

**Bot doesn't respond in Telegram**
→ Make sure the Colab cell is still running (the cell should show a spinning icon). If Colab disconnects, re-run the cell.

**"Repository not found" on git clone**
→ Your GITHUB_TOKEN might not have the `repo` scope. Generate a new one at github.com/settings/tokens with `repo` checked.

**"Budget exhausted"**
→ PHASE tracks spend. Add more credit on OpenRouter and increase TOTAL_BUDGET.

**SOLID keeps rejecting results**
→ This is working as intended — SOLID is strict. Check `/phase senate` to see why. The feedback is injected into the retry automatically.

---

## Updating PHASE

When a new version is released, just change one line in your Colab cell:

```python
!git pull origin main  # gets the latest code
```

Or to reset completely:

```python
!rm -rf /content/phase
!git clone https://{token}@github.com/EXOAI-1/phase /content/phase
```

---

## Cost Estimates

| Model | Role | Cost per 1K tokens |
|-------|------|-------------------|
| Claude Opus 4.6 | PLASMA strategic, Architect | $15 in / $75 out |
| Claude Sonnet 4.6 | PLASMA coordination, Coder | $3 in / $15 out |
| Claude Haiku 4.5 | SOLID validator 2 | $0.80 in / $4 out |
| Gemini Flash 1.5 | Researcher, Reviewer, SOLID v1 | $0.075 in / $0.30 out |
| Llama 3.1 8B | SOLID validator 3 | $0.06 in / $0.06 out |

A typical goal costs $0.01–$0.10 depending on complexity. Your $50 budget will handle hundreds of goals.

---

## Next Steps

- Read **[ARCHITECTURE.md](ARCHITECTURE.md)** to understand how PHASE works internally
- Read **[DEVELOPER.md](DEVELOPER.md)** to modify or extend the system
- Try building a plugin — see the plugin template in `plugin_base.py`

---

*PHASE v1.1.0 · PLASMA · FLUX · SOLID*
