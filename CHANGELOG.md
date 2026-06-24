# Changelog

All notable changes to this skill are recorded here. Versioning follows [SemVer](https://semver.org/).

## [0.1.0] — 2026-06-24

Initial public release.

### Added
- `SKILL.md` manifest (entry point read by agent runtimes)
- `agents/openai.yaml` OpenAI-format interface descriptor
- `references/` — snapshots of FinNotes machine-readable platform docs:
  - `api-platform-contract.md` (API spec)
  - `platform-guide-for-ai.md` (integration patterns)
  - `platform-for-ai-index.md` (AI docs directory index)
  - `create-api-key-guide.md` (skill-specific exception handling)
  - `finnotes-agent-key-handoff.sample.json` (downloadable key JSON shape)
- `scripts/`:
  - `store_finnotes_key.py` — import downloaded handoff JSON → write `~/.finnotes/credentials.env` (mode 0600) + `~/.finnotes/profile.json`
  - `finnotes_request.py` — wrap `urllib` to call `/v1/*` with the stored Bearer key, classify HTTP errors into `FINNOTES_*` agent signals
  - `finnotes_profile.py` — show non-secret metadata; `--require <permission>` for pre-call gating
  - `delete_finnotes_handoff.py` — delete downloaded JSON after user-confirmed import (`--confirmed` required)

### Notes
- This version targets the FinNotes API at `https://api.finnotes.com/v1` (commercial API base, separate from the `platform.finnotes.com` developer console).
- All scripts use Python 3 stdlib only — no third-party dependencies.
- The skill is expected to mount under `~/.<runtime>/skills/finnotes-api/` for user-level installs, or `./.agent/skills/finnotes-api/` for project-local.

### Known limitations
- No automatic 429 backoff / retry. If your agent hits the per-second rate limit (Pro: 3 req/s, Max: 10 req/s), it's responsible for honoring `Retry-After`.
- No multi-profile support. One key per machine (`~/.finnotes/credentials.env`).
- `references/*` files are point-in-time snapshots; the live URLs at `https://platform.finnotes.com/docs/for-ai/` may be newer.

### Compatibility
- Agent runtimes: Claude Code, Codex, OpenClaw, any runtime that loads `skills/` from user or project folder
- Python: 3.8+
- OS: macOS / Linux (Windows paths in `store_finnotes_key.py` should work but untested)
