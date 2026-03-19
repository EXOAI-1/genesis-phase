# PHASE Developer Guide

> Complete reference for modifying, extending, and debugging PHASE.

---

## Quick Start for Developers

```bash
# Clone
git clone https://github.com/EXOAI-1/phase
cd phase

# Install dependencies
pip install aiohttp pyyaml python-telegram-bot requests

# Run tests (no API keys needed)
PYTHONPATH=. python3 tests/run_tests.py

# Run integration simulation
PYTHONPATH=. python3 integration_test.py

# Syntax check
python3 -c "
import ast; from pathlib import Path
for f in Path('.').rglob('*.py'):
    if '__pycache__' not in str(f):
        ast.parse(f.read_text()); print(f'OK: {f}')
"
```

---

## File Map

| File | Lines | Purpose |
|------|-------|---------|
| `config.py` | 184 | Typed Config dataclass, YAML loader, singleton `cfg` |
| `llm.py` | 201 | Async LLM client, retry, fallback, cost tracking |
| `state.py` | 298 | StateManager: budget, nodes, events, persistence |
| `task.py` | 193 | Task dataclass, TaskStatus, TaskQueue |
| `solid_engine.py` | 290 | 3-validator consensus engine |
| `flux_base.py` | 194 | FluxNode ABC: poll loop, SOLID integration, retry |
| `flux_coder.py` | 64 | Coder node (Claude Sonnet) |
| `flux_researcher.py` | 58 | Researcher node (Gemini Flash) |
| `flux_reviewer.py` | 70 | Reviewer node (Gemini Flash) |
| `flux_architect.py` | 69 | Architect node (Claude Opus) |
| `plasma.py` | 628 | PLASMA: decompose, route, synthesise, evolve |
| `plugin_base.py` | 255 | Plugin system: PhasePlugin, PluginRegistry |
| `telegram_phase.py` | 251 | Telegram command handlers |
| `bootstrap.py` | 308 | Colab launcher |
| `tests/test_phase.py` | 1043 | 87 unit tests |
| `integration_test.py` | 290 | Full lifecycle simulation |

---

## How to Add a New FLUX Node

### Option A: As a Plugin (no core changes)

1. Create `plugins/your_node/__init__.py`
2. Subclass `FluxNode`, implement `execute()`
3. Export a `PLUGIN = PhasePlugin(...)` descriptor
4. Add model to `model_config.yaml` under `flux:`
5. Load via `/phase plugin load your_node` or add to `bootstrap.py` PLUGINS list

See the full template in `plugin_base.py` or `ARCHITECTURE.md`.

### Option B: As a Core Node (permanent)

1. Create `flux_your_node.py` in the root directory
2. Subclass `FluxNode`, set `node_type` and `system_prompt`
3. Add model to `model_config.yaml` under `flux:`
4. Import and instantiate in `bootstrap.py`
5. Add tests in `tests/test_phase.py`

---

## How to Change Models

Edit `model_config.yaml` — the only file that contains model strings:

```yaml
# To use a different coder model:
flux:
  coder: "openai/gpt-4.1"

# To change a SOLID validator:
solid:
  validator_3: "deepseek/deepseek-r1"

# To use a cheaper PLASMA coordinator:
plasma:
  coordination: "google/gemini-flash-1.5"
```

No code changes needed. Restart PHASE to pick up changes.

To verify no model strings leaked into Python:
```bash
grep -rn 'anthropic/\|google/\|openai/\|meta-llama/' *.py \
  | grep -v config.py | grep -v llm.py | grep -v plugin_base.py
# Should return nothing (config defaults and price map are expected)
```

---

## How to Add a Telegram Command

1. Write a handler function in `telegram_phase.py`:

```python
async def _cmd_mycommand(args, send, plasma):
    result = "Your data here"
    await send(result)
```

2. Add it to the dispatch table in `handle_phase_command()`:

```python
dispatch = {
    "status":    _cmd_status,
    "mycommand": _cmd_mycommand,  # add here
    ...
}
```

3. Add to the help text in `_cmd_help()`.

---

## How to Write Tests

All tests live in `tests/test_phase.py`. They run offline with mocked LLM calls.

**Pattern for tests that need state:**

```python
class TestMyFeature:
    def _setup(self, tmp_path):
        os.environ["PHASE_DATA_DIR"] = str(tmp_path)
        import state as sm
        from state import StateManager
        sm.state = StateManager()
        run(sm.state.init_budget(50.0))

    def test_something(self, tmp_path):
        self._setup(tmp_path)
        # ... your test
```

**Pattern for tests that need SOLID mocked:**

```python
import solid_engine as sol
from task import ValidationResult
mock_solid = MagicMock()
mock_solid.validate_task_result = AsyncMock(return_value=ValidationResult(
    task_id="x", approved=True, votes=[],
    consensus="unanimous", feedback=""
))
sol.solid = mock_solid
```

**Run tests:**

```bash
PYTHONPATH=. python3 tests/run_tests.py          # standalone runner
PYTHONPATH=. python3 -m pytest tests/ -v          # if pytest installed
PYTHONPATH=. python3 integration_test.py          # full simulation
```

---

## How the LLM Client Works

`llm.py` exposes a single function: `call_llm()`. All modules use it.

**Request flow:**
1. Check `OPENROUTER_API_KEY` env var
2. Try primary model
3. If empty response → try each fallback model in order
4. Each attempt: retry up to 2 times with exponential backoff
5. Track usage via registered callbacks
6. Return text or empty string (never raises)

**Cost estimation:**
Separate input/output pricing per model. Budget is tracked via callbacks fired after every call:

```python
register_usage_callback(fn)  # fn(tag, cost_usd, prompt_tokens, completion_tokens)
```

---

## How State Persistence Works

`state.py` uses atomic writes: write to `.tmp`, then `rename()` to the final path. This prevents corruption if the process is killed mid-write.

```python
async def _save(self):
    tmp = STATE_FILE.with_suffix(".tmp")
    tmp.write_text(json.dumps(asdict(self._s), indent=2, default=str))
    tmp.replace(STATE_FILE)  # atomic on POSIX
```

State is saved after every mutation (budget change, node registration, event log, vote). The rolling event window is capped at 500 entries.

---

## How Self-Evolution Works

1. `Plasma.propose_evolution()` acquires `_evolution_lock` (prevents concurrent evolutions)
2. PLASMA status set to "evolving"
3. LLM call (strategic model) with recent events + performance stats
4. Response parsed for: IMPROVEMENT, FILE, RATIONALE, CURRENT_CODE, PROPOSED_CODE
5. `Solid.validate_evolution()` runs all 3 validators — **unanimous required**
6. If approved: file content is string-replaced, committed to `plasma` branch, pushed
7. Version bumped (e.g., 1.0.0 → 1.0.1)
8. If rejected: feedback logged, notified via Telegram

---

## Environment Variables

| Variable | Required | Default | Purpose |
|----------|----------|---------|---------|
| `OPENROUTER_API_KEY` | Yes | — | OpenRouter API key for all LLM calls |
| `TELEGRAM_BOT_TOKEN` | Yes | — | Telegram bot token |
| `GITHUB_TOKEN` | No | — | GitHub PAT for self-evolution commits |
| `TOTAL_BUDGET` | No | `50` | Maximum spend in USD |
| `PHASE_DATA_DIR` | No | `data` | Directory for state persistence |
| `PHASE_REPO_DIR` | No | `.` | Git repo root for evolution commits |
| `PHASE_CONFIG` | No | `model_config.yaml` | Path to config file |
| `PHASE_FLUX_POLL_SECONDS` | No | `2.0` | FLUX node poll interval |
| `PHASE_LLM_TIMEOUT` | No | `90` | LLM call timeout in seconds |

---

## Debugging

**Enable debug logging:**
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

**Check state file directly:**
```bash
cat data/phase_state.json | python3 -m json.tool
```

**Check what SOLID is doing:**
Use `/phase senate` in Telegram, or:
```python
events = state.recent_events(50)
solid_events = [e for e in events if e["source"] == "SOLID"]
```

**Common issues:**

| Symptom | Cause | Fix |
|---------|-------|-----|
| Empty LLM responses | API key invalid or no credit | Check OpenRouter dashboard |
| SOLID always rejects | Validators finding real issues | Check `/phase senate` for feedback |
| Tasks stuck IN_PROGRESS | FLUX node crashed | Check Colab output for exceptions |
| Evolution always rejected | SOLID is conservative (by design) | Review proposals in event log |
| "Task destroyed but pending" | Normal — asyncio cleanup on shutdown | Harmless warning, ignore |

---

## Rules You Must Never Break

1. **Late imports** — never change `import state as _s` (inside functions) to top-level imports
2. **Never name a file `solid.py`** — conflicts with `solid/` package directory
3. **Never cache `state.state`** in a module-level variable
4. **All models in YAML** — no hardcoded model strings in `.py` files
5. **Evolution requires unanimous** SOLID approval (3/3)
6. **Never touch `main` branch** programmatically — only `plasma` branch

---

*PHASE v1.1.0 · Developer Guide*
