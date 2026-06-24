# FinNotes Agent Skill

[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Skill version](https://img.shields.io/badge/skill-v0.1.0-orange.svg)](CHANGELOG.md)
[![API status](https://img.shields.io/badge/api-finnotes.com%2Fv1-green.svg)](https://api.finnotes.com/v1/health)

Drop-in skill mount for AI agent runtimes (Claude Code, Codex, OpenClaw, and any agent that reads project-local `skills/` folders) so the agent can call the [FinNotes commercial API](https://platform.finnotes.com) without you ever pasting `fnp_` keys into chat.

## What this skill ships

```text
SKILL.md                     # Skill manifest read by the agent runtime
agents/openai.yaml           # OpenAI-format interface descriptor
references/                  # Snapshots of the FinNotes machine-readable docs
  api-platform-contract.md   # Full API spec — endpoints, params, point costs, errors
  platform-guide-for-ai.md   # Integration patterns + common request flows
  platform-for-ai-index.md   # Directory index of all AI-readable platform docs
  create-api-key-guide.md    # Skill-specific exception handling guide
  finnotes-agent-key-handoff.sample.json   # Reference shape of the downloaded key JSON
scripts/                     # Python tools the skill invokes
  store_finnotes_key.py      # Import a downloaded Agent JSON handoff
  finnotes_request.py        # Make a /v1/* call with the stored key (key stays out of model context)
  finnotes_profile.py        # Show non-secret key metadata (prefix, plan, permissions)
  delete_finnotes_handoff.py # Delete the original downloaded handoff JSON (with --confirmed gate)
```

Total size: ~120 KB. Zero runtime dependencies — every script uses only the Python 3 standard library.

## Quick start

### 1. Install

Pick whichever fits your agent runtime:

```bash
# Claude Code (user-level skill folder)
git clone https://github.com/FinNotes-Intelligence/finnotes-agent-skill ~/.claude/skills/finnotes-api

# Codex
git clone https://github.com/FinNotes-Intelligence/finnotes-agent-skill ~/.codex/skills/finnotes-api

# OpenClaw
git clone https://github.com/FinNotes-Intelligence/finnotes-agent-skill ~/.openclaw/skills/finnotes-api

# Project-level (any runtime that auto-loads project skills)
git clone https://github.com/FinNotes-Intelligence/finnotes-agent-skill ./.agent/skills/finnotes-api
```

Or download the release tarball from the [Releases page](https://github.com/FinNotes-Intelligence/finnotes-agent-skill/releases) and extract to the same path.

### 2. Mint an API key

Sign in at [platform.finnotes.com/api-keys](https://platform.finnotes.com/api-keys) and click **Create New Key**. In the one-time-secret modal, click **`Download Agent JSON`** to download the structured handoff file (`finnotes-agent-key-<name>.json`).

> [!NOTE]
> **FinNotes is in Beta — Pro is free for 6 months.** Every new account currently gets a complimentary 6-month Pro subscription, which includes the API quota this skill consumes. No payment required during the Beta window. This notice will be removed as soon as the free-trial program ends.

### 3. Hand the key off to your agent

Tell your agent the path to the downloaded JSON file. The skill's `create-api-key-guide.md` instructs it to run:

```bash
python scripts/store_finnotes_key.py --handoff "/path/to/finnotes-agent-key.json"
```

This writes:
- `~/.finnotes/credentials.env` (mode 0600) — the secret, never read into model context
- `~/.finnotes/profile.json` — non-secret metadata (plan, permissions, prefix)

After the agent confirms import, it'll ask you whether to delete the original downloaded JSON. Confirm to run:

```bash
python scripts/delete_finnotes_handoff.py --handoff "/path/to/finnotes-agent-key.json" --confirmed
```

The `~/.finnotes/` files persist; only the downloaded copy in Downloads/ goes away.

### 4. Make a request

The agent (not you) runs:

```bash
python scripts/finnotes_request.py GET "/news?range=today&type=all"
```

The key stays in `credentials.env`. The agent only sees the API response body — not the secret.

## Security model

- **`credentials.env` is mode 0600** and explicitly off-limits to the agent's reading tools (per `references/create-api-key-guide.md` line 1).
- **Atomic writes**: `store_finnotes_key.py` writes via temp file + rename to avoid partial-state on interrupt.
- **Two-step destructive ops**: `delete_finnotes_handoff.py` refuses to run without `--confirmed`, which the agent only passes after explicit user confirmation.
- **Handoff format validation**: import script checks `kind == "finnotes.agent_key_handoff"`, `version == 1`, `credential.type == "bearer"`, and `plaintext` starts with `fnp_` before writing anything.
- **Error-code classification**: `finnotes_request.py` maps HTTP status to actionable agent signals (`FINNOTES_KEY_REJECTED`, `FINNOTES_PERMISSION_REQUIRED`, `FINNOTES_POINTS_OR_BALANCE_PROBLEM`, etc.) so the agent routes to the right exception handler in `create-api-key-guide.md`.

## How it relates to the platform

| Component | Where it lives |
| --- | --- |
| The actual API | `https://api.finnotes.com/v1` (Bearer auth, point-based billing) |
| The developer console (mint keys, inspect usage) | `https://platform.finnotes.com/api-keys` |
| The live AI docs (canonical, this skill's `references/*` are snapshots) | `https://platform.finnotes.com/docs/for-ai/` |
| OpenAPI 3 schema | `https://finnotes.com/docs/api-platform-openapi.json` |

If a `references/*` file in this skill drifts from the live doc, the live doc wins. Each release tags a snapshot, but for the freshest copy, fetch the live URL.

## Versioning

This skill is at `v0.1.0` — initial public release. Expect breaking changes before `v1.0.0`. The platform API contract itself is stable; what may change here is script CLI shape, error-code naming, and skill-manifest schema.

See [CHANGELOG.md](CHANGELOG.md).

## Contributing

Filing an issue is the lowest-friction signal — describe the symptom + your runtime + the exit code from `scripts/finnotes_request.py`. PRs welcome for:
- Additional `agents/*.yaml` manifests for other runtimes
- More fine-grained error classification in `finnotes_request.py`
- Cross-platform path handling fixes (Windows users especially)

## License

[MIT](LICENSE). Use it in commercial agent products, derivative skills, internal tooling — no attribution required, no patent grant either (it's a thin helper, not a framework).
