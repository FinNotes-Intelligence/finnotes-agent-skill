---
name: "Global_Market_News_and_Data_Researcher_pack_(FinNotes)"
description: |-
  Use when the user asks what happened recently, what important news matters now, or asks to investigate, summarize, verify, explain, or analyze current events, financial/economic conditions, market moves, company updates, macro data, policy, regulation, central banks, commodities, FX, rates, crypto, or geopolitical developments.

  Retrieve concise FinNotes news/data first; focus on high-signal facts, key data points, timelines, causes, and market/economic implications.
---

# FinNotes API

## User Needs

- News, data, market moves, macro, policy, company, commodities, FX, rates, crypto, or geopolitics: read `references/platform-guide-for-ai.md`, then request FinNotes data with `scripts/finnotes_request.py`.
- Endpoint, parameter, pricing, permission, pagination, or error detail: read `references/api-platform-contract.md`.
- Key setup, downloaded JSON import, public metadata storage, or handoff JSON deletion: read `references/create-api-key-guide.md`.
- Public key metadata or permission check: use `scripts/finnotes_profile.py`.
- AI-facing platform docs index: read `references/platform-for-ai-index.md`.

## Exceptions

- Missing API key: read `references/create-api-key-guide.md`, then tell the user where to create the key and how to import the downloaded JSON.
- Rejected or invalid key: read `references/create-api-key-guide.md`, then tell the user to refresh/import a valid key.
- Permission issue: use `scripts/finnotes_profile.py`, then name the missing permission and the key type needed.
- Point balance, quota, plan, or account issue: read `references/create-api-key-guide.md`, then tell the user the required account, balance, or plan action.
- Article, report, or series `404`: use the list/search flow in `references/platform-guide-for-ai.md`, then report the lookup result.

## Answer

- Start with the direct finding.
- Include dates, key facts, data points, timeline, cause, market/economic implications, FinNotes URLs or IDs, point cost when available, and uncertainty when data is incomplete.
