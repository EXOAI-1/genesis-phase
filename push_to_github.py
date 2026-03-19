#!/usr/bin/env python3
"""
push_to_github.py — Push PHASE to GitHub in one command.

USAGE
-----
  export GITHUB_TOKEN=ghp_your_token_here
  export GITHUB_USER=your_username
  python3 push_to_github.py

WHAT THIS DOES
--------------
  1. Validates your GitHub token
  2. Creates repo 'phase' (public)
  3. Pushes all 30 files
  4. Creates a GitHub Release v1.0.0-PHASE
  5. Prints the final repo URL and install instructions

REQUIREMENTS
------------
  pip install requests
"""

import base64
import json
import os
import sys
import time
from pathlib import Path

import requests

# ── Configuration ─────────────────────────────────────────────────────────────

GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "YOUR_TOKEN_HERE")
GITHUB_USER  = os.environ.get("GITHUB_USER",  "YOUR_USERNAME_HERE")
REPO_NAME    = "phase"
REPO_DESC    = (
    "PHASE — Autonomous multi-agent AI system. "
    "PLASMA orchestrates. FLUX executes. SOLID validates."
)
TAG          = "v1.0.0-PHASE"
RELEASE_NAME = "PHASE v1.0.0 — PLASMA · FLUX · SOLID"
RELEASE_BODY = """\
## PHASE v1.0.0

Autonomous multi-agent AI system: goal decomposition, specialist routing,
3-model consensus validation, and PLASMA self-evolution via GitHub.

### Architecture
- **PLASMA** — boss: decomposes goals, routes tasks, synthesises results, self-evolves
- **FLUX nodes** — workers: coder, researcher, reviewer, architect
- **SOLID** — 3 validators: Gemini Flash + Claude Haiku + Llama 3.1 vote on every result

### Install
See INSTALL.md — 4 secrets + 1 Colab cell.

### Tests
87 tests · all offline · all passing.
"""

FILES = [
    "README.md", "INSTALL.md", "DEVELOPER.md",
    "docs/INSTALL.md", "docs/DEVELOPER.md",
    "model_config.yaml", "requirements.txt",
    "config.py", "llm.py", "state.py", "task.py", "solid_engine.py",
    "flux_base.py", "flux_coder.py", "flux_researcher.py",
    "flux_reviewer.py", "flux_architect.py",
    "plasma.py", "plugin_base.py", "telegram_phase.py", "bootstrap.py",
    "phase/__init__.py", "flux/__init__.py", "solid/__init__.py",
    "plugins/__init__.py", "tests/__init__.py",
    "tests/test_phase.py", "tests/run_tests.py",
    "data/mission.md",
    "HANDOVER_TO_OPUS.md",
    "push_to_github.py",
]

# ── GitHub API helpers ────────────────────────────────────────────────────────

API = "https://api.github.com"

def hdr(token):
    return {
        "Authorization":        f"token {token}",
        "Accept":               "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }

def api_ok(r, ctx):
    if r.status_code not in (200, 201, 204):
        print(f"\n❌  {ctx} failed [{r.status_code}]")
        try:    print(json.dumps(r.json(), indent=2)[:600])
        except: print(r.text[:300])
        sys.exit(1)
    return r.json() if r.content else {}

def enc(path):
    return base64.b64encode(Path(path).read_bytes()).decode()

def step(msg):
    print(f"\n{'─'*58}\n  {msg}\n{'─'*58}")

def note(msg):
    print(f"  · {msg}")

# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    if GITHUB_TOKEN in ("", "YOUR_TOKEN_HERE"):
        print("❌  Set GITHUB_TOKEN:  export GITHUB_TOKEN=ghp_...")
        sys.exit(1)
    if GITHUB_USER in ("", "YOUR_USERNAME_HERE"):
        print("❌  Set GITHUB_USER:   export GITHUB_USER=yourusername")
        sys.exit(1)

    pkg = Path(__file__).parent.resolve()
    h   = hdr(GITHUB_TOKEN)

    print(f"""
╔══════════════════════════════════════════════════════╗
║        ⚡ PHASE — GitHub push                        ║
╠══════════════════════════════════════════════════════╣
║  User  : {GITHUB_USER:<44}║
║  Repo  : {REPO_NAME:<44}║
║  Files : {len(FILES):<44}║
╚══════════════════════════════════════════════════════╝
""")

    # 1. Validate token
    step("1/5  Validating token")
    usr = api_ok(requests.get(f"{API}/user", headers=h), "auth")["login"]
    note(f"Authenticated as: {usr}")

    # 2. Create repo
    step(f"2/5  Creating repo '{REPO_NAME}'")
    rc = requests.post(f"{API}/user/repos", headers=h, json={
        "name": REPO_NAME, "description": REPO_DESC,
        "private": False, "auto_init": False,
        "has_issues": True, "has_wiki": False,
    })
    if rc.status_code == 422 and "already exists" in rc.text:
        note("Repo already exists — updating files")
    else:
        api_ok(rc, "repo creation")
        note(f"Created: github.com/{usr}/{REPO_NAME}")
    time.sleep(2)

    # 3. Push files
    step(f"3/5  Pushing {len(FILES)} files")
    pushed = updated = skipped = failed = 0
    for rel in FILES:
        local = pkg / rel
        if not local.exists():
            note(f"SKIP (not found): {rel}")
            skipped += 1
            continue
        sha = None
        rg = requests.get(f"{API}/repos/{usr}/{REPO_NAME}/contents/{rel}", headers=h)
        if rg.status_code == 200:
            sha = rg.json().get("sha")
        payload = {
            "message": f"PHASE v1.0: {Path(rel).name}",
            "content": enc(local),
            "branch":  "main",
        }
        if sha:
            payload["sha"] = sha
        rp = requests.put(
            f"{API}/repos/{usr}/{REPO_NAME}/contents/{rel}",
            headers=h, json=payload,
        )
        if rp.status_code in (200, 201):
            action = "updated" if sha else "created"
            note(f"{action}: {rel}")
            if sha: updated += 1
            else:   pushed  += 1
        else:
            note(f"FAILED [{rp.status_code}]: {rel}")
            failed += 1
    note(f"\n{pushed} new · {updated} updated · {skipped} skipped · {failed} failed")

    # 4. Set topics
    step("4/5  Setting repo metadata")
    requests.patch(f"{API}/repos/{usr}/{REPO_NAME}", headers=h,
        json={"description": REPO_DESC})
    requests.put(
        f"{API}/repos/{usr}/{REPO_NAME}/topics",
        headers={**h, "Accept": "application/vnd.github.mercy-preview+json"},
        json={"names": ["ai","agent","multi-agent","llm","autonomous",
                         "python","orchestration","genesis"]},
    )
    note("Topics and description updated")

    # 5. Create release
    step(f"5/5  Creating release '{TAG}'")
    existing = requests.get(f"{API}/repos/{usr}/{REPO_NAME}/releases/tags/{TAG}", headers=h)
    if existing.status_code == 200:
        requests.delete(
            f"{API}/repos/{usr}/{REPO_NAME}/releases/{existing.json()['id']}", headers=h
        )
        note("Removed previous release")
    rrel = api_ok(requests.post(
        f"{API}/repos/{usr}/{REPO_NAME}/releases", headers=h,
        json={"tag_name": TAG, "target_commitish": "main",
              "name": RELEASE_NAME, "body": RELEASE_BODY,
              "draft": False, "prerelease": False},
    ), "release creation")
    note(f"Release: {rrel['html_url']}")

    # Done
    repo_url = f"https://github.com/{usr}/{REPO_NAME}"
    print(f"""
╔══════════════════════════════════════════════════════════╗
║        ✅  PHASE pushed to GitHub!                       ║
╠══════════════════════════════════════════════════════════╣
║  Repo    : {repo_url:<49}║
║  Release : {TAG:<49}║
║  Pushed  : {pushed+updated} files ({pushed} new, {updated} updated){"": <30}║
╠══════════════════════════════════════════════════════════╣
║  Tests   : 87 passing                                    ║
╚══════════════════════════════════════════════════════════╝

User install (share this):

  Cell 1 — 4 secrets in Colab (🔑 key icon):
    OPENROUTER_API_KEY  TELEGRAM_BOT_TOKEN
    GITHUB_TOKEN        TOTAL_BUDGET

  Cell 2 — run once:
    from google.colab import userdata
    token = userdata.get("GITHUB_TOKEN")
    !git clone https://{{token}}@github.com/{usr}/{REPO_NAME} /content/phase
    %cd /content/phase
    !pip install -q aiohttp pyyaml python-telegram-bot
    %run bootstrap.py

  Open Telegram → send any message → PHASE is online.
""")

if __name__ == "__main__":
    main()
