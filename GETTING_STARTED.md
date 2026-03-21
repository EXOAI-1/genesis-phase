# GENESIS PHASE — Getting Started (Complete Beginner Guide)

> **You need:** A Google account, a Telegram account, $5. That's it.
>
> **Time:** 10 minutes from zero to talking with your AI.
>
> **No coding experience required.** Every step is copy-paste.

---

## What you're building

GENESIS PHASE is an AI agent that:
- Lives in Google Colab (free cloud computer)
- Talks to you via Telegram (like a chat app)
- Thinks on its own between conversations
- Learns from its own mistakes
- Can write code, search the web, and modify itself

It's based on [Ouroboros](https://github.com/razzant/ouroboros) by razzant,
with 8 upgrades that make it learn from experience.

---

## Step 1: Get your API keys (5 minutes)

You need 4 keys. Here's exactly how to get each one.

### 1a. OpenRouter API Key

This lets your AI use models like Claude, Gemini, and GPT.

1. Go to **https://openrouter.ai**
2. Click **Sign Up** (use Google account — fastest)
3. Once logged in, click **Keys** in the left sidebar
4. Click **Create Key**
5. Name it anything (e.g., "genesis")
6. Copy the key — it starts with `sk-or-v1-...`
7. Go to **https://openrouter.ai/credits** and add **$5** minimum

> ⚠️ Without credit, the AI can't think. $5 lasts a long time.

### 1b. Telegram Bot Token

This creates the chat bot you'll talk to.

1. Open **Telegram** on your phone or desktop
2. Search for **@BotFather** (it has a blue checkmark)
3. Send it: `/start`
4. Send it: `/newbot`
5. It asks for a name — type anything (e.g., "Genesis Phase")
6. It asks for a username — type something unique ending in `bot` (e.g., `my_genesis_phase_bot`)
7. BotFather replies with a token like `7123456789:AAF...` — **copy this entire token**

### 1c. GitHub Token

This lets the AI save its own code changes.

1. Go to **https://github.com/settings/tokens**
2. Click **Generate new token (classic)**
3. Name: "genesis-phase"
4. Expiration: 90 days (or "No expiration")
5. Check the **repo** box (full control of private repositories)
6. Click **Generate token**
7. Copy the token — it starts with `ghp_...`

> ⚠️ GitHub only shows the token ONCE. Copy it now.

### 1d. Fork the repo (optional but recommended)

1. Go to **https://github.com/razzant/ouroboros**
2. Click **Fork** (top right)
3. Keep all defaults, click **Create Fork**
4. Note your username and the repo name (e.g., `EXOAI-1/ouroboros`)

---

## Step 2: Set up Google Colab (3 minutes)

### 2a. Open Colab

1. Go to **https://colab.research.google.com**
2. Click **New Notebook**

### 2b. Add your secrets

1. Look at the **left sidebar** — click the **🔑 key icon** ("Secrets")
2. Click **Add a new secret** for each of these:

| Name (type exactly) | Value (paste your key) |
|-----|-------|
| `OPENROUTER_API_KEY` | Your `sk-or-v1-...` key |
| `TELEGRAM_BOT_TOKEN` | Your `7123456789:AAF...` token |
| `GITHUB_TOKEN` | Your `ghp_...` token |
| `TOTAL_BUDGET` | `50` |

3. **Toggle each secret ON** (the switch next to each one must be blue)

> ⚠️ If the toggles aren't ON, the AI can't read the secrets. This is the #1 setup mistake.

---

## Step 3: Add the code cells (2 minutes)

### Cell 1: Configuration

Click **+ Code** to add a new cell. Paste this and **edit the two lines** with your info:

```python
import os

# ════════════════════════════════════════
# EDIT THESE TWO LINES
# ════════════════════════════════════════
os.environ["GITHUB_USER"] = "EXOAI-1"      # ← Your GitHub username
os.environ["GITHUB_REPO"] = "ouroboros"     # ← Your fork name (or "ouroboros")
```

**Run this cell** (click the ▶ play button or press Shift+Enter).

### Cell 2: Launch

Click **+ Code** again. Paste this:

```python
# Upload genesis-phase.zip to Colab first (drag into Files sidebar)
# OR if you pushed to GitHub, use the bootstrap shim instead:
# %run colab_bootstrap_shim.py

!unzip -o /content/genesis-phase.zip -d /content/ouroboros_repo 2>/dev/null
%cd /content/ouroboros_repo
!pip install -q openai requests
%run colab_launcher.py
```

**Before running this cell:**
- Drag your `genesis-phase.zip` file into the **Files panel** on the left sidebar of Colab
- Wait for it to upload (you'll see it appear as `/content/genesis-phase.zip`)

**Run this cell.** You'll see output scrolling — wait for:

```
🧠 Background consciousness auto-started (default: always on)
```

**That means it's running.** Don't close this tab.

---

## Step 4: Talk to your AI (30 seconds)

1. Open **Telegram**
2. Search for your bot's username (the one you created with BotFather)
3. Send any message — try: `Hello, who are you?`
4. Wait 5-10 seconds — GENESIS PHASE responds

**First message:** You'll see "✅ Owner registered. GENESIS PHASE online."
This registers you as the owner. Only you can talk to this bot.

---

## Step 5: Try these commands

| Message | What happens |
|---------|-------------|
| `Hello, who are you?` | The AI introduces itself |
| `Write a Python function that checks if a number is prime` | It writes code |
| `What's happening in AI news today?` | It searches the web |
| `/status` | Shows budget, workers, system state |
| `/bg start` | Starts background thinking |
| `/bg stop` | Stops background thinking |
| `/evolve on` | Enables self-evolution (it modifies its own code!) |
| `/panic` | Emergency stop — kills everything |

---

## What happens next (automatically)

Once you've chatted for a while, these things happen silently:

- **After ~10 tasks:** The AI starts learning from patterns — "I fail 80% of shell tasks due to timeouts"
- **On long tasks:** The AI sees its own spending: "Round 10/200, spent $0.12" — and wraps up faster on simple questions
- **Between conversations:** Background consciousness thinks every 5 minutes — reads news, checks GitHub, notices patterns
- **Over days:** Consciousness observes your preferences ("owner likes short answers") and writes them to a file the agent reads

Check `MyDrive/Ouroboros/memory/` after a few hours to see:
- `task_stats.md` — performance summary
- `consciousness_thread.md` — what it was thinking last
- `owner_preferences.md` — how it thinks you like to communicate

---

## Troubleshooting

### "Missing required secret: OPENROUTER_API_KEY"
→ Go to the 🔑 sidebar in Colab. Make sure all 4 secrets are added AND toggled ON.

### "GITHUB_USER not set"
→ Make sure you ran Cell 1 (the config cell) before Cell 2.

### Bot doesn't respond on Telegram
→ Check Colab — is the cell still running? Look for errors in red.
→ Check your OpenRouter balance — if it's $0, the AI can't think.
→ Make sure you messaged the RIGHT bot (the one YOU created, not someone else's).

### "Ouroboros" still appears in some places
→ The Python package is named `ouroboros/` for compatibility with the original codebase. All user-facing text says "GENESIS PHASE." This is intentional.

### Colab disconnected
→ Re-run both cells. Your data is on Google Drive — nothing is lost.
→ Colab disconnects after ~90 minutes of inactivity. This is a Google limitation.
→ For longer sessions: Colab Pro ($10/month) or keep the tab active.

### High costs
→ Send `/status` to see budget remaining.
→ Dynamic round limits kick in after ~10 tasks — simple chats auto-cap.
→ Background consciousness uses the cheapest model (Gemini Flash).

---

## Pushing upgrades to your fork (optional)

To make GENESIS PHASE permanent in your GitHub fork:

1. In Colab, open a new cell and run:
```python
%cd /content/ouroboros_repo
!git add -A
!git commit -m "GENESIS PHASE v1.0.0: 8 upgrades + bug fixes"
!git push origin main
```

Or use the `push_genesis_phase.py` script included in the zip.

---

## Architecture (for the curious)

```
You (Telegram)
    │
    ▼
Google Colab
    ├── colab_launcher.py        ← Main loop: polls Telegram, dispatches tasks
    │
    ├── ouroboros/agent.py        ← Receives task, builds context, runs LLM
    │   ├── ouroboros/loop.py     ← LLM ↔ tool iteration (+cost checks, +dynamic caps)
    │   ├── ouroboros/context.py  ← Builds prompt (+failure warnings, +owner prefs)
    │   ├── ouroboros/tools/      ← 16 tools (shell, git, browser, search, etc.)
    │   └── ouroboros/memory.py   ← Scratchpad, identity, chat history
    │
    ├── ouroboros/consciousness.py ← Background thinking every 5 min
    │   ├── task_stats.py          ← Reads logs, computes performance stats
    │   └── failure_memory.py      ← Finds relevant past failures
    │
    ├── prompts/SYSTEM.md          ← "I Am GENESIS PHASE" — agent's identity
    ├── prompts/CONSCIOUSNESS.md   ← Instructions for background thinking
    └── BIBLE.md                   ← Constitution (9 principles of agency)

Google Drive (MyDrive/Ouroboros/)
    ├── state/      ← Budget, task queue, session state
    ├── logs/       ← events.jsonl, chat.jsonl, tools.jsonl
    └── memory/     ← scratchpad.md, identity.md, knowledge/
                      task_stats.md, consciousness_thread.md,
                      owner_preferences.md
```

---

## Credits

**GENESIS PHASE** is built on [Ouroboros](https://github.com/razzant/ouroboros) by [razzant](https://github.com/razzant).

Ouroboros provides the core architecture: the agent, the LLM tool loop, the supervisor, the Telegram integration, the consciousness engine, the constitutional framework (BIBLE.md), and the self-evolution pipeline.

GENESIS PHASE adds 8 behavior-changing upgrades and bug fixes on top of this foundation. See [UPGRADES.md](UPGRADES.md) for the complete technical details.

**License:** MIT (same as Ouroboros).
