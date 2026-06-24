# Changelog

All notable changes to this skill are recorded here. Versioning follows [SemVer](https://semver.org/).

## [0.2.1] — 2026-06-24

Naming alignment patch on top of v0.2.0. Pure rename — no behavior, script, or schema changes.

### Changed
- **Repository renamed**: `FinNotes-Intelligence/finnotes-agent-skill` → `FinNotes-Intelligence/finnotes-news-and-data-skill`. GitHub serves a permanent 301 redirect on the old URL, so existing clones and bookmarks continue to work, but new installs should use the new URL.
- **SKILL.md `name:`** dropped the `-pack` suffix:
  `finnotes-global-market-news-and-data-researcher-pack` → `finnotes-global-market-news-and-data-researcher`.
  Runtimes that cached the old `$<name>` from v0.2.0 need a one-time refresh.
- **`agents/openai.yaml`** `display_name` now uses an ampersand (`&`) to match the README and matches the SKILL.md name (no `-pack`): `FinNotes Global Market News & Data Researcher`. `default_prompt` updated to reference the new name.
- **`README.md` title** simplified: `Skill: FinNotes Global Market News & Data Researcher Pack` → `Skill: FinNotes Global Market News & Data Researcher` (drops the redundant "Pack" — "Skill:" already signals the artifact type).

### Rationale
"Pack" was redundant in two places (the README title's "Skill:" prefix already telegraphs the artifact type, and the SKILL name's "researcher-pack" double-tagged the noun). The previous repo name (`finnotes-agent-skill`) over-claimed: it took the whole "FinNotes agent skill" namespace for one specific product. The new repo name follows a `finnotes-<scope>-skill` pattern that leaves room for future scoped skills (e.g. `finnotes-portfolio-skill`) without renaming back.

### Notes
- All install commands in `README.md` now point at the new repo URL. The old URL still works via GitHub's redirect — no immediate user action required.
- Scripts and references are unchanged from v0.2.0.

## [0.2.0] — 2026-06-24

Protocol revamp + news helper. SKILL.md is rewritten around an explicit Control-Plane / Execution-Branch / Routing-Matrix / Output-Protocol structure (designed for stricter agent-runtime parsing) and a dedicated `finnotes_news.py` script replaces ad-hoc `finnotes_request.py GET "/news?…"` invocations for the common news workflows.

### Added
- `scripts/finnotes_news.py` — single helper that wraps all the news intents:
  - `1` / `<N>` — today's or last-N-days summary list
  - `full` — every today's article in full body (uses the new `/v1/news/today/full` bundle endpoint)
  - `date YYYY-MM-DD` — single-date summary
  - `detail <id>` / `detail <type> <slug>` — single-article detail
  - `--type all,market-news,chart-news,column-article` and `--limit N` query refinements
- `finnotes_request.py` and `finnotes_news.py` both set a `User-Agent: FinNotes-Agent-Skill/0.1` header (replacing the default `Python-urllib`), so platform analytics can see real skill traffic.
- Cloudflare `403` handling: when the WAF blocks a request before it reaches FinNotes, both scripts emit `FINNOTES_CLOUDFLARE_ACCESS_DENIED` / `CLOUDFLARE_ACCESS_DENIED` instead of the generic `PERMISSION_REQUIRED` (so the agent doesn't tell users to fix permissions when the problem is the firewall).

### Changed
- **SKILL.md is completely rewritten** with a routing protocol the agent runtime follows literally:
  - Section 1 — control plane (when to execute, when to read references, phase-1 vs phase-2 conversation pacing, negative-restraint rule against re-fetching after `full`).
  - Section 2 — command-syntax table mapping user intent to exact `finnotes_news.py` invocation.
  - Section 3 — exception-routing matrix.
  - Section 4 — output protocol (immediate delivery, identifiers exposed in Phase 1, full implications in Phase 2).
- **Skill name changed**: `Global_Market_News_and_Data_Researcher_pack_(FinNotes)` → `finnotes-global-market-news-and-data-researcher-pack` (kebab-case, lowercase — required for OpenAI Skills indexing). Agent runtimes that resolved the old name MUST update their `$<name>` references.
- **Description adds an EXCLUSION clause**: skill is now explicitly marked off-limits for entertainment / pop-culture / sports / celebrity topics. Routing systems should not invoke FinNotes for those intents.
- `agents/openai.yaml` `display_name`, `short_description`, and `default_prompt` updated to match the new manifest.
- `references/create-api-key-guide.md` now leads with the **Free access notice** (6-month Pro free, cutoff 2027-01-01) and a **Grandfathering clause** (existing unexpired subscriptions keep their full term after the program closes).
- `references/api-platform-contract.md` and `references/platform-guide-for-ai.md` re-synced from the live docs at https://platform.finnotes.com/docs/for-ai/ — they now include the `/v1/news/today/full` bundled endpoint added in the v0.1.1 cycle.

### Notes
- Backwards-incompatible at the SKILL-name level. Agents that auto-detected the skill from the previous capitalized/underscored name will need a one-time re-registration. If your runtime caches `default_prompt`, refresh it.
- Scripts still use Python 3 stdlib only — no third-party dependencies, ~125 KB total.

## [0.1.1] — 2026-06-24

Snapshot refresh for the `GET /v1/news/today/full` bundled endpoint added to the platform.

### Changed
- `references/api-platform-contract.md` — synced to platform contract dated 2026-06-24, includes new §10.4 "Today Full Bundle" + §5.2 pricing row.
- `references/platform-guide-for-ai.md` — synced; new §3.1 one-shot variant for "read every article from today in full".
- `references/platform-for-ai-index.md` — synced.

### Notes
- No script or manifest changes. Scripts still use the same `/v1/*` Bearer auth interface; the new endpoint is reachable via `finnotes_request.py GET "/news/today/full"`.
- This is a snapshot-only sync release. Live docs at `https://platform.finnotes.com/docs/for-ai/` always win when in doubt.

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
