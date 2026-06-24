# FinNotes — AI-readable docs index

All machine-readable docs for AI agents integrating with the FinNotes commercial API live in this directory. Served as `text/plain` with `.txt` extension.

## Canonical AI docs (this directory)

| File | Coverage | URL |
| --- | --- | --- |
| `contract.txt` | Full API spec — endpoints, params, point cost, errors | https://platform.finnotes.com/docs/for-ai/contract.txt |
| `guide.txt` | Integration patterns, retry policy, push lifecycle, cost optimisation | https://platform.finnotes.com/docs/for-ai/guide.txt |
| `index.txt` (this file) | Directory listing for `/docs/for-ai/` | https://platform.finnotes.com/docs/for-ai/index.txt |

## Sibling resources (not in this directory)

| Resource | Use | URL |
| --- | --- | --- |
| OpenAPI 3 schema (JSON) | SDK / tooling generation | https://finnotes.com/docs/api-platform-openapi.json |
| Site-wide AI index | Top-level AI resource catalog | https://finnotes.com/llms.txt |
| RFC 9727 api-catalog | API discovery linkset | https://finnotes.com/.well-known/api-catalog |
| Agent Skills index | Cloudflare Agent Skills discovery | https://finnotes.com/.well-known/agent-skills/index.json |

## For human reading (not in `/docs/for-ai/`)

| Resource | URL |
| --- | --- |
| HTML rendering of contract | https://platform.finnotes.com/api-documents |
| Markdown (.md) source for download | https://platform.finnotes.com/docs/for-users/contract.md |

## Quick facts

- Base URL: `https://api.finnotes.com/v1`
- Auth: `Authorization: Bearer fnp_<...>` (mint at `https://platform.finnotes.com/api-keys`)
- Plans: Pro 1,350 pts/mo @ 3 req/s · Max 5,000 pts/mo @ 10 req/s

## Conventions

- All `.txt` files in this directory: `Content-Type: text/plain`, body is markdown source verbatim.
- The `.txt` + `text/plain` combination is the only format confirmed to be reliably consumed by AI client UIs (web + mobile across major vendors). `text/markdown` and HTML wrappers were tested and rejected.
- Files are bundled into the build artifact via Vite `?raw` import — doc updates require a redeploy.
- New AI docs added under `/docs/for-ai/` must also be listed in this `index.txt`.
