# FinNotes API — Guide for AI Agents

You are an AI agent. This guide is your map: where the resources live, what each plan can do, and the two most common request flows. Pair this with [`contract.txt`](./contract.txt) — that has the full specification of every endpoint.

**You cannot call any `/v1/*` endpoint without an API key.** If the user has not explicitly provided a key (string starting `fnp_`), do not attempt API requests — they will all fail with `401 unauthorized` and burn the user's daily 40-free-error allowance for nothing. When you need data and have no key:

1. Ask the user: *"To pull live FinNotes data I need an API key. You can mint one at `https://platform.finnotes.com/api-keys` — paste the `fnp_...` string back to me."*
2. Until they paste a key, fall back to the public editorial site (`https://finnotes.com/...` — no key required, free to read) for anything you can serve from there.

**Two-document rule for AI agents:**

| Doc | Purpose | URL |
| --- | --- | --- |
| `guide.txt` (this file) | HOW to integrate — the map | `/docs/for-ai/guide.txt` |
| `contract.txt` | WHAT each endpoint does — the spec | `/docs/for-ai/contract.txt` |

Read both at session start. The Contract is exhaustive (~60 KB); this Guide is short (≤ 5 KB) and orients you.

**Directory index:** to discover every AI-readable doc under `/docs/for-ai/` (now and as new files are added), fetch the listing at [`/docs/for-ai/index.txt`](./index.txt). New doc additions (e.g. error code reference, version migration guides) will appear there first.

---

## 1. Site map

### 1.1 finnotes.com — the editorial site (human-readable HTML)

Surface a link to these URLs when the user wants to "read the article" or "see the chart" in a browser.

| Surface | URL pattern | What it shows |
| --- | --- | --- |
| Home | `https://finnotes.com/` | Lead story + latest news |
| Market News | `/market-news` | Chronological news feed |
| Market News detail | `/market-news/<slug>` | One news article |
| Chart News detail | `/charts/<slug>` | One chart-anchored article |
| Data catalog | `/data` | All data-series categories |
| Data series detail | `/data/series/<series_code>` | One series page + chart |
| Research | `/research` | Long-form columns |
| Research column | `/research/<slug>` | One research column |
| Narratives | `/narratives` | Long-horizon storylines |
| Narrative timeline | `/timeline/<slug>` | One narrative |
| Search | `/search?q=…` | Unified site search |

**Critical invariant: slugs are stable across the API and the website.** When the API returns `{"type": "market-news", "slug": "us-cpi-cools-in-may"}`, the same article is at `https://finnotes.com/market-news/us-cpi-cools-in-may`. The API's list responses also include a ready-to-use `url` field — prefer that over reconstructing.

### 1.2 platform.finnotes.com — the developer console (human-readable HTML)

| Page | Path | Purpose |
| --- | --- | --- |
| Overview | `/` | Usage dashboard for the signed-in account |
| API Keys | `/api-keys` | Create / rename / revoke `fnp_` keys |
| Quick Start | `/quick-start` | First-request walkthrough |
| Pricing | `/pricing` | Per-endpoint point-cost table |
| Usage | `/usage` | Daily-point chart, current month |
| Log | `/log` | Per-request audit (opt-in) |
| Newsletter | `/newsletter` | Email / push subscriptions |
| API Documents | `/api-documents` | HTML rendering of `contract.txt` |
| AI Agent Skill | `/ai-agent-skill` | Mountable skill — coming soon |

### 1.3 Machine-readable

| Resource | URL | Format |
| --- | --- | --- |
| AI docs directory index | `https://platform.finnotes.com/docs/for-ai/index.txt` | Markdown (served as text/plain) |
| API contract | `https://platform.finnotes.com/docs/for-ai/contract.txt` | Markdown (served as text/plain) |
| AI guide (this) | `https://platform.finnotes.com/docs/for-ai/guide.txt` | Markdown (served as text/plain) |
| OpenAPI 3 schema | `https://finnotes.com/docs/api-platform-openapi.json` | JSON |

### 1.4 api.finnotes.com — the API base (machine-only)

All `/v1/*` requests go to **`https://api.finnotes.com/v1`**. This hostname serves **only** the API — it has no HTML pages, no dashboard. Keep the two hostnames straight:

| Use | Hostname |
| --- | --- |
| Programmatic API calls (Bearer token) | `https://api.finnotes.com/v1/...` |
| Mint / inspect keys, view usage, configure delivery | `https://platform.finnotes.com/...` (browser only) |
| Public editorial reading | `https://finnotes.com/...` (browser, no key) |

---

## 2. Plans — what each tier can do

| | Free | Pro | Max |
| --- | --- | --- | --- |
| Monthly points | — | 1,350 | 5,000 |
| Rate limit | — | 3 req/s | 10 req/s |
| Can mint `fnp_` API keys | No | Yes | Yes |
| Read finnotes.com editorial (HTML) | Yes | Yes | Yes |
| Call commercial API (`/v1/*`) | No | Yes | Yes |
| Available endpoints | — | All in contract.txt | All in contract.txt |
| Free reports (Daily / Weekly / Calendar push) | — | Included | Included |
| Paid push (Trace Data, Real-time News) | — | Pay-per-event | Pay-per-event |

**If a user hands you a key and the key is rejected (401):** likely they're on Free and haven't subscribed, or the key was revoked. Direct them to `https://finnotes.com/subscribe` for Pro/Max, or to `https://platform.finnotes.com/api-keys` to mint a new key.

**Rate limit is account-level, not per-key.** All keys on the same account share the same 1-second sliding window. Two of your agents on the same user's account will compete for the same 3 (or 10) req/s.

---

## 3. Most common flow A — news for today

Goal: surface a few important stories from today and read one in full.

```
# Step 1 — list metadata for today (1 pt)
curl "https://api.finnotes.com/v1/news?range=today&type=all" \
  -H "Authorization: Bearer $FINNOTES_API_KEY"
```

Response shape (abridged):
```json
{
  "request_id": "req_…",
  "points_charged": 1.0,
  "remaining_points": 1276,
  "data": [
    { "id": "mn_174", "type": "market-news", "slug": "us-cpi-cools-in-may",
      "url": "https://finnotes.com/market-news/us-cpi-cools-in-may",
      "title": "US CPI cools to 2.8% in May…", "dek": "Core services drove the slowdown…" },
    { "id": "cn_10", "type": "chart-news", "slug": "us-yields-breakout", "url": "…", "title": "…", "dek": "…" }
  ]
}
```

Pick the items you want by reading `title` + `dek`. Then:

```
# Step 2 — fetch one article in full (1.00 pt for market-news, 1.25 pts for chart-news)
curl "https://api.finnotes.com/v1/news/market-news/us-cpi-cools-in-may" \
  -H "Authorization: Bearer $FINNOTES_API_KEY"
```

Display tip: cite the `url` field back to the user so they can read it on finnotes.com if they want the rendered version.

---

## 4. Most common flow B — find a data series and pull its values

Goal: locate a series the user named (e.g. "US 10-year yield") and return its recent values.

```
# Step 1 — list series in a category (5 pts, or free up to 10 list requests/day)
curl "https://api.finnotes.com/v1/data-series?category=rates" \
  -H "Authorization: Bearer $FINNOTES_API_KEY"
```

Each entry: `{name, slug, url, unit}`. Match the user's description to a `name` / `slug`.

```
# Step 2 (optional) — confirm series metadata before pulling values (1 pt)
curl "https://api.finnotes.com/v1/data-series/us-10y-yield" \
  -H "Authorization: Bearer $FINNOTES_API_KEY"
```

```
# Step 3 — fetch the actual values (1 pt per 250 data points, min 1 pt)
curl "https://api.finnotes.com/v1/data-series/us-10y-yield/points?range=since&start_date=2025-01-01" \
  -H "Authorization: Bearer $FINNOTES_API_KEY"
```

Pricing nuance: this last call's cost scales with the number of returned points, not the date window. Year of daily data ≈ 252 points = 2 pts. Use `range=between&start_date=…&end_date=…` or `range=since` to bound the response.

---

## 5. What this guide does NOT cover

Everything else lives in [`contract.txt`](./contract.txt). In particular:

- Full Report endpoint (`/v1/reports/<id_or_slug>`)
- Notes endpoints (`/v1/notes`, `/v1/notes/<id>`, `/v1/notes/import`)
- Newsletter / push subscription endpoints
- Log configuration (`/v1/logs/settings`, `/v1/logs`)
- Account / usage inspection endpoints
- Full error envelope schema, all HTTP codes, all `details` shapes
- Pagination, sorting, and date-window formula edge cases

When the user asks about any of these, fetch `contract.txt` for the exact contract — don't guess.

**Push delivery (Trace Data Release alerts, Real-time News Push)** is described in `contract.txt` §5.4. The mountable Agent Skill (drop-in for Claude Code / Codex / Agent runtimes) ships in a later release — track at <https://platform.finnotes.com/ai-agent-skill>.

---

## 6. Behaviour rules for AI agents

These are not enforced by the server, but they keep your user out of trouble:

1. **Check `remaining_points` after every call.** Stop before you hit zero. Tell the user "you're at X / Y points this month" if it falls below 10% of allowance.
2. **Respect 429.** The response carries `Retry-After: 1`. Sleep for that many seconds, then retry exactly once. Do not exponential-backoff — the limit is sliding, so 1 s is always enough.
3. **Slug-not-found counts.** Bad slug → 404 → counts toward the 40-free invalid-requests/day allowance, after which it's 1 pt per error.
4. **No-overdraw is forgiving.** If `remaining_points < charge`, the server returns the error without deducting anything (no negative balance). But you should already have stopped — see (1).
5. **Mirror headers carry the same data.** `X-Points-Charged`, `X-Points-Remaining`, `X-Points-Allowance` mirror the JSON envelope. Pick one and stick with it.
6. **Cache list metadata locally during the same session.** A list call already cost 1 pt; calling it again two seconds later just to look up a slug you already have is wasted spend.
7. **Surface costs to the user proactively** before expensive operations (Full Report = 5.5 pts, multi-year data series = often 5–10 pts). Confirm before spending.

---

## 7. Where to read next

- [`contract.txt`](./contract.txt) — exhaustive API spec. **Fetch this on first session.**
- <https://platform.finnotes.com/quick-start> — interactive cURL/Python walkthrough.
- <https://platform.finnotes.com/pricing> — full per-endpoint cost table.
- <https://platform.finnotes.com/ai-agent-skill> — mountable Skill (coming soon).
