---
name: "finnotes-global-market-news-and-data-researcher"
description: |-
  Use when the user asks what happened recently, what important news matters now, or asks to investigate, summarize, verify, explain, or analyze current events, financial/economic conditions, market moves, company updates, macro data, policy, regulation, central banks, commodities, FX, rates, crypto, or geopolitical developments. 
  
  Retrieve concise FinNotes news/data first; focus on high-signal facts, key data points, timelines, causes, and market/economic implications. 
  
  EXCLUSION: STRICTLY PROHIBITED for entertainment, pop culture, sports, or celebrity news. Do NOT trigger this tool for entertainment topics. 
---

# Global News and Data Researcher Skill (FinNotes)

## 1. ROUTING & CONVERSATIONAL CONSTRAINTS (Control Plane)
- **DIRECT EXECUTION:** For basic news requests, execute the scripts in Section 2 immediately. **MUST NOT** read reference markdowns prior to execution unless an explicit error/exception occurs.
- **PROGRESSIVE DISCLOSURE (L1/L2 Interaction):** Treat the user interaction as a multi-step conversational flow.
  - **Phase 1 (Overview & Speed):** When the user asks for a summary or daily scan, execute summary commands. Prioritize fast feedback, high-density facts, and low latency. 
  - **Phase 2 (Deep Dive & Depth):** When the user asks for details on a specific item from the overview, pivot to in-depth analysis. Execute `detail` or `full` commands to provide comprehensive context, source-link checks, and related macro/micro data.
- **NEGATIVE RESTRAINT:** After executing a `full` daily lookup, you **MUST NOT** execute `detail` lookups for the same day (the `full` payload already contains this data).

## 2. COMMAND SYNTAX (Execution Branch)
Strictly use the following scripts for corresponding intents:

| User Intent | Command Syntax |
| :--- | :--- |
| Today's all-news summary | `python scripts/finnotes_news.py 1` |
| Today's full details | `python scripts/finnotes_news.py full` |
| Recent N-days summary | `python scripts/finnotes_news.py <N>` |
| Specific date summary | `python scripts/finnotes_news.py date YYYY-MM-DD` |
| Item detail by ID | `python scripts/finnotes_news.py detail <id>` |
| Item detail by Type & Slug | `python scripts/finnotes_news.py detail <type> <slug>` |

## 3. EXCEPTION & ROUTING MATRIX
If an error occurs or a complex non-news request is made, halt immediate output and follow this routing logic strictly:

| Trigger / Error Condition | Action Required |
| :--- | :--- |
| `NO_KEY` / Missing / Invalid Key | Read `references/create-api-key-guide.md`. Instruct user on key creation/import. |
| Permission / Scope Issue | Run `scripts/finnotes_profile.py`. Report missing permission and required key type. |
| Balance / Quota / Plan Issue | Read `references/create-api-key-guide.md`. Report required account action. |
| Article / Report `404` | Execute search flow in `references/platform-guide-for-ai.md`. Report results. |
| Non-news data, pricing, usage | Read relevant reference files before responding. |
| Endpoint parameter / Contract | Read `references/api-platform-contract.md`. |


## 4. OUTPUT PROTOCOL
- **Immediate Delivery:** Upon receiving script output, reply instantly. Do not add artificial wait times or unnecessary extra API calls.
- **Format:** Start with the direct finding. Maintain high data density.
- **Conversational Hooks (Phase 1):** When delivering an overview, ensure the output naturally exposes identifiers (such as Dates, News IDs, or Slugs) so the user can easily reference them for follow-up detail requests.
- **Required Elements (Phase 2):** For deep dives, always include Key Facts, Data Points, Financial/Market Implications, URLs/IDs, Point Costs (if available), and explicitly state uncertainty if data is partial.
- **Analysis:** Keep analytical commentary minimal during Phase 1 (Overview). Reserve detailed interpretation and implication analysis for Phase 2 (Deep Dive), unless explicitly requested earlier.


# 