# FinNotes API Key Management And Exception Guide

Read this file only when the normal local-credential path fails, the user provides a downloaded Agent JSON handoff, public key metadata or permission checks are needed, the user asks to delete the downloaded handoff JSON, or the user cannot complete the requested FinNotes API operation.

Do not read, print, summarize, or copy `~/.finnotes/credentials.env` or any downloaded handoff JSON. If metadata is needed, use `python scripts/finnotes_profile.py`.

## Local Files And Commands

The import command creates:

```text
~/.finnotes/credentials.env
~/.finnotes/profile.json
```

`credentials.env` contains the secret and must not be read into model context.

`profile.json` contains non-secret metadata such as key prefix, creation time, plan, and permissions. Prefer `python scripts/finnotes_profile.py` so the agent sees a stable, secret-free summary.

Use these commands:

```bash
# Import a downloaded platform JSON. Do not open the JSON manually.
python scripts/store_finnotes_key.py --handoff "/path/to/finnotes-agent-key.json"

# Show public key metadata only.
python scripts/finnotes_profile.py

# Check one permission before attempting an operation.
python scripts/finnotes_profile.py --require usage

# Make an API request without exposing the key.
python scripts/finnotes_request.py GET "/news?range=today&type=all"

# Check whether the current local key works.
python scripts/finnotes_request.py --check

# Delete the downloaded handoff JSON only after explicit user confirmation.
python scripts/delete_finnotes_handoff.py --handoff "/path/to/finnotes-agent-key.json" --confirmed
```

After importing a handoff JSON, tell the user that the secret was stored in `credentials.env` and public metadata was stored in `profile.json`. Then ask whether to delete the original downloaded JSON from the public/download folder. Run the delete command only after the user confirms.

Deleting the original downloaded handoff JSON does not delete `credentials.env` or `profile.json`; the API key and public key metadata remain available locally.

## First Classify The Failure

Use the helper diagnostic, HTTP status, API error payload, and `python scripts/finnotes_profile.py` metadata to classify the issue before telling the user what to do.

| Failure | Likely signal | User guidance |
| --- | --- | --- |
| No local key | `FINNOTES_CREDENTIALS_MISSING`, missing `~/.finnotes/credentials.env` | Ask the user to create/download an Agent JSON key handoff. |
| Invalid/revoked key | `FINNOTES_KEY_REJECTED`, HTTP `401` | Ask the user to create/download a replacement Agent JSON key handoff. |
| Missing permission | `FINNOTES_PERMISSION_REQUIRED`, HTTP `403`, or `finnotes_profile.py --require <permission>` fails | Tell the user the current key lacks the required permission and ask for a key created with that permission. |
| Zero/insufficient points | `FINNOTES_POINTS_OR_BALANCE_PROBLEM`, `insufficient_points`, `remaining_points=0` | Explain point balance. If the user is on Pro and needs more usage, suggest upgrading to Max. |
| Key-check endpoint problem | `FINNOTES_KEY_CHECK_ENDPOINT_NOT_FOUND` from `--check` | Ask the user to re-download/import a handoff JSON or verify the configured API base. |
| Normal content `404` | Article slug, report id, or data-series slug not found | Do not send the user to create a key. Resolve with list/search endpoints or explain the item was not found. |

## New User Or No Local Key

Tell the user:

To use live FinNotes API data, create an API key at:

https://platform.finnotes.com/api-keys

In the API Keys page:

1. Sign in to your FinNotes account.
2. Create a new key. The key name can be any user-facing label, such as `Production server`.
3. Keep `Basic(all news, report & data)` enabled.
4. Leave unrelated permissions off unless you need notes, usage endpoints, logs, newsletter, or notification management.
5. If you want the agent to call dedicated account usage endpoints, enable `View usage & remaining points`; otherwise the agent can still read point headers on billable responses.
6. In the one-time key modal, click `Download Agent JSON`.
7. Give the downloaded JSON file path to the agent. Do not paste the `fnp_...` key into chat.

The downloaded JSON should match `references/finnotes-agent-key-handoff.sample.json`.

When the user provides the downloaded handoff JSON path, run the import command:

```bash
python scripts/store_finnotes_key.py --handoff "/path/to/finnotes-agent-key.json"
```

After import succeeds, follow the delete-confirmation rule in "Local Files And Commands".

## Invalid Or Revoked Key

Tell the user:

The local FinNotes key was rejected by the API. It may have been revoked, copied incorrectly, or issued for an account that no longer has API access.

Create a replacement key at:

https://platform.finnotes.com/api-keys

Then download the Agent JSON and provide the file path. The agent will import it with:

```bash
python scripts/store_finnotes_key.py --handoff "/path/to/finnotes-agent-key.json"
```

After import succeeds, ask whether to delete the original downloaded JSON. If the user confirms, run:

```bash
python scripts/delete_finnotes_handoff.py --handoff "/path/to/finnotes-agent-key.json" --confirmed
```

## Missing Permission

Tell the user:

The current FinNotes key is valid, but it does not have the permission required for this operation.

Use `python scripts/finnotes_profile.py` or the API error to name the missing permission if available. For a quick check, run:

```bash
python scripts/finnotes_profile.py --require usage
```

Replace `usage` with the required permission. Common mappings:

| Needed operation | Required permission |
| --- | --- |
| News, reports, data-series | `basic` |
| Notes download/import/sync | `notes` |
| Account points and usage endpoints | `usage` |
| Request-log reading | `view_log` |
| Request-log settings or deletion | `manage_log` |
| Newsletter or push preferences | `manage_newsletter` |
| Account-wide all-key usage state | `all_usage_state` |
| API notification preferences | `notification_management` |

Ask the user to create/download a new Agent JSON key with the required permission enabled, then provide the file path for import. Do not ask them to paste the plaintext key.

## Zero Or Insufficient Points

Tell the user:

The current key works, but the account does not have enough remaining FinNotes points for this request.

Then choose the guidance by plan when known:

- `pro`: If the user needs more API usage this month, upgrade to Max at `https://finnotes.com/subscribe` or reduce the request size/cost.
- `max`: Reduce the request size/cost, wait for the next reset, or contact FinNotes if the usage need is larger than the Max allowance.
- unknown plan: Ask the user to check `https://platform.finnotes.com/usage` and `https://finnotes.com/subscribe`.

Cost-reduction options to suggest before upgrading:

- use `range=today` instead of multi-day news windows
- fetch list metadata first and detail only selected items
- narrow data-series date ranges
- avoid full reports unless the user confirms the 5.5 point cost

Do not tell the user to create another key for a point-balance problem; points are account-level.
